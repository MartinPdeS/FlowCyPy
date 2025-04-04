import pytest



# from PyMieSim.units import ureg, Quantity # noqa F401
# from PyMieSim.units import *  # noqa F401
# from numpy import sqrt

# _scaled_units_str_list = [
#     'watt', 'volt', 'meter', 'second', 'liter', 'hertz', 'ohm', 'ampere'
# ]

# for _units_str in _scaled_units_str_list:
#     for scale in ['femto', 'pico', 'nano', 'micro', 'milli', '', 'kilo', 'mega']:
#         _unit = scale + _units_str
#         globals()[_unit] = getattr(ureg, _unit)


# joule = ureg.joule
# coulomb = ureg.coulomb
# power = ureg.watt.dimensionality
# kelvin = ureg.kelvin
# celsius = ureg.celsius
# particle = ureg.particle
# degree = ureg.degree
# distance = ureg.meter.dimensionality
# time = ureg.second.dimensionality
# volume = ureg.liter.dimensionality
# frequency = ureg.hertz.dimensionality
# dB = ureg.dB
# pascal = ureg.pascal
# minute = ureg.minute


# # Define a custom unit 'bit_bins'
# ureg.define("bit_bins = ![detector_resolution]")
# bit_bins = ureg.bit_bins

# ureg.define("sqrt_hertz = Hz**0.5")
# sqrt_hertz = ureg.sqrt_hertz


from FlowCyPy import units






from PyMieSim import experiment as _PyMieSim
import numpy
# from FlowCyPy import units

def test_basic():


    pms_source = _PyMieSim.source.PlaneWave.build_sequential(
        total_size=10,
        wavelength=500 * units.nanometer,
        polarization=0 * units.degree,
        amplitude=1 * units.volt / units.meter
    )

    pms_scatterer = _PyMieSim.scatterer.Sphere.build_sequential(
        total_size=10,
        diameter=1 * units.nanometer,
        property=1.5 * units.RIU,
        medium_property=1.0 * units.RIU,
        source=pms_source
    )

    pms_detector = _PyMieSim.detector.Photodiode.build_sequential(
        total_size=10,
        mode_number='NC00',
        NA=0.2 * units.AU,
        cache_NA=0.0 * units.AU,
        gamma_offset=0.0 * units.degree,
        phi_offset=0.0 * units.degree,
        polarization_filter=numpy.nan * units.degree,
        sampling=200 * units.AU,
        rotation=0 * units.degree
    )


    experiment = _PyMieSim.Setup(source=pms_source, scatterer=pms_scatterer, detector=pms_detector)

    coupling_value = experiment.get_sequential('coupling')


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
