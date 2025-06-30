# Initialize a unit registry
from PyMieSim.units import ureg, Quantity # noqa F401
from PyMieSim.units import *  # noqa F401

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

dimensionless = ureg.dimensionless


# Define a custom unit 'bit_bins'
ureg.define("bit_bins = ![Int64]")
bit_bins = ureg.bit_bins

ureg.define("sqrt_hertz = Hz**0.5")
sqrt_hertz = ureg.sqrt_hertz


ureg.define("photoelectron = [Float64]")  # Define a custom unit 'photoelectron'
ureg.define("event = [Int64]")  # Define a custom unit 'events'

photoelectron = ureg.photoelectron
event = ureg.event