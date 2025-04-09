# Initialize a unit registry
from PyMieSim.units import ureg, Quantity # noqa F401
from PyMieSim.units import *  # noqa F401
from numpy import sqrt

_scaled_units_str_list = [
    'watt', 'volt', 'meter', 'second', 'liter', 'hertz', 'ohm', 'ampere'
]

for _units_str in _scaled_units_str_list:
    for scale in ['femto', 'pico', 'nano', 'micro', 'milli', '', 'kilo', 'mega']:
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
pascal = ureg.pascal
minute = ureg.minute


# Define a custom unit 'bit_bins'
ureg.define("bit_bins = ![detector_resolution]")
bit_bins = ureg.bit_bins

ureg.define("sqrt_hertz = Hz**0.5")
sqrt_hertz = ureg.sqrt_hertz