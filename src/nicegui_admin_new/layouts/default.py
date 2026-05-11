from dataclasses import dataclass

from nicegui import ui

from nicegui_admin_new.elements.log_drawer import LogDrawer
from nicegui_admin_new.layout import NiceguiAdminLayout


@dataclass
class DefaultLayout(NiceguiAdminLayout):
    def __post_init__(self):
        super().__post_init__()

    def __call__(self, *args, **kwargs) -> NiceguiAdminLayout.Result:
        result = super().__call__(*args, **kwargs)

        with ui.header(elevated=True) as result.elements["header"]:
            result.elements["left_menu_button"] = ui.button(on_click=lambda: result.elements["left_drawer"].toggle(), icon="menu").props("flat").props("color=white")
        with ui.left_drawer(fixed=False).style("background-color: #ebf1fa").props("bordered") as result.elements["left_drawer"]:
            ...

        result.elements["log_drawer"] = LogDrawer(title="Task Log",
                                         opened=False)

        with ui.footer() as result.elements["footer"]:
            ...

        with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20) as result.elements["page_scroller"]:
            result.elements["page_scroller_button"] = ui.button("Scroll to Top")

        return result


default_layout = DefaultLayout(name="default")
