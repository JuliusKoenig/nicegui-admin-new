import importlib
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import uvicorn
from celery import Celery
from fastapi import FastAPI
from nicegui import ui, app as ui_app, APIRouter

from nicegui_admin_new.console import console
from nicegui_admin_new.extension import NiceguiAdminBaseExtension
from nicegui_admin_new.layout import NiceGuiAdminBaseLayout
from nicegui_admin_new.settings import Settings
from nicegui_admin_new.type import NiceguiAdminType
from nicegui_admin_new.task import NiceguiAdminBaseTask


@dataclass
class NiceguiBaseAdmin(NiceguiAdminType):
    router: APIRouter = field(default_factory=lambda: APIRouter(prefix=settings.nicegui_mount_path),
                                              metadata={"private": True})

    def __post_init__(self):
        super().__post_init__()

        # register root page
        self.router.get("/")(self.root)

        def _scan_for_python_files(root: Path):
            files = []
            for d in root.iterdir():
                if d.is_dir():
                    r = _scan_for_python_files(root=d)
                    files.extend(r)
                elif d.is_file() and d.suffix == ".py" and d.stem != "__init__":
                    files.append(d)
            return files

        # load core tasks
        _python_file_paths = _scan_for_python_files(root=Path(__file__).parent / "tasks")

        # get import strings
        _import_strings = []
        for _python_file_path in _python_file_paths:
            _import_string = _python_file_path.relative_to(_python_file_path.parent.parent.parent).with_suffix("").as_posix().replace("/", ".")
            _import_strings.append(_import_string)

        # import task files
        for _import_string in _import_strings:
            try:
                importlib.import_module(_import_string)
            except ModuleNotFoundError as e:
                console.print(f"Module '{_import_string}' not found!\n"
                              f"{e}", style="red")
                raise e
            except Exception as e:
                console.print(f"Error loading module '{_import_string}'!\n"
                              f"{e}", style="red")
                raise e

        # load core layouts
        _python_file_paths = _scan_for_python_files(root=Path(__file__).parent / "layouts")

        # get import strings
        _import_strings = []
        for _python_file_path in _python_file_paths:
            _import_string = _python_file_path.relative_to(_python_file_path.parent.parent.parent).with_suffix("").as_posix().replace("/", ".")
            _import_strings.append(_import_string)

        # import layout files
        for _import_string in _import_strings:
            try:
                layout_module = importlib.import_module(_import_string)

                # look up for NiceGuiAdminBaseLayout subclasses in module
                for attr_name, attr in layout_module.__dict__.items():
                    if attr_name.startswith("_"):
                        continue

                    # check if attr is a instance of NiceGuiAdminBaseLayout
                    if not isinstance(attr, NiceGuiAdminBaseLayout):
                        continue

                    # add extension
                    console.print(f"include layout '{attr_name}'")
                    self.add_child(attr)
            except ModuleNotFoundError as e:
                console.print(f"Module '{_import_string}' not found!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue
            except Exception as e:
                console.print(f"Error loading module '{_import_string}'!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue

        # load core routes
        _python_file_paths = _scan_for_python_files(root=Path(__file__).parent / "routers")

        # get import strings
        _import_strings = []
        for _python_file_path in _python_file_paths:
            _import_string = _python_file_path.relative_to(_python_file_path.parent.parent.parent).with_suffix("").as_posix().replace("/", ".")
            _import_strings.append(_import_string)

        # import router files
        for _import_string in _import_strings:
            try:
                router_module = importlib.import_module(_import_string)
                print()

                # look up for NiceGuiAdminBaseAPIRouter subclasses in module
                for attr_name, attr in router_module.__dict__.items():
                    if attr_name.startswith("_"):
                        continue

                    # check if attr is a instance of NiceGuiAdminBaseAPIRouter
                    if not isinstance(attr, APIRouter):
                        continue

                    # add extension
                    console.print(f"include router '{attr_name}'")
                    self.router.include_router(attr)
            except ModuleNotFoundError as e:
                console.print(f"Module '{_import_string}' not found!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue
            except Exception as e:
                console.print(f"Error loading module '{_import_string}'!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue

        # load extensions
        for extension_name in settings.active_extensions:
            try:
                extension_module = importlib.import_module(extension_name)

                # look up for NiceguiAdminBaseExtension subclasses in module
                for attr_name, attr in extension_module.__dict__.items():
                    if attr_name.startswith("_"):
                        continue

                    # check if attr is a instance of NiceguiAdminBaseExtension
                    if not isinstance(attr, NiceguiAdminBaseExtension):
                        continue

                    # add extension
                    self.add_child(attr)

                for extension_name, extension in self.extensions.items():
                    # lookup for python files
                    _python_file_paths = []
                    for _task_directory in extension.info.task_directories:
                        _result = _scan_for_python_files(root=_task_directory)
                        _python_file_paths.extend(_result)

                    # get import strings
                    _import_strings = []
                    for _python_file_path in _python_file_paths:
                        _import_string = _python_file_path.relative_to(Path(extension.info.base_path).parent).with_suffix("").as_posix().replace("/", ".")
                        _import_strings.append(_import_string)

                    # import task files
                    for _import_string in _import_strings:
                        importlib.import_module(_import_string)
            except ModuleNotFoundError as e:
                console.print(f"Extension '{extension_name}' not found!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue
            except Exception as e:
                console.print(f"Error loading extension '{extension_name}'!\n"
                              f"{e}", style="red")
                tb = traceback.format_tb(e.__traceback__)
                console.print(tb, style="red")
                continue

        # include router
        core_api_app.include_router(self.router)

    @property
    def extensions(self) -> dict[str, NiceguiAdminBaseExtension]:
        extensions = {}
        for children_name, children in self.children.items():
            if not isinstance(children, NiceguiAdminBaseExtension):
                continue
            extensions[children_name] = children
        return extensions

    @property
    def layouts(self) -> dict[str, NiceGuiAdminBaseLayout]:
        layouts = {}
        for children_name, children in self.children.items():
            if not isinstance(children, NiceGuiAdminBaseLayout):
                continue
            layouts[children_name] = children
        return layouts

    async def root(self):
        return {"info": "Welcome to the Nicegui Admin!"}
#         async def start_new_task():
#             console.pager("start new task")
#             # result: AsyncResult = send_mail.apply_async(kwargs={"recipient": receiver.value,
#             #                                                     "subject": subject.value,
#             #                                                     "html_str": editor.value})
#             # ui.notify(result)
#
#         ui.label("Worker Test")
#
#         with ui.card().classes("w-full").tight():
#             with ui.card_section().classes("w-full"):
#                 ui.label("Versenden einer Test E-Mail").classes("text-xl text-bold")
#             ui.separator()
#             with ui.card_section().props("horizontal").classes("w-full"):
#                 with ui.card_section().classes("w-full"):
#                     receiver = ui.input(value="julius@koenig-site.de",
#                                         placeholder="Receiver").props("outlined dense").classes("w-full, mb-1")
#                     subject = ui.input(value="Test Mail from Worker Test",
#                                        placeholder="Subject").props("outlined dense").classes("w-full mb-1")
#                     editor = ui.editor(value="""\
# <html>
#   <body>
#     <p>Hi,<br>
#        How are you?<br>
#        <a href="http://www.realpython.com">Real Python</a>
#        has many great tutorials.
#     </p>
#   </body>
# </html>
# """,
#                                        placeholder="Enter your message body here...")
#             ui.separator()
#             with ui.card_actions().classes("w-full"):
#                 ui.button(text="Send",
#                           icon="send",
#                           on_click=lambda e: start_new_task())
#
#         with ui.header(elevated=True):
#             ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props("flat").props("color=white")
#         with ui.left_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as left_drawer:
#             ui.label("LEFT DRAWER")
#
#         log_drawer = LogDrawer(title="Task Log",
#                                opened=False)
#
#         with ui.footer():
#             ui.label("FOOTER")
#
#         with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20):
#             ui.button("Scroll to Top")

# init settings
settings = Settings()

# init api app
core_api_app = FastAPI(contact=settings.fastapi_contact,
                       debug=settings.fastapi_debug,
                       deprecated=settings.fastapi_deprecated,
                       description=settings.fastapi_description,
                       docs_url=f"{settings.nicegui_mount_path}{settings.fastapi_docs_url}",
                       extra=settings.fastapi_extra,
                       include_in_schema=settings.fastapi_include_in_schema,
                       license_info=settings.fastapi_license_info,
                       openapi_external_docs=settings.fastapi_openapi_external_docs,
                       openapi_prefix=settings.fastapi_openapi_prefix,
                       openapi_tags=settings.fastapi_openapi_tags,
                       openapi_url=f"{settings.nicegui_mount_path}{settings.fastapi_openapi_url}",
                       redirect_slashes=settings.fastapi_redirect_slashes,
                       redoc_url=f"{settings.nicegui_mount_path}{settings.fastapi_redoc_url}",
                       responses=settings.fastapi_responses,
                       root_path=settings.fastapi_root_path,
                       root_path_in_servers=settings.fastapi_root_path_in_servers,
                       separate_input_output_schemas=settings.fastapi_separate_input_output_schemas,
                       servers=settings.fastapi_servers,
                       strict_content_type=settings.fastapi_strict_content_type,
                       summary=settings.fastapi_summary,
                       swagger_ui_init_oauth=settings.fastapi_swagger_ui_init_oauth,
                       swagger_ui_oauth2_redirect_url=f"{settings.nicegui_mount_path}{settings.fastapi_swagger_ui_oauth2_redirect_url}",
                       swagger_ui_parameters=settings.fastapi_swagger_ui_parameters,
                       terms_of_service=settings.fastapi_terms_of_service,
                       title=settings.fastapi_title,
                       version=settings.fastapi_version)

core_api_router: APIRouter = core_api_app.router

# init ui app
ui_app.docs_url = "/docs"
ui_app.redoc_url = "/redoc"
ui_app.openapi_url = "/openapi.json"
ui_app.setup()
ui.run_with(app=core_api_app,
            title=settings.nicegui_title,
            viewport=settings.nicegui_viewport,
            favicon=settings.nicegui_favicon,
            dark=settings.nicegui_dark,
            language=settings.nicegui_language,
            binding_refresh_interval=settings.nicegui_binding_refresh_interval,
            reconnect_timeout=settings.nicegui_reconnect_timeout,
            message_history_length=settings.nicegui_message_history_length,
            cache_control_directives=settings.nicegui_cache_control_directives,
            gzip_middleware_factory=None,
            mount_path=settings.nicegui_mount_path,
            on_air=None,
            tailwind=settings.nicegui_tailwind,
            unocss=settings.nicegui_unocss,
            prod_js=settings.nicegui_prod_js,
            storage_secret=settings.nicegui_storage_secret,
            show_welcome_message=settings.nicegui_show_welcome_message)

# init celery
celery = Celery(__name__,
                include=[f"{__name__}.extensions",
                         f"{__name__}.tasks"],
                task_cls=f"{__name__}.task:{NiceguiAdminBaseTask.__name__}")
celery.conf.update(broker_url=(f"pyamqp://{settings.broker_username}:"
                               f"{settings.broker_password}@"
                               f"{settings.broker_host}:"
                               f"{settings.broker_port}"),
                   result_backend=(f"db+mysql+pymysql://"
                                   f"{settings.db_username}:"
                                   f"{settings.db_password}@"
                                   f"{settings.db_host}:"
                                   f"{settings.db_port}/"
                                   f"{settings.db_name}"),
                   beat_scheduler="sqlalchemy_celery_beat.schedulers:DatabaseScheduler",
                   beat_dburi=(f"mysql+pymysql://"
                               f"{settings.db_username}:"
                               f"{settings.db_password}@"
                               f"{settings.db_host}:"
                               f"{settings.db_port}/"
                               f"{settings.db_name}"),
                   task_serializer="json",
                   result_serializer="json",
                   accept_content=["json"],
                   timezone="Europe/Berlin",
                   enable_utc=True)

# init admin
core_admin = NiceguiBaseAdmin()


# start uvicorn
app =f"{Path(__file__).relative_to(Path(__file__).parent.parent).with_suffix("")}:core_api_app".replace("/", ".")
uvicorn.run(host=str(settings.uvicorn_host),
            port=settings.uvicorn_port,
            reload=settings.uvicorn_reload,
            app=app,
            workers=settings.uvicorn_workers,
            log_level="info")
