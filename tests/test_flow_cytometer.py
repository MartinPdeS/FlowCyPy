import numpy as np
import pytest
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy import units


@pytest.fixture
def default_digitizer():
    return SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_freq=5e6 * units.hertz,
    )

@pytest.fixture
def default_detector_0():
    return Detector(
        name='default',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,
    )


@pytest.fixture
def default_detector_1():
    return Detector(
        name='default_bis',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,
        baseline_shift=0.0 * units.volt,
    )


@pytest.fixture
def flow_cell():
    source = GaussianBeam(
        numerical_aperture=1 * units.AU,
        wavelength=1550 * units.nanometer,
        optical_power=100e-3 * units.watt,
    )

    return FlowCell(
        source=source,
        volume_flow=0.1 * units.microliter / units.second,
        flow_area=(12 * units.micrometer) ** 2,
        event_scheme='uniform-sequential'
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
        particle_count=1e+9 * units.particle / units.milliliter,
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_scatterer(default_population):
    scatterer = ScattererCollection()
    scatterer.add_population(default_population)
    return scatterer


def test_flow_cytometer_simulation(default_detector_0, default_detector_1, default_scatterer, flow_cell, default_digitizer):
    """Test the simulation of flow cytometer signals."""
    cytometer = FlowCytometer(
        signal_digitizer=default_digitizer,
        scatterer_collection=default_scatterer,
        detectors=[default_detector_0, default_detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

    experiment = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    # Check that the signals are not all zeros (pulses should add non-zero values)
    assert not np.all(experiment.data.continuous.Signal == 0 * units.volt), "FSC signal is all zeros."
    assert not np.all(experiment.data.continuous.Signal == 0 * units.volt), "SSC signal is all zeros."

    # Check that the noise has been added to the signal
    assert np.std(experiment.data.continuous.Signal) > 0 * units.volt, "FSC signal variance is zero, indicating no noise added."
    assert np.std(experiment.data.continuous.Signal) > 0 * units.volt, "SSC signal variance is zero, indicating no noise added."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, default_detector_0, default_detector_1, default_scatterer, flow_cell, default_digitizer):
    """Test the plotting of flow cytometer signals."""
    cytometer = FlowCytometer(
        signal_digitizer=default_digitizer,
        scatterer_collection=default_scatterer,
        detectors=[default_detector_0, default_detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='uniform'
    )

    acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    acquisition.plot.signals()

    plt.close()

    acquisition.logger.scatterer()

    acquisition.run_triggering(
        threshold=3.0 * units.volt,
        trigger_detector_name='default',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    acquisition.plot.trigger()

    plt.close()

    acquisition.plot.peaks(
        x_detector='default',
        y_detector='default_bis'
    )


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
