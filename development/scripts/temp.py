from PyMieSim.units import Quantity, ureg

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
    def check(value):
        assert isinstance(value, Quantity), (
            f"Expected a pint Quantity instance, got {type(value)}"
        )

class Energy(BaseUnit):
    """Quantity specifically for energy units."""
    _expected_dim = "[energy]"

    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.check("[energy]"), (
            f"Value units {value.dimensionality} do not match energy units"
        )

class Time(BaseUnit):
    """Quantity specifically for time units."""
    _expected_dim = "[time]"

    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.check("[time]"), (
            f"Value units {value.dimensionality} do not match time units"
        )

class Power(BaseUnit):
    """Quantity specifically for power units."""
    _expected_dim = "[power]"

    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.check("[power]"), (
            f"Value units {value.dimensionality} do not match power units"
        )

# Examples
e = 5 * ureg.joule
t = 2 * ureg.second
p = 1 * ureg.watt

assert isinstance(e, Energy)   # True
assert isinstance(t, Time)     # True
assert isinstance(p, Power)    # True
assert not isinstance(p, Energy)  # Correct: watt ≠ energy


from pydantic.dataclasses import dataclass


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Detector():
    phi_angle: Power

test = Detector(phi_angle=0 * ureg.watt)