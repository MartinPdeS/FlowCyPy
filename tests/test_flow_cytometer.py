import numpy as np
import pytest
from FlowCyPy import FlowCytometer, Detector, Scatterer, GaussianBeam, FlowCell
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import distribution
from FlowCyPy.population import Population

from FlowCyPy.units import (
    RIU,
    degree,
    watt,
    hertz,
    volt,
    meter,
    second,
    micrometer,
    particle,
    nanometer,
    millivolt,
    milliliter,
    ampere,
    AU
)


@pytest.fixture
def default_detector_0():
    return Detector(
        name='default',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,
        sampling_freq=1e5 * hertz,
    )


@pytest.fixture
def default_detector_1():
    return Detector(
        name='default_bis',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,
        sampling_freq=1e5 * hertz,
        noise_level=0 * volt,
        saturation_level=1 * millivolt,
        baseline_shift=0.0 * volt,
        n_bins='12bit',
    )


@pytest.fixture
def flow_cell():
    return FlowCell(
        flow_speed=0.2 * meter / second,
        flow_area=(1e-6 * meter * meter),
        run_time=1e-3 * second,
    )


@pytest.fixture
def default_size_distribution():
    return distribution.Normal(
        mean=1.0 * micrometer,
        std_dev=0.1 * micrometer
    )


@pytest.fixture
def default_ri_distribution():
    return distribution.Normal(
        mean=1.0 * RIU,
        std_dev=0.1 * RIU
    )


@pytest.fixture
def default_population(default_size_distribution, default_ri_distribution):
    return Population(
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_scatterer(flow_cell, default_population):
    scatterer = Scatterer()
    scatterer.add_population(default_population, particle_count=1.8e+5 * particle / milliliter)
    scatterer.initialize(flow_cell=flow_cell)
    return scatterer


@pytest.fixture
def default_source():
    return GaussianBeam(
        numerical_aperture=1 * AU,
        wavelength=1550 * nanometer,
        optical_power=100e-3 * watt,
    )


def test_flow_cytometer_simulation(default_source, default_detector_0, default_detector_1, default_scatterer):
    """Test the simulation of flow cytometer signals."""
    cytometer = FlowCytometer(
        source=default_source,
        detectors=[default_detector_0, default_detector_1],
        scatterer=default_scatterer,
        coupling_mechanism='mie'
    )
    cytometer.simulate_pulse()

    # Check that the signals are not all zeros (pulses should add non-zero values)
    assert not np.all(default_detector_0.dataframe.Signal == 0 * volt), "FSC signal is all zeros."
    assert not np.all(default_detector_0.dataframe.Signal == 0 * volt), "SSC signal is all zeros."

    # Check that the noise has been added to the signal
    assert np.std(default_detector_1.dataframe.Signal) > 0 * volt, "FSC signal variance is zero, indicating no noise added."
    assert np.std(default_detector_1.dataframe.Signal) > 0 * volt, "SSC signal variance is zero, indicating no noise added."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, default_source, default_detector_0, default_detector_1, default_scatterer):
    """Test the plotting of flow cytometer signals."""
    cytometer = FlowCytometer(
        source=default_source,
        detectors=[default_detector_0, default_detector_1],
        scatterer=default_scatterer,
        coupling_mechanism='uniform'
    )
    cytometer.simulate_pulse()

    cytometer.plot()

    plt.close()

    cytometer._log_statistics()


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
