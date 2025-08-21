from PyMieSim.units import ureg, Quantity


class BaseUnit():
    @staticmethod
    def check(value):
        assert isinstance(value, Quantity), f"Expected a pint Quantity instance, got {type(value)}"


class Energy(BaseUnit):
    """Quantity specifically for energy units."""
    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.dimensionality == ureg.joule.dimensionality, f"Value units {value.dimensionality} do not match energy units"

class Time(BaseUnit):
    """Quantity specifically for time units."""
    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.dimensionality == ureg.second.dimensionality, f"Value units {value.dimensionality} do not match time units"

class Power(BaseUnit):
    """Quantity specifically for power units."""
    @staticmethod
    def check(value):
        BaseUnit.check(value)
        assert value.dimensionality == ureg.watt.dimensionality, f"Value units {value.dimensionality} do not match power units"




def calculate_power(energy: Energy, time: Time) -> Power:
    """Calculate power from energy and time."""
    Energy.check(energy)
    Time.check(time)

    result = (energy / time).to(ureg.watt)
    return result

# Usage
energy = 100 * ureg.joule
time = 10 * ureg.second
power = calculate_power(energy, time)
print(f"Power: {power}")