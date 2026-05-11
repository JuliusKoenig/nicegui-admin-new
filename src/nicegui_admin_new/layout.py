from dataclasses import dataclass, field

from nicegui.element import Element

from nicegui_admin_new.type import NiceguiAdminType


@dataclass
class NiceguiAdminLayout(NiceguiAdminType):
    @dataclass
    class Result:
        elements: dict[str, Element] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()

    def __call__(self, *args, **kwargs) -> Result:
        return self.Result()