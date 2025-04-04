import pytest




from FlowCyPy.binary.interface_core import FlowCyPySim
from FlowCyPy.binary.interface_peak_locator import SlidingWindowPeakLocator, GlobalPeakLocator
from PyMieSim.binary.interface_source import BindedPlanewave

from PyMieSim.experiment.utils import config_dict, Sequential
from FlowCyPy import units
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





# ----------------- FIXTURES -----------------


@pytest.fixture
def amplifier():
    return TransimpedanceAmplifier(
        gain=100 * units.volt / units.ampere,
        bandwidth=10 * units.megahertz
    )

@pytest.fixture
def default_digitizer():
    """Fixture for creating a default signal digitizer."""
    return SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=5e6 * units.hertz,
    )

@pytest.fixture
def detector_0():
    """Fixture for creating the first default detector."""
    return Detector(
        name='default',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def detector_1():
    """Fixture for creating the second default detector."""
    return Detector(
        name='default_bis',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def source():
    return GaussianBeam(
        numerical_aperture=0.1 * units.AU,
        wavelength=1550 * units.nanometer,
        optical_power=100e-3 * units.watt,
    )

@pytest.fixture
def flow_cell():
    """Fixture for creating a default flow cell."""

    return FlowCell(
        sample_volume_flow=1 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=10 * units.micrometer,
        height=6 * units.micrometer,
    )

@pytest.fixture
def diameter_distribution():
    """Fixture for creating a normal size distribution."""
    return distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer
    )

@pytest.fixture
def ri_distribution():
    """Fixture for creating a normal refractive index distribution."""
    return distribution.Normal(
        mean=1.5 * units.RIU,
        std_dev=0.1 * units.RIU
    )

@pytest.fixture
def population(diameter_distribution, ri_distribution):
    """Fixture for creating a default population."""
    return Sphere(
        particle_count=110 * units.particle,
        diameter=diameter_distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

@pytest.fixture
def scatterer_collection(population):
    """Fixture for creating a scatterer collection with a default population."""
    scatterer = ScattererCollection()
    scatterer.add_population(population)
    return scatterer

@pytest.fixture
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, source, amplifier, default_digitizer):
    """Fixture for creating a default Flow Cytometer."""
    return FlowCytometer(
        source=source,
        transimpedance_amplifier=amplifier,
        signal_digitizer=default_digitizer,
        scatterer_collection=scatterer_collection,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

# ----------------- UNIT TESTS -----------------




def test_flow_cytometer_acquisition():
    a = numpy.linspace(0, 1)
    core = FlowCyPySim(a, a, a, a, 2)

def test_basic():
    sphere = BindedPlanewave(1, [0, 1], 1)




def test_basic():
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
