import importlib
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field, DirectoryPath, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings

from nicegui_admin_new import settings
from nicegui_admin_new.settings import BASE_PREFIX
from nicegui_admin_new.type import NiceguiAdminType

EXTENSION_BASE_PREFIX = f"{BASE_PREFIX}EXTENSION_"


@dataclass
class NiceguiAdminBaseExtension(NiceguiAdminType):
    base_path: Path = field(init=False,
                            repr=False,
                            metadata={"private": True})

    class Info(BaseModel):
        base_path: DirectoryPath = Field(default=...,
                                         title="Base Path",
                                         description="Base Path for extension")
        name: str = Field(default=...,
                          title="Name",
                          description="Name for extension")
        description: str = Field(default=...,
                                 title="Description",
                                 description="Description for extension")
        version: str = Field(default=...,
                             title="Version",
                             description="Version for extension")
        view_directories: list[DirectoryPath] = Field(default_factory=list,
                                                      title="View Directories",
                                                      description="View Directories for extension")
        task_directories: list[DirectoryPath] = Field(default_factory=list,
                                                      title="Task Directories",
                                                      description="Task Directories for extension")

        @field_validator("view_directories", "task_directories", mode="before")
        @classmethod
        def _ensure_base_path(cls,
                              value: list[DirectoryPath],
                              info: ValidationInfo) -> list[DirectoryPath]:
            base_path = info.data["base_path"]
            new_value = []
            for path in value:
                new_path = base_path / path
                new_value.append(new_path)
            return new_value

    info: Info = field(default=...,
                       repr=False,
                       metadata={"private": True})

    class Settings(BaseSettings):
        model_config = {
            "case_sensitive": False,
            "env_prefix": EXTENSION_BASE_PREFIX
        }

    settings: Settings = field(default=...,
                               repr=False,
                               metadata={"private": True})

    def __post_init__(self):
        # init info
        if self.info is Ellipsis:
            self.info = self.Info()

        # init settings
        if self.settings is Ellipsis:
            self.settings = self.Settings()

        # set name
        self.name = self.info.name

        # init
        super().__post_init__()