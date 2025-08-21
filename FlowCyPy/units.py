# Initialize a unit registry
from PyMieSim.units import ureg, Quantity # noqa F401
from PyMieSim.units import *  # noqa F401
import pint

_scaled_units_str_list = [
    'watt', 'volt', 'meter', 'second', 'liter', 'hertz', 'ohm', 'ampere', 'joule', 'coulomb', 'kelvin', 'celsius', 'degree', 'particle'
]

for _units_str in _scaled_units_str_list:
    for scale in ['femto', 'pico', 'nano', 'micro', 'milli', '', 'kilo', 'mega']:
        _unit = scale + _units_str
        globals()[_unit] = getattr(ureg, _unit)


ureg.define("photoelectron = [Float64]")  # Define a custom unit 'photoelectron'
ureg.define("event = [Int64]")  # Define a custom unit 'events'
ureg.define("sqrt_hertz = Hz**0.5")
ureg.define("bit_bins = ![Int64]")


dB = ureg.dB
pascal = ureg.pascal
minute = ureg.minute
dimensionless = ureg.dimensionless
bit_bins = ureg.bit_bins
sqrt_hertz = ureg.sqrt_hertz
photoelectron = ureg.photoelectron
event = ureg.event

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
        # Use pint's dimensionality check; accepts strings like "energy"
        return obj.check(expected)

class BaseUnit(metaclass=UnitMeta):
    _expected_dim: str | None = None

    @classmethod
    def check(cls, value):
        assert isinstance(value, Quantity), f"Expected a pint Quantity instance, got {type(value)}"
        assert value.check(cls._expected_dim), f"Value units {value.dimensionality} do not match {cls.__name__} units"
        return value


class Energy(BaseUnit):
    """Quantity specifically for energy units."""
    _expected_dim = "joule"

class Time(BaseUnit):
    """Quantity specifically for time units."""
    _expected_dim = "second"

class Power(BaseUnit):
    """Quantity specifically for power units."""
    _expected_dim = "watt"

class Voltage(BaseUnit):
    """Quantity specifically for voltage units."""
    _expected_dim = "volt"

class Current(BaseUnit):
    """Quantity specifically for current units."""
    _expected_dim = "ampere"

class Resistance(BaseUnit):
    """Quantity specifically for resistance units."""
    _expected_dim = "ohm"

class Temperature(BaseUnit):
    """Quantity specifically for temperature units."""
    _expected_dim = "kelvin"

class Length(BaseUnit):
    """Quantity specifically for length units."""
    _expected_dim = "meter"

class Volume(BaseUnit):
    """Quantity specifically for volume units."""
    _expected_dim = "liter"

class FlowRate(BaseUnit):
    """Quantity specifically for flow rate units."""
    _expected_dim = "liter / time"

class Frequency(BaseUnit):
    """Quantity specifically for frequency units."""
    _expected_dim = "hertz"

class Angle(BaseUnit):
    """Quantity specifically for angle units."""
    _expected_dim = "degree"

class RefractiveIndex(BaseUnit):
    """Quantity specifically for refractive index units."""
    _expected_dim = "refractive_index_units"

class Dimensionless(BaseUnit):
    """Quantity specifically for dimensionless units."""
    _expected_dim = ""

from typing import get_type_hints

def validate(function):
    def wrapper(*args, **kwargs):
        hints = get_type_hints(function)

        for arg, hint in zip(args, hints.values()):
            if isinstance(hint, BaseUnit):
                hint.check(arg)

        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in hints:
                hint = hints[kwarg_name]
                if issubclass(hint, BaseUnit):
                    hint.check(kwarg_value)

        return function(*args, **kwargs)
    return wrapper

