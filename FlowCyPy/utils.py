from pydantic import ConfigDict
from pydantic.dataclasses import dataclass  # noqa: F401


class StrictDataclassMixing:
    def __setattr__(self, name: str, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        # Merge annotations from all parent classes
        annotations = {}
        for cls in self.__class__.__mro__:
            if "__annotations__" in cls.__dict__:
                annotations.update(cls.__annotations__)

        if name not in annotations:
            raise AttributeError(
                f"Cannot add new attribute '{name}' to {self.__class__.__name__}"
            )

        super().__setattr__(name, value)


config_dict = ConfigDict(
    arbitrary_types_allowed=True, kw_only=True, slots=True, extra="forbid"
)
