# Initialize a unit registry
from PyMieSim.units import ureg, Quantity # noqa F401
from PyMieSim.units import *  # noqa F401

_scaled_units_str_list = [
    'watt', 'volt', 'meter', 'second', 'liter', 'hertz', 'ohm', 'ampere'
]

for _units_str in _scaled_units_str_list:
    for scale in ['nano', 'micro', 'milli', '', 'kilo', 'mega']:
        _unit = scale + _units_str
        globals()[_unit] = getattr(ureg, _unit)


joule = ureg.joule
coulomb = ureg.coulomb
power = ureg.watt.dimensionality
kelvin = ureg.kelvin
celsius = ureg.celsius
particle = ureg.particle
degree = ureg.degree
distance = ureg.meter.dimensionality
time = ureg.second.dimensionality
volume = ureg.liter.dimensionality
frequency = ureg.hertz.dimensionality
dB = ureg.dB
