from dataclasses import dataclass

from nicegui_admin_new.type import NiceguiAdminType


@dataclass
class NiceGuiAdminBaseLayout(NiceguiAdminType):
    def __post_init__(self):
        super().__post_init__()
        print()

    def __call__(self, *args, **kwargs):
        print()