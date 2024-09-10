import numpy as np
import pytest
from FlowCyPy import FlowCytometer, Detector, ScattererDistribution, Source, FlowCell
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy.distribution import NormalDistribution


@pytest.fixture
def default_detector():
    return Detector(
        name='default',
        NA=1,
        phi_angle=90,
        responsitivity=1,
        acquisition_frequency=1e3,
        noise_level=0,
        saturation_level=1_000,
        baseline_shift=0.0,
        n_bins=100,
    )

@pytest.fixture
def flow():
    return  FlowCell(
        flow_speed=80e-6,
        flow_area=1e-6,
        total_time=1.0,
        scatterer_density=1e11
    )


@pytest.fixture
def default_distribution():
    return NormalDistribution(
        mean=1e-6,
        std_dev=1e-7
    )

@pytest.fixture
def default_scatterer_distribution(flow, default_distribution):
    return  ScattererDistribution(
        flow=flow,
        refractive_index=[1.5],
        size=[default_distribution],
    )


@pytest.fixture
def default_source():
    return Source(
        NA=1,
        wavelength=1550e-9,
        optical_power=1e-3,
    )

def test_flow_cytometer_simulation(default_source, default_detector, default_scatterer_distribution):
    """Test the simulation of flow cytometer signals."""
    cytometer = FlowCytometer(
        source=default_source,
        detectors=[default_detector],
        scatterer_distribution=default_scatterer_distribution,
        coupling_mechanism='rayleigh'
    )
    cytometer.simulate_pulse()

    # Check that the signals are not all zeros (pulses should add non-zero values)
    assert np.any(default_detector.signal > 0), "FSC signal is all zeros."
    assert np.any(default_detector.signal > 0), "SSC signal is all zeros."

    # Check that the noise has been added to the signal
    assert np.var(default_detector.signal) > 0, "FSC signal variance is zero, indicating no noise added."
    assert np.var(default_detector.signal) > 0, "SSC signal variance is zero, indicating no noise added."

@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, default_source, default_detector, default_scatterer_distribution):
    """Test the plotting of flow cytometer signals."""
    cytometer = FlowCytometer(
        source=default_source,
        detectors=[default_detector],
        scatterer_distribution=default_scatterer_distribution,
        coupling_mechanism='uniform'
    )
    cytometer.simulate_pulse()

    cytometer.plot()

    plt.close()

    cytometer.print_properties()

if __name__ == '__main__':
    pytest.main([__file__])