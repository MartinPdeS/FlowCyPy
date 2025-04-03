from PyMieSim import experiment
import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, TransimpedanceAmplifier
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import distribution
from FlowCyPy.population import Sphere
from FlowCyPy import units
from FlowCyPy import peak_locator
from FlowCyPy import circuits


def test_before_hand_1():
    SIZE = 4
    source = experiment.source.PlaneWave.build_sequential(
        total_size=SIZE,
        polarization=0 * units.degree,
        amplitude = 1 * units.volt / units.meter,
        wavelength=500 * units.nanometer
    )

    sphere = experiment.scatterer.Sphere.build_sequential(
        total_size=SIZE,
        source=source,
        diameter=[100, 200, 300, 400] * units.nanometer,
        property=1.44 * units.RIU,
        medium_property=1.1 * units.RIU
    )

    detector = experiment.detector.Photodiode(
        NA=[0.2, 0.2, 0.2, 0.2] * units.AU,
        phi_offset=[0, 0, 0, 0] * units.degree,
        gamma_offset=[0, 0, 0, 0] * units.degree,
        cache_NA=[0, 0, 0, 0] * units.AU,
        sampling=[100, 100, 100, 100] * units.AU,
        mode_number=['NC00', 'NC00', 'NC00', 'NC00'],
        polarization_filter=[np.nan, np.nan, np.nan, np.nan] * units.degree,
        rotation=[0, 0, 0, 0] * units.degree
    )

    setup = experiment.Setup(
        source=source,
        scatterer=sphere,
        detector=detector
    )

    setup.get_sequential('coupling')




if __name__ == '__main__':
    pytest.main(["-W error", __file__])
