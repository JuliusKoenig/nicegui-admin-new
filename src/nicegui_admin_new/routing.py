import asyncio
import inspect
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException, Request, Response
from nicegui import APIRouter, background_tasks, binding, core, helpers
from nicegui.page import page
from nicegui.client import Client, ClientConnectionTimeout
from nicegui.error import error_content
from nicegui.language import Language
from nicegui.logging import log

from nicegui_admin_new.layout import NiceguiAdminLayout


class NiceguiAdminPage(page):
    def __init__(self,
                 path: str, *,
                 layout_name: str | None = None,
                 title: str | None = None,
                 viewport: str | None = None,
                 favicon: str | Path | None = None,
                 dark: bool | None = ...,
                 language: Language = ...,
                 response_timeout: float = 3.0,
                 reconnect_timeout: float | None = None,
                 markdown: bool | None = None,
                 api_router: APIRouter | None = None,
                 **kwargs: Any,
                 ) -> None:
        super().__init__(path=path,
                         title=title,
                         viewport=viewport,
                         favicon=favicon,
                         dark=dark,
                         language=language,
                         response_timeout=response_timeout,
                         reconnect_timeout=reconnect_timeout,
                         markdown=markdown,
                         api_router=api_router,
                         **kwargs)
        self.layout_name = layout_name

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        core.app.remove_route(self.path)  # NOTE make sure only the latest route definition is used

        if "include_in_schema" not in self.kwargs:
            self.kwargs["include_in_schema"] = core.app.config.endpoint_documentation in {"page", "all"}

        self.api_router.get(self._path, **self.kwargs)(self._wrap(func))
        Client.page_routes[func] = self.path
        return func

    def _get_layout(self,
                    request: Request) -> NiceguiAdminLayout:
        return request.app.admin.layouts[self.layout_name]

    def _wrap(self, func: Callable[..., Any]) -> Callable[..., Any]:
        parameters_of_decorated_func = list(inspect.signature(func).parameters.keys())

        def check_for_late_return_value(task: asyncio.Task) -> None:
            try:
                if task.result() is not None:
                    log.error(f"ignoring {task.result()}; "
                              "it was returned after the HTML had been delivered to the client")
            except asyncio.CancelledError:
                pass
            except ClientConnectionTimeout as e:
                log.debug("client connection timed out")
                e.client.delete()
            except Exception as e:
                core.app.handle_exception(e)

        def create_500_error_page(e: Exception, request: Request) -> Response:
            page_exception_handler = core.app._page_exception_handler
            if page_exception_handler is None:
                raise e
            with Client(NiceguiAdminPage(""), request=request) as error_client:
                # page exception handler
                if helpers.expects_arguments(page_exception_handler):
                    page_exception_handler(e)
                else:
                    page_exception_handler()

                # FastAPI exception handlers
                for key, handler in core.app.exception_handlers.items():
                    if key == 500 or (isinstance(key, type) and isinstance(e, key)):
                        result = handler(request, e)
                        if helpers.should_await(result):
                            background_tasks.create(result, name=f"exception handler {handler.__name__}")

                # NiceGUI exception handlers
                core.app.handle_exception(e)

                return error_client.build_response(request, 500)

        @wraps(func)
        async def decorated(*dec_args, **dec_kwargs) -> Response:
            request = dec_kwargs["request"]
            # NOTE cleaning up the keyword args so the signature is consistent with "func" again
            dec_kwargs = {k: v for k, v in dec_kwargs.items() if k in parameters_of_decorated_func}
            with Client(self, request=request) as client:
                if any(p.name == "client" for p in inspect.signature(func).parameters.values()):
                    dec_kwargs["client"] = client
                try:
                    # get layout
                    layout = self._get_layout(request=request)

                    # render layout
                    layout_result = layout(*dec_args, **dec_kwargs)

                    result = func(*dec_args, **dec_kwargs)
                except Exception as e:
                    return create_500_error_page(e, request)

            if helpers.should_await(result):
                async def wait_for_result() -> Response | None:
                    with client:
                        try:
                            return await result
                        except Exception as e:
                            client.handle_exception(e)
                            return create_500_error_page(e, request)

                task = background_tasks.create(wait_for_result(),
                                               name=f"wait for result of page '{client.page.path}'",
                                               handle_exceptions=False)
                task_wait_for_connection = background_tasks.create(
                    client._waiting_for_connection.wait(),  # pylint: disable=protected-access
                    name=f"wait for connection {client.page.path}",
                )
                done, _ = await asyncio.wait([
                    task,
                    task_wait_for_connection,
                ], timeout=self.response_timeout, return_when=asyncio.FIRST_COMPLETED)
                if not done:
                    task.cancel()
                    log.warning(f"Response for {client.page.path} not ready after {self.response_timeout} seconds")
                    client.delete()
                if not task_wait_for_connection.done():
                    task_wait_for_connection.cancel()
                if task.done():
                    result = task.result()
                else:
                    result = None
                    task.add_done_callback(check_for_late_return_value)

            if not await client.sub_pages_router._can_resolve_full_path(client):  # pylint: disable=protected-access
                # Handle 404 gracefully without re-raising exception (similar to 404 handler when no root function)
                log.warning(f"{request.url} not found")
                with client:
                    error_content(404, HTTPException(404, f"{client.sub_pages_router.current_path} not found"))
                return client.build_response(request, 404)

            if isinstance(result, Response):  # NOTE if setup returns a response, we don"t need to render the page
                return result
            binding._refresh_step()  # pylint: disable=protected-access
            return client.build_response(request, client.status_code)

        parameters = [p for p in inspect.signature(func).parameters.values() if p.name != "client"]
        # NOTE adding request as a parameter so we can pass it to the client in the decorated function
        if "request" not in {p.name for p in parameters}:
            request = inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)
            parameters.insert(0, request)
        decorated.__signature__ = inspect.Signature(parameters)  # type: ignore

        return decorated


