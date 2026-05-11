from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import Field

from nicegui_admin_new.extension import NiceguiAdminBaseExtension, EXTENSION_BASE_PREFIX


@dataclass
class MailingExtension(NiceguiAdminBaseExtension):
    class Settings(NiceguiAdminBaseExtension.Settings):
        model_config = {
            "case_sensitive": False,
            "env_prefix": f"{EXTENSION_BASE_PREFIX}MAILING_"
        }

        smtp_server: str = Field(default=...,
                                 title="SMTP Server",
                                 description="SMTP Server")
        smtp_port: int = Field(default=...,
                               title="SMTP Port",
                               description="SMTP Port")
        smtp_username: str = Field(default=...,
                                   title="SMTP Username",
                                   description="SMTP Username")
        smtp_password: str = Field(default=...,
                                   title="SMTP Password",
                                   description="SMTP Password")

        class Encryption(str, Enum):
            NO_ENCRYPTION = "NO_ENCRYPTION"
            STARTTLS = "STARTTLS"
            SSL = "SSL"

        smtp_use_ssl: Encryption = Field(default=...,
                                         title="SMTP Use SSL",
                                         description="SMTP Use SSL")
        smtp_timeout: int = Field(default=10,
                                  title="SMTP Timeout",
                                  description="SMTP Timeout")
        sender_email: str = Field(default=...,
                                  title="Sender Email",
                                  description="The email address that will be used as the sender of all emails.")
        sender_display_name: str = Field(default="Nicegui Admin - Mailing Extension",
                                         title="Sender Display Name",
                                         description="The display name that will be used as the sender of all emails.")


mailing_extension = MailingExtension(info=NiceguiAdminBaseExtension.Info(base_path=Path(__file__).parent,
                                                                         title="Mailing",
                                                                         name="nicegui_admin_mailing",
                                                                         short_name="mailing",
                                                                         description="Mailing extension for nicegui admin.",
                                                                         version="1.0.0",
                                                                         router_directories=[Path("router")],
                                                                         layout_directories=[],
                                                                         static_directories=[Path("static")],
                                                                         task_directories=[Path("tasks")]))