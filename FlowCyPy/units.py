from pint import UnitRegistry

# Initialize a unit registry
ureg = UnitRegistry(system='mks')
Quantity = ureg.Quantity



watt = ureg.watt

particle = ureg.particle
hertz = ureg.hertz
volt = ureg.volt
refractive_index_unit = ureg.refractive_index_unit
degree = ureg.degree

meter = ureg.meter
millimeter = ureg.millimeter
micrometer = ureg.micrometer
nanometer = ureg.nanometer

second = ureg.second
millisecond = ureg.millisecond
microsecond = ureg.microsecond

liter = ureg.liter
milliliter = ureg.milliliter
