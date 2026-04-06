from pydantic import ConfigDict
from pydantic.dataclasses import dataclass  # noqa: F401


config_dict = ConfigDict(
    arbitrary_types_allowed=True, kw_only=True, slots=True, extra="forbid"
)
