# Initialize a unit registry
from PyMieSim.units import ureg, Quantity  # noqa F401
from PyMieSim.units import *  # noqa F401
import pint


class UnitMeta(type):
    """
    Metaclass that makes isinstance(x, SomeUnit) return True
    when x is a pint.Quantity with the right dimensionality.
    """

    def __instancecheck__(cls, obj):
        if not isinstance(obj, Quantity):
            return False
        expected = getattr(cls, "_expected_dim", None)
        if expected is None:
            return False
        # Use pint's dimensionality check; accepts strings like "[energy]"
        return obj.check(expected)


class BaseUnit(metaclass=UnitMeta):
    _expected_dim: str | None = None

    @staticmethod
    def _check(value):
        assert isinstance(
            value, Quantity
        ), f"Expected a pint Quantity instance, got {type(value)}"


# class Power(BaseUnit):
#     """Quantity specifically for power units."""
#     _expected_dim = "watt"


class Power(BaseUnit):
    """Quantity specifically for power units."""

    _expected_dim = "[power]"

    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.check(
            "[power]"
        ), f"Value units {value.dimensionality} do not match power units"


from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True, kw_only=True, slots=True, extra="forbid"
)


@dataclass(config=config_dict)
class Detector:
    phi_angle: Power


test = Detector(phi_angle=0 * ureg.watt)
