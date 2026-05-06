from dataclasses import dataclass, field, fields
from typing import Optional, TypeVar


T = TypeVar("T", bound="NiceguiAdminType")


@dataclass()
class NiceguiAdminType:
    name: str | None = field(default=None)
    parent: Optional["NiceguiAdminType"] = field(default=None,
                                                 repr=False,
                                                 metadata={"private": True})
    _init: bool = field(default=False,
                        init=False,
                        repr=False)
    _children: list["NiceguiAdminType"] = field(default_factory=list,
                                                init=False,
                                                repr=False)

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__
        if self.parent:
            self.parent.add_child(self)
        else:
            ...  # ToDo: register startup and shutdown handlers only for root objects
        self._init = True

    def __setattr__(self,
                    key,
                    value):
        if self._init:
            _field = None
            for f in fields(self):
                if f.name == key:
                    _field = f
                    break
            if _field is not None:
                is_private = _field.metadata.get("private", False)
                if is_private:
                    raise AttributeError(f"{key} is a private field and cannot be set directly")
        super().__setattr__(key, value)

    @property
    def root_parent(self) -> "NiceguiAdminType":
        if self.parent is not None:
            return self.parent.root_parent
        else:
            return self

    @property
    def children(self) -> dict[str, "NiceguiAdminType"]:
        children = {}
        for child in self._children:
            children[child.name] = child
        return children

    def add_child(self,
                  obj: T | type[T],
                  **kwargs) -> T:
        if type(obj) is type:
            return obj(parent=self,
                       **kwargs)
        else:
            if not isinstance(obj, NiceguiAdminType):
                raise ValueError(f"{obj} is not an instance of NiceguiAdminType")
            if obj in self._children:
                raise ValueError(f"{obj} is already a child of {self}")
            setattr(obj, "_init", False)
            obj.parent = self
            setattr(obj, "_init", True)
            self._children.append(obj)
            return obj

    def get_child_by_name(self,
                          name: str) -> T | None:
        if name not in self.children:
            return None
        return self.children[name]

    def get_child_by_type(self,
                          t: type[T]) -> list[T]:
        result = []
        for name, child in self.children.items():
            child_type = type(child)
            if issubclass(child_type, t):
                result.append(child)
        return result
