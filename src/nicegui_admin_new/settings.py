from ipaddress import IPv4Address
from typing import Any, Literal

from nicegui.language import Language
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_PREFIX = "NICEGUI_ADMIN_"


class NiceguiAdminSettings(BaseSettings):
    model_config = {
        "case_sensitive": False,
        "env_prefix": BASE_PREFIX
    }

    # admin
    active_extensions: list[str] = Field(default_factory=list,
                                         title="Active Extensions",
                                         description="Active Extensions")

    # uvicorn
    uvicorn_host: IPv4Address = Field(default="127.0.0.1",
                                      title="Uvicorn Host",
                                      description="Uvicorn Host")
    uvicorn_port: int = Field(default=8000,
                              title="Uvicorn Port",
                              description="Uvicorn Port",
                              ge=1,
                              lt=65535)
    uvicorn_workers: int | None = Field(default=None,
                                        title="Uvicorn Workers",
                                        description="Uvicorn Workers",
                                        ge=1)
    uvicorn_reload: bool = Field(default=False,
                                 title="Uvicorn Reload",
                                 description="Uvicorn Reload")

    # nicegui
    nicegui_title: str = Field(default="Nicegui-Admin",
                               title="Nicegui Title",
                               description="Nicegui Title")
    nicegui_viewport: str = Field(default="width=device-width, initial-scale=1",
                                  title="Nicegui Viewport",
                                  description="Nicegui Viewport")
    nicegui_favicon: str | None = Field(default=None,
                                        title="Nicegui Favicon",
                                        description="Nicegui Favicon")
    nicegui_dark: bool = Field(default=False,
                               title="Nicegui Dark",
                               description="Nicegui Dark")
    nicegui_language: Language = Field(default="de-DE",
                                       title="Nicegui Language",
                                       description="Nicegui Language")
    nicegui_binding_refresh_interval: float = Field(default=0.1,
                                                    title="Nicegui Binding Refresh Interval",
                                                    description="Nicegui Binding Refresh Interval")
    nicegui_reconnect_timeout: float = Field(default=3,
                                             title="Nicegui Reconnect Timeout",
                                             description="Nicegui Reconnect Timeout")
    nicegui_message_history_length: int = Field(default=1000,
                                                title="Nicegui Message History Length",
                                                description="Nicegui Message History Length")
    nicegui_cache_control_directives: str = Field(default="public, max-age=31536000, immutable, stale-while-revalidate=31536000",
                                                  title="Nicegui Cache Control Directives",
                                                  description="Nicegui Cache Control Directives")
    nicegui_mount_path: str = Field(default="/admin",
                                    title="Nicegui Mount Path",
                                    description="Nicegui Mount Path")
    nicegui_tailwind: bool = Field(default=True,
                                   title="Nicegui Tailwind",
                                   description="Nicegui Tailwind")
    nicegui_unocss: Literal['mini', 'wind3', 'wind4'] | None = Field(default=None,
                                                                     title="Nicegui UnoCSS",
                                                                     description="Nicegui UnoCSS")
    nicegui_prod_js: bool = Field(default=True,
                                  title="Nicegui Prod JS",
                                  description="Nicegui Prod JS")
    nicegui_storage_secret: str | None = Field(default=None,
                                               title="Nicegui Storage Secret",
                                               description="Nicegui Storage Secret")
    nicegui_show_welcome_message: bool = Field(default=True,
                                               title="Nicegui Show Welcome Message",
                                               description="Nicegui Show Welcome Message")

    # fastapi
    fastapi_debug: bool = Field(default=False,
                                title="FastAPI Debug",
                                description="FastAPI Debug")
    fastapi_title: str = Field(default="Nicegui-Admin API",
                               title="FastAPI Title",
                               description="FastAPI Title")
    fastapi_summary: str | None = Field(default="API for Nicegui-Admin",
                                        title="FastAPI Summary",
                                        description="FastAPI Summary")
    fastapi_description: str = Field(default="REST API using to communicate with Nicegui-Admin frontend",
                                     title="FastAPI Description",
                                     description="FastAPI Description")
    fastapi_version: str = Field(default="0.1.0",
                                 title="FastAPI Version",
                                 description="FastAPI Version")
    fastapi_openapi_url: str | None = Field(default="/api/openapi.json",
                                            title="FastAPI OpenAPI URL",
                                            description="FastAPI OpenAPI URL")
    fastapi_openapi_tags: list[dict[str, Any]] | None = Field(default_factory=lambda: [{"name": "nicegui-admin",
                                                                                        "value": "Nicegui-Admin API"}],
                                                              title="FastAPI OpenAPI Tags",
                                                              description="FastAPI OpenAPI Tags")
    fastapi_servers: list[dict[str, str | Any]] | None = Field(default=None,
                                                               title="FastAPI Servers",
                                                               description="FastAPI Servers")
    fastapi_redirect_slashes: bool = Field(default=True,
                                           title="FastAPI Redirect Slashes",
                                           description="FastAPI Redirect Slashes")
    fastapi_docs_url: str | None = Field(default="/api/docs",
                                         title="FastAPI Docs URL",
                                         description="FastAPI Docs URL")
    fastapi_redoc_url: str | None = Field(default="/api/redoc",
                                          title="FastAPI Redoc URL",
                                          description="FastAPI Redoc URL")
    fastapi_swagger_ui_oauth2_redirect_url: str | None = Field(default="/api/docs/oauth2-redirect",
                                                               title="FastAPI Swagger UI OAuth2 Redirect URL",
                                                               description="FastAPI Swagger UI OAuth2 Redirect URL")
    fastapi_swagger_ui_init_oauth: dict[str, Any] | None = Field(default=None,
                                                                 title="FastAPI Swagger UI Init OAuth",
                                                                 description="FastAPI Swagger UI Init OAuth")
    fastapi_terms_of_service: str | None = Field(default=None,
                                                 title="FastAPI Terms of Service",
                                                 description="FastAPI Terms of Service")
    fastapi_contact: dict[str, str | Any] | None = Field(default_factory=dict,
                                                         title="FastAPI Contact",
                                                         description="FastAPI Contact")
    fastapi_license_info: dict[str, str | Any] | None = Field(default=None,
                                                              title="FastAPI License Info",
                                                              description="FastAPI License Info")
    fastapi_openapi_prefix: str = Field(default="",
                                        title="FastAPI OpenAPI Prefix",
                                        description="FastAPI OpenAPI Prefix")
    fastapi_root_path: str = Field(default="",
                                   title="FastAPI Root Path",
                                   description="FastAPI Root Path")
    fastapi_root_path_in_servers: bool = Field(default=True,
                                               title="FastAPI Root Path in Servers",
                                               description="FastAPI Root Path in Servers")
    fastapi_responses: dict[int | str, dict[str, Any]] | None = Field(default=None,
                                                                      title="FastAPI Responses",
                                                                      description="FastAPI Responses")
    fastapi_deprecated: bool | None = Field(default=None,
                                            title="FastAPI Deprecated",
                                            description="FastAPI Deprecated")
    fastapi_include_in_schema: bool = Field(default=True,
                                            title="FastAPI Include in Schema",
                                            description="FastAPI Include in Schema")
    fastapi_swagger_ui_parameters: dict[str, Any] | None = Field(default=None,
                                                                 title="FastAPI Swagger UI Parameters",
                                                                 description="FastAPI Swagger UI Parameters")
    fastapi_separate_input_output_schemas: bool = Field(default=True,
                                                        title="FastAPI Separate Input Output Schemas",
                                                        description="FastAPI Separate Input Output Schemas")
    fastapi_openapi_external_docs: dict[str, Any] | None = Field(default=None,
                                                                 title="FastAPI OpenAPI External Docs",
                                                                 description="FastAPI OpenAPI External Docs")
    fastapi_strict_content_type: bool = Field(default=True,
                                              title="FastAPI Strict Content Type",
                                              description="FastAPI Strict Content Type")
    fastapi_extra: dict[str, Any] = Field(default_factory=dict,
                                          title="FastAPI Extra",
                                          description="FastAPI Extra")

    # broker
    broker_username: str = Field(default=...,
                                 title="Broker Username",
                                 description="Broker Username")
    broker_password: str = Field(default=...,
                                 title="Broker Password",
                                 description="Broker Password")
    broker_host: IPv4Address | str = Field(default=...,
                                     title="Broker Host",
                                     description="Broker Host")
    broker_port: int = Field(default=...,
                             title="Broker Port",
                             description="Broker Port",
                             ge=1,
                             lt=65535)

    # database
    db_username: str = Field(default=...,
                             title="DB Username",
                             description="DB Username")
    db_password: str = Field(default=...,
                             title="DB Password",
                             description="DB Password")
    db_host: IPv4Address | str = Field(default=...,
                                 title="DB Host",
                                 description="DB Host")
    db_port: int = Field(default=...,
                         title="DB Port",
                         description="DB Port",
                         ge=1,
                         lt=65535)
    db_name: str = Field(default=...,
                         title="DB Database Name",
                         description="DB Database Name")