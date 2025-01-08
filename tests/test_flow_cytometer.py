import numpy as np
import pytest
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
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
    millisecond,
    milliliter,
    ampere,
    AU
)


@pytest.fixture
def default_detector_0():
    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_freq=1e5 * hertz
    )

    return Detector(
        name='default',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,
        signal_digitizer=signal_digitizer
    )


@pytest.fixture
def default_detector_1():
    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_freq=1e5 * hertz,
    )

    return Detector(
        name='default_bis',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,
        baseline_shift=0.0 * volt,
        signal_digitizer=signal_digitizer
    )


@pytest.fixture
def flow_cell():
    source = GaussianBeam(
        numerical_aperture=1 * AU,
        wavelength=1550 * nanometer,
        optical_power=100e-3 * watt,
    )

    return FlowCell(
        source=source,
        flow_speed=0.2 * meter / second,
        flow_area=(1e-6 * meter * meter),
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
        particle_count=1.8e+5 * particle / milliliter,
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_scatterer(flow_cell, default_population):
    scatterer = ScattererCollection()
    scatterer.add_population(default_population)
    return scatterer


def test_flow_cytometer_simulation(default_detector_0, default_detector_1, default_scatterer, flow_cell):
    """Test the simulation of flow cytometer signals."""
    cytometer = FlowCytometer(
        scatterer_collection=default_scatterer,
        detectors=[default_detector_0, default_detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

    experiment = cytometer.get_continous_acquisition(run_time=0.2 * millisecond)

    # Check that the signals are not all zeros (pulses should add non-zero values)
    assert not np.all(experiment.detector_dataframe.Signal == 0 * volt), "FSC signal is all zeros."
    assert not np.all(experiment.detector_dataframe.Signal == 0 * volt), "SSC signal is all zeros."

    # Check that the noise has been added to the signal
    assert np.std(experiment.detector_dataframe.Signal) > 0 * volt, "FSC signal variance is zero, indicating no noise added."
    assert np.std(experiment.detector_dataframe.Signal) > 0 * volt, "SSC signal variance is zero, indicating no noise added."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, default_detector_0, default_detector_1, default_scatterer, flow_cell):
    """Test the plotting of flow cytometer signals."""
    cytometer = FlowCytometer(
        scatterer_collection=default_scatterer,
        detectors=[default_detector_0, default_detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='uniform'
    )

    experiment = cytometer.get_continous_acquisition(run_time=0.2 * millisecond)

    experiment.plot.signals()

    plt.close()

    experiment.logger.scatterer()


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
