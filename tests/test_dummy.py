import pytest




from FlowCyPy.binary.interface_core import FlowCyPySim
from FlowCyPy.binary.interface_peak_locator import SlidingWindowPeakLocator, GlobalPeakLocator
from PyMieSim.binary.interface_source import BindedPlanewave

# from PyMieSim.experiment.utils import config_dict, Sequential
from PyMieSim import units
import numpy

# import numpy as np
# import pytest
# import matplotlib.pyplot as plt
# from unittest.mock import patch
# from FlowCyPy.cytometer import FlowCytometer#, Detector, ScattererCollection, GaussianBeam, TransimpedanceAmplifier, SignalDigitizer
# from FlowCyPy.flow_cell import FlowCell
# from FlowCyPy.signal_digitizer import SignalDigitizer
# from FlowCyPy import distribution
# from FlowCyPy.population import Sphere
# from FlowCyPy import units
# from FlowCyPy import peak_locator
# from FlowCyPy import circuits





def test_flow_cytometer_acquisition():
    a = numpy.linspace(0, 1)
    core = FlowCyPySim(a, a, a, a, 2)

def test_basic():
    sphere = BindedPlanewave(1, [0, 1], 1)




def test_basic_1():
    from PyMieSim import experiment as _PyMieSim

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
