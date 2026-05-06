from nicegui import ui

from nicegui_admin_new import core_api_router, core_admin

@core_api_router.page("/")
def root():
    ui.label("Hello NiceGUI Admin!")


if __name__ in {"__main__", "__mp_main__"}:
    print()