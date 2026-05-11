from dataclasses import dataclass

from nicegui import ui

from nicegui_admin_new.elements.log_drawer import LogDrawer
from nicegui_admin_new.layout import NiceguiAdminLayout


@dataclass
class DefaultLayout(NiceguiAdminLayout):
    def __post_init__(self):
        super().__post_init__()

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        with ui.header(elevated=True) as self.header:
            ui.button(on_click=lambda: self.left_drawer.toggle(), icon="menu").props("flat").props("color=white")
        with ui.left_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as self.left_drawer:
            ui.label("LEFT DRAWER")

        self.log_drawer = LogDrawer(title="Task Log",
                               opened=False)

        with ui.footer() as self.footer:
            ui.label("FOOTER")

        with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20) as self.page_scroller:
            ui.button("Scroll to Top")


default_layout = DefaultLayout(name="default")
