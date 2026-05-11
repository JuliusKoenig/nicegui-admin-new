from dataclasses import dataclass

from nicegui_admin_new.layout import NiceguiAdminLayout


@dataclass
class DefaultLayout(NiceguiAdminLayout):
    def __post_init__(self):
        super().__post_init__()

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


default_layout = DefaultLayout(name="default")
