import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import uvicorn
from celery import Celery
from celery.apps.worker import Worker
from nicegui import ui, app as ui_app, App as UiApp, Client
from nicegui.middlewares import RedirectWithPrefixMiddleware, SetCacheControlMiddleware
from starlette.routing import Route
from typer import Typer

from nicegui_admin_new import __name__ as __package_name__
from nicegui_admin_new.extension import NiceguiAdminBaseExtension
from nicegui_admin_new.layout import NiceguiAdminLayout
from nicegui_admin_new.logger import logger as __module_logger__
from nicegui_admin_new.routing import NiceguiAdminAPIRouter
from nicegui_admin_new.settings import NiceguiAdminSettings
from nicegui_admin_new.task import NiceguiAdminBaseTask
from nicegui_admin_new.type import NiceguiAdminType


@dataclass
class NiceguiAdmin(NiceguiAdminType):
    settings: NiceguiAdminSettings = field(default_factory=lambda: NiceguiAdminSettings(),
                                           metadata={"private": True})
    logger: logging.Logger = field(default=__module_logger__,
                                   metadata={"private": True})

    def __post_init__(self):
        super().__post_init__()

        # init ui app
        self.logger.debug(f"Init Nicegui App ...")
        ui_app.config.add_run_config(
            reload=False,
            title=self.settings.nicegui_title,
            viewport=self.settings.nicegui_viewport,
            favicon=self.settings.nicegui_favicon,
            dark=self.settings.nicegui_dark,
            language=self.settings.nicegui_language,
            binding_refresh_interval=self.settings.nicegui_binding_refresh_interval,
            reconnect_timeout=self.settings.nicegui_reconnect_timeout,
            message_history_length=self.settings.nicegui_message_history_length,
            cache_control_directives=self.settings.nicegui_cache_control_directives,
            tailwind=self.settings.nicegui_tailwind,
            unocss=self.settings.nicegui_unocss,
            prod_js=self.settings.nicegui_prod_js,
            show_welcome_message=self.settings.nicegui_show_welcome_message,
            markdown=False,
        )
        ui_app.config.endpoint_documentation = "all"
        ui_app.add_middleware(RedirectWithPrefixMiddleware)
        ui_app.add_middleware(SetCacheControlMiddleware)

        for route in ui_app.routes:
            if not isinstance(route, Route):
                continue
            if route.path.startswith('/_nicegui') and hasattr(route, 'methods'):
                route.tags = ["internal"]
                route.include_in_schema = True
            if route.path == '/' or route.path in Client.page_routes.values():
                route.include_in_schema = True

        ui_app.docs_url = self.settings.fastapi_docs_url
        ui_app.redoc_url = self.settings.fastapi_redoc_url
        ui_app.openapi_url = self.settings.fastapi_openapi_url
        ui_app.title = self.settings.fastapi_title
        ui_app.summary = self.settings.fastapi_summary
        ui_app.description = self.settings.fastapi_description
        ui_app.version = self.settings.fastapi_version
        ui_app.terms_of_service = self.settings.fastapi_terms_of_service
        ui_app.contact = self.settings.fastapi_contact
        ui_app.license_info = self.settings.fastapi_license_info
        ui_app.setup()
        ui_app.admin = self
        self.logger.debug(f"Nicegui App init done.")

        # import router
        self.logger.debug(f"Import Nicegui Admin Router ...")
        for router_file_path in self._scan_for_python_files(root=Path(__file__).parent / "router"):
            self._import_router(router_file_path=router_file_path)
        self.logger.debug(f"Nicegui Admin Router import done.")

        # import layouts
        self.logger.debug(f"Import Nicegui Admin Layouts ...")
        for layout_file_path in self._scan_for_python_files(root=Path(__file__).parent / "layouts"):
            self._import_layout(layout_file_path=layout_file_path)

        # add static files
        self.logger.debug(f"Add static files ...")
        self._add_static(url_path="/static",
                         local_directory=Path(__file__).parent / "static")
        self.logger.debug(f"Add static files done.")

        # get tasks directories
        tasks_directories = [Path(__file__).parent / "tasks"]

        # init celery
        self.logger.debug(f"Init Celery ...")
        include = [task_directory
                   .relative_to(Path(__file__).parent.parent)
                   .with_suffix("")
                   .as_posix()
                   .replace("/", ".") for task_directory in tasks_directories]
        self._celery = Celery(__package_name__,
                              include=include,
                              task_cls=f"{__package_name__}.task:NiceguiAdminBaseTask")
        self._celery.conf.update(broker_url=(f"pyamqp://{self.settings.broker_username}:"
                                             f"{self.settings.broker_password}@"
                                             f"{self.settings.broker_host}:"
                                             f"{self.settings.broker_port}"),
                                 result_backend=(f"db+mysql+pymysql://"
                                                 f"{self.settings.db_username}:"
                                                 f"{self.settings.db_password}@"
                                                 f"{self.settings.db_host}:"
                                                 f"{self.settings.db_port}/"
                                                 f"{self.settings.db_name}"),
                                 beat_scheduler="sqlalchemy_celery_beat.schedulers:DatabaseScheduler",
                                 beat_dburi=(f"mysql+pymysql://"
                                             f"{self.settings.db_username}:"
                                             f"{self.settings.db_password}@"
                                             f"{self.settings.db_host}:"
                                             f"{self.settings.db_port}/"
                                             f"{self.settings.db_name}"),
                                 task_serializer="json",
                                 result_serializer="json",
                                 accept_content=["json"],
                                 timezone="Europe/Berlin",
                                 enable_utc=True)
        self.logger.debug(f"Celery init done.")

        # import tasks
        self.logger.debug(f"Import Celery Tasks ...")
        for task_directory in tasks_directories:
            for task_file_path in self._scan_for_python_files(root=task_directory):
                self._import_task(task_file_path=task_file_path)
        self.logger.debug(f"Celery Tasks import done.")

        # init worker
        self._celery_worker = self._celery.Worker(include=include,
                                                  task_cls=f"{__package_name__}.task:NiceguiAdminBaseTask")

        # load extensions
        for extension_name in self.settings.active_extensions:
            self._import_extension(extension_name=extension_name)

        # setup routes & pages
        ui.page("/")(self.ui_root)
        ui_app.get("/api")(self.api_root)

    def __call__(self, *args, **kwargs) -> Typer:
        cli = Typer()

        cli.command(name="serve", help="Start the Nicegui Admin Server")(self.serve)
        cli.command(name="worker", help="Start a Celery Worker")(self.worker)

        return cli(*args, **kwargs)

    def _scan_for_python_files(self,
                               root: Path):
        self.logger.debug(f"Scan for python files in {root} ...")
        files = []
        for d in root.iterdir():
            if d.is_dir():
                r = self._scan_for_python_files(root=d)
                files.extend(r)
            elif d.is_file() and d.suffix == ".py" and d.stem != "__init__":
                files.append(d)
        self.logger.debug(f"Scan for python files in {root} done. Got {len(files)} files.")
        return files

    def _get_search_objs(self,
                         module: ModuleType,
                         import_cls: type,
                         instance_mode: bool = True) -> list[Any]:
        self.logger.debug(f"Get search objects in {module.__name__} ...")

        search_objs = []
        for attr_name, attr in module.__dict__.items():
            if attr_name.startswith("_"):
                continue
            if attr is import_cls:
                continue
            if instance_mode:
                if not isinstance(attr, import_cls):
                    continue
            else:
                try:
                    if not issubclass(attr, import_cls):
                        continue
                except TypeError:
                    continue
            search_objs.append(attr)

        self.logger.debug(f"Get search objects in {module.__name__} done. Got {len(search_objs)} objects.")

        return search_objs

    def _import_file(self,
                     file_path: Path,
                     import_cls: type,
                     base_path: Path | None = None,
                     instance_mode: bool = True) -> Any:
        self.logger.debug(f"Import file {file_path} ...")

        # check if file exists
        if not file_path.is_file():
            raise FileNotFoundError(f"File '{file_path}' not found!")

        # set base path
        if base_path is None:
            base_path = Path(__file__).parent.parent

        # get import string
        import_string = file_path.relative_to(base_path).with_suffix("").as_posix().replace("/", ".")
        module = importlib.import_module(import_string)

        # search for objects
        search_objs = self._get_search_objs(module=module,
                                            import_cls=import_cls,
                                            instance_mode=instance_mode)

        self.logger.debug(f"Import file {file_path} done. Got {len(search_objs)} objects.")

        return search_objs

    def _import_router(self,
                       router_file_path: Path,
                       base_path: Path | None = None,
                       overwrite_tags: list[str] | None = None,
                       overwrite_prefix: str | None = None) -> None:
        self.logger.debug(f"Import router {router_file_path} ...")
        api_router = self._import_file(file_path=router_file_path,
                                       import_cls=NiceguiAdminAPIRouter,
                                       base_path=base_path,
                                       instance_mode=True)
        for api_router_instance in api_router:
            # overwrite tags
            if overwrite_tags:
                api_router_instance.tags = overwrite_tags
                for route in api_router_instance.routes:
                    route.tags = overwrite_tags

            # overwrite prefix
            if overwrite_prefix:
                api_router_instance.prefix = overwrite_prefix + api_router_instance.prefix
                for route in api_router_instance.routes:
                    route.path = overwrite_prefix + route.path

            self.logger.debug(f"Register router {api_router_instance} ...")
            ui_app.include_router(api_router_instance)
        self.logger.debug(f"Import router {router_file_path} done.")

    def _import_layout(self,
                       layout_file_path: Path,
                       base_path: Path | None = None) -> None:
        self.logger.debug(f"Import layout {layout_file_path} ...")
        layouts = self._import_file(file_path=layout_file_path,
                                    import_cls=NiceguiAdminLayout,
                                    base_path=base_path,
                                    instance_mode=True)
        for layout in layouts:
            self.logger.debug(f"Register layout {layout} ...")
            self.add_child(layout)
        self.logger.debug(f"Import layout {layout_file_path} done.")

    def _add_static(self,
                    url_path: str,
                    local_directory: Path,
                    overwrite_tags: list[str] | None = None) -> None:
        if overwrite_tags is None:
            overwrite_tags = []
        if "Static Files" not in overwrite_tags:
            overwrite_tags.append("Static Files")

        self.logger.debug(f"Add static files {url_path} ...")

        routes_backup = self.app.routes.copy()
        self.app.add_static_files(url_path=f"{url_path}",
                                  local_directory=local_directory)
        if overwrite_tags:
            delta = []
            for route in self.app.routes:
                if route in routes_backup:
                    continue
                delta.append(route)
            for route in delta:
                route.tags.extend(overwrite_tags)
        self.logger.debug(f"Add static files {url_path} done.")

    def _import_task(self,
                     task_file_path: Path,
                     base_path: Path | None = None) -> None:
        self.logger.debug(f"Import task {task_file_path} ...")
        tasks = self._import_file(file_path=task_file_path,
                                  import_cls=NiceguiAdminBaseTask,
                                  instance_mode=False,
                                  base_path=base_path)
        for task in tasks:
            self.logger.debug(f"Register task {task} ...")
            self.celery.register_task(task())
        self.logger.debug(f"Import task {task_file_path} done.")

    def _import_extension(self,
                          extension_name: Path) -> None:
        self.logger.debug(f"Import extension {extension_name} ...")

        # import extension
        extension_module = importlib.import_module(extension_name)

        # search for NiceguiAdminBaseExtension subclasses in module
        extensions: NiceguiAdminBaseExtension = self._get_search_objs(module=extension_module,
                                                                      import_cls=NiceguiAdminBaseExtension,
                                                                      instance_mode=True)

        # add extension
        for extension in extensions:
            # import router
            self.logger.debug(f"Import router for extension {extension.info.name} ...")
            for router_directory in extension.info.router_directories:
                self.logger.debug(f"Import router {router_directory} for extension {extension.info.name} ...")
                for router_file_path in self._scan_for_python_files(root=router_directory):
                    self._import_router(router_file_path=router_file_path,
                                        base_path=extension.info.base_path.parent,
                                        overwrite_tags=[f"Extensions - {extension.info.title}"],
                                        overwrite_prefix=f"/extensions/{extension.info.short_name}")
                self.logger.debug(f"Import router {router_directory} for extension {extension.info.name} done.")
            self.logger.debug(f"Import router for extension {extension.info.name} done.")

            # import layouts
            self.logger.debug(f"Import layouts for extension {extension.info.name} ...")
            for layout_directory in extension.info.layout_directories:
                self.logger.debug(f"Import layouts {layout_directory} for extension {extension.info.name} ...")
                for layout_file_path in self._scan_for_python_files(root=layout_directory):
                    self._import_layout(layout_file_path=layout_file_path,
                                        base_path=extension.info.base_path.parent)
                self.logger.debug(f"Import layouts {layout_directory} for extension {extension.info.name} done.")
            self.logger.debug(f"Import layouts for extension {extension.info.name} done.")

            # add static files
            self.logger.debug(f"Add static files for extension {extension.info.name} ...")
            for static_directory in extension.info.static_directories:
                self.logger.debug(f"Add static files {static_directory} for extension {extension.info.name} ...")
                self._add_static(url_path=f"/extensions/{extension.info.short_name}/static",
                                 local_directory=static_directory,
                                 overwrite_tags=[f"Extensions - {extension.info.title}"])
                self.logger.debug(f"Add static files {static_directory} for extension {extension.info.name} done.")

            # import tasks
            self.logger.debug(f"Import tasks for extension {extension.info.name} ...")
            for task_directory in extension.info.task_directories:
                self.logger.debug(f"Import tasks {task_directory} for extension {extension.info.name} ...")
                for task_file_path in self._scan_for_python_files(root=task_directory):
                    self._import_task(task_file_path=task_file_path,
                                      base_path=extension.info.base_path.parent)
                self.logger.debug(f"Import tasks {task_directory} for extension {extension.info.name} done.")
            self.logger.debug(f"Import tasks for extension {extension.info.name} done.")

            self.add_child(extension)

        self.logger.debug(f"Import extension {extension_name} done.")

    @property
    def app(self) -> UiApp:
        return ui_app

    @property
    def routes(self) -> list[Route]:
        return self.app.routes

    @property
    def layouts(self) -> list[NiceguiAdminLayout]:
        layouts = {}
        for children_name, children in self.children.items():
            if isinstance(children, NiceguiAdminLayout):
                layouts[children_name] = children
        return layouts

    @property
    def celery(self) -> Celery:
        return self._celery

    @property
    def celery_worker(self) -> Worker:
        return self._celery_worker

    @property
    def tasks(self):
        return self.celery.tasks

    @property
    def extensions(self) -> dict[str, NiceguiAdminBaseExtension]:
        extensions = {}
        for children_name, children in self.children.items():
            if isinstance(children, NiceguiAdminBaseExtension):
                extensions[children_name] = children
        return extensions

    async def ui_root(self):
        ui.label("root")

    async def api_root(self):
        self.logger.debug(f"Nicegui Admin API Root ...")
        return {"message": "Hello World"}

    def serve(self):
        self.logger.info(f"Starting Nicegui Admin Server at http://{self.settings.uvicorn_host}:{self.settings.uvicorn_port} ...")

        # start uvicorn
        uvicorn.run(host=str(self.settings.uvicorn_host),
                    port=self.settings.uvicorn_port,
                    reload=self.settings.uvicorn_reload,
                    app=ui_app,
                    workers=self.settings.uvicorn_workers,
                    log_level="info")

    def worker(self):
        self.celery_worker.start()
