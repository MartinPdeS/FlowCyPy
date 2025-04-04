# import pytest

# def test_before_hand():
#     import numpy
#     from FlowCyPy.binary.interface_core import FlowCyPySim

#     a = numpy.linspace(0, 1)

#     FlowCyPySim(a, a, a, a, 2)


# if __name__ == '__main__':
#     pytest.main(["-W error", __file__])

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

def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    flow_cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()



if __name__ == '__main__':
    pytest.main(["-W error", __file__])
