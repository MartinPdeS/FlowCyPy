import numpy as np
import pytest
from FlowCyPy import FlowCytometer, Detector, ScattererDistribution, Source, FlowCell
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.population import Population
from FlowCyPy.units import (
    refractive_index_unit,
    degree,
    watt,
    hertz,
    volt,
    meter,
    second,
    micrometer,
    particle,
    liter,
    milliliter
)


@pytest.fixture
def default_detector():
    return Detector(
        name='default',
        NA=1,
        phi_angle=90 * degree,
        responsitivity=1 * volt / watt,
        acquisition_frequency=1e5 * hertz,
        noise_level=0 * volt,
        saturation_level=1_000 * volt,
        baseline_shift=0.0 * volt,
        n_bins='12bit',
    )

@pytest.fixture
def flow():
    return FlowCell(
        flow_speed=0.2 * meter / second,
        flow_area=1e-6 * meter * meter,
        total_time=1e-3 * second,
    )


@pytest.fixture
def default_size_distribution():
    return NormalDistribution(
        mean=1.0 * micrometer,
        std_dev=0.1 * micrometer
    )

@pytest.fixture
def default_ri_distribution():
    return NormalDistribution(
        mean=1.0 * refractive_index_unit,
        std_dev=0.1 * refractive_index_unit
    )

@pytest.fixture
def default_population(default_size_distribution, default_ri_distribution):
    return Population(
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        concentration=1.8e5 * particle / milliliter,
        name="Default population"
    )


@pytest.fixture
def default_scatterer_distribution(flow, default_population):
    return  ScattererDistribution(
        flow=flow,
        populations=[default_population]
    )


@pytest.fixture
def default_source():
    return Source(
        NA=1,
        wavelength=1550e-9 * meter,
        optical_power=1e-3 * watt,
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