class NiceguiAdminAPIRouter(APIRouter):
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    def page(self,
             path: str, *,
             title: str | None = None,
             viewport: str | None = None,
             favicon: str | Path | None = None,
             dark: bool | None = ...,  # type: ignore
             response_timeout: float = 3.0,
             **kwargs,
             ) -> Callable:
        """Page

        Creates a new page at the given route.
        Each user will see a new instance of the page.
        This means it is private to the user and not shared with others.

        :param path: route of the new page (path must start with "/")
        :param title: optional page title
        :param viewport: optional viewport meta tag content
        :param favicon: optional relative filepath or absolute URL to a favicon (default: `None`, NiceGUI icon will be used)
        :param dark: whether to use Quasar's dark mode (defaults to `dark` argument of `run` command)
        :param response_timeout: maximum time for the decorated function to build the page (default: 3.0)
        :param kwargs: additional keyword arguments passed to FastAPI's @app.get method
        """

        return NiceguiAdminPage(
            path=path,
            title=title,
            viewport=viewport,
            favicon=favicon,
            dark=dark,
            response_timeout=response_timeout,
            api_router=self,
            **kwargs
        )

    def layout(self,
               path: str, *,
               layout_name: str = "default",
               title: str | None = None,
               viewport: str | None = None,
               favicon: str | Path | None = None,
               dark: bool | None = ...,  # type: ignore
               response_timeout: float = 3.0,
               **kwargs) -> Callable:
        """Layout

        Creates a new page with the given layout at the given route.
        Each user will see a new instance of the page.
        This means it is private to the user and not shared with others.

        :param path: route of the new page (path must start with "/")
        :param layout_name: name of the layout to use (default: "default")
        :param title: optional page title
        :param viewport: optional viewport meta tag content
        :param favicon: optional relative filepath or absolute URL to a favicon (default: `None`, NiceGUI icon will be used)
        :param dark: whether to use Quasar's dark mode (defaults to `dark` argument of `run` command)
        :param response_timeout: maximum time for the decorated function to build the page (default: 3.0)
        :param kwargs: additional keyword arguments passed to FastAPI's @app.get method
        """

        return NiceguiAdminPage(
            path=path,
            layout_name=layout_name,
            title=title,
            viewport=viewport,
            favicon=favicon,
            dark=dark,
            response_timeout=response_timeout,
            api_router=self,
            **kwargs
        )
