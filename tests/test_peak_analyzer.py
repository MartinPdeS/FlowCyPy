import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch

# Importing from FlowCyPy
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, peak_locator, distribution
from FlowCyPy import units
from FlowCyPy.population import Population
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.utils import generate_dummy_detector

# Seed for reproducibility
np.random.seed(10)


# Fixtures
@pytest.fixture
def flow_cell():
    source = GaussianBeam(
        numerical_aperture=1 * units.AU,
        wavelength=1550e-9 * units.meter,
        optical_power=1e-3 * units.watt,
    )

    return FlowCell(
        source=source,
        volume_flow=10 * units.microliter / units.second,
        flow_area=1e-6 * units.meter * units.meter,
    )


@pytest.fixture
def default_size_distribution():
    return distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer
    )


@pytest.fixture
def default_ri_distribution():
    return distribution.Normal(
        mean=1.0 * units.RIU,
        std_dev=0.1 * units.RIU
    )


@pytest.fixture
def default_population(default_size_distribution, default_ri_distribution):
    return Population(
        particle_count=3e+5 * units.particle / units.milliliter,
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_scatterer(flow_cell, default_population):
    scatterer = ScattererCollection()

    scatterer.add_population(default_population)

    return scatterer

@pytest.fixture
def default_digitizer():
    """Creates a default detector with common properties."""
    def create_detector(name):
        return SignalDigitizer(
            bit_depth=1024,
            saturation_levels='auto',
            sampling_freq=1e5 * units.hertz,
        )

@pytest.fixture
def default_detector():
    """Creates a default detector with common properties."""
    def create_detector(name):
        return Detector(
            name=name,
            numerical_aperture=1 * units.AU,
            phi_angle=0 * units.degree,
            responsitivity=1 * units.ampere / units.watt,
            baseline_shift=0.0 * units.volt,
        )
    return create_detector


@pytest.fixture
def default_cytometer(default_scatterer, default_detector, flow_cell, default_digitizer):
    """Fixture for a default cytometer with two detectors."""

    detectors = [default_detector('0'), default_detector('1')]

    cytometer = FlowCytometer(
        signal_digitizer=default_digitizer,
        scatterer_collection=default_scatterer,
        detectors=detectors,
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

    return cytometer


# Algorithm setup
algorithm = peak_locator.MovingAverage(
    threshold=0.001 * units.volt,
    window_size=0.8 * units.second,
)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
