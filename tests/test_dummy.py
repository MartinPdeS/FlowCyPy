import pytest



from PyMieSim import experiment as _PyMieSim
from FlowCyPy.binary.interface_core import FlowCyPySim

from PyMieSim import units
import numpy

def test_0():
    a = numpy.linspace(0, 1)
    core = FlowCyPySim(a, a, a, a, 2)




def test_1():
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
