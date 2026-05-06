from nicegui import ui


class LogDrawer(ui.element):
    def __init__(self,
                 title: str,
                 height: int = 400,
                 opened: bool = False,
                 footer_mode: bool = True):
        super().__init__("div")

        with self:
            self.button = ui.button(on_click=self.toggle)
            with ui.row() as self.title_row:
                self.title = ui.label(title)

        self._height = height
        self._opened = opened
        self._footer_mode = footer_mode
        self._apply_style()

    def _apply_style(self):
        self.classes(
            f"fixed left-0 right-0 bottom-{14 if self.footer_mode else 0} z-50 "
            f"z-[6000] "
            f"bg-gray dark:bg-gray-900 border-t shadow-xl "
            f"transition-transform duration-300 "
            f"p-4"
        ).style(
            f"left: 300px; "
            f"height: {self.height}px; "
            f"border-top: 1px solid #ccc; "
            f"transform: translateY({self.height}px);"
        )
        self.title_row.classes("w-full items-center justify-between")
        self.title.classes("text-xl font-bold")
        self.button.props("round "
                          "unelevated").classes("absolute left-1/2 -top-6 -translate-x-1/2 "
                                                "z-[6001]")
        self.button.icon = "keyboard_arrow_down" if self.opened else "keyboard_arrow_up"
        if self._opened:
            self.style(f"height: {self.height}px; transform: translateY(0);")
        else:
            self.style(f"height: {self.height}px; transform: translateY({self.height - 60}px);")

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int):
        self._height = value
        self._apply_style()

    @property
    def opened(self) -> bool:
        return self._opened

    @opened.setter
    def opened(self, value: bool):
        self._opened = value
        self._apply_style()

    @property
    def footer_mode(self) -> bool:
        return self._footer_mode

    @footer_mode.setter
    def footer_mode(self, value: bool):
        self._footer_mode = value
        self._apply_style()

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.opened = False

    def toggle(self) -> None:
        if self.opened:
            self.close()
        else:
            self.open()
