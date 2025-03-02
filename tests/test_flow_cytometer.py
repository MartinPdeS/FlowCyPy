import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import FlowCytometer, Detector, ScattererCollection, GaussianBeam, FlowCell
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy import units
from FlowCyPy import peak_locator

# ----------------- FIXTURES -----------------

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
        responsitivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def detector_1():
    """Fixture for creating the second default detector."""
    return Detector(
        name='default_bis',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,
    )

@pytest.fixture
def flow_cell():
    """Fixture for creating a default flow cell."""
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
def size_distribution():
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
def population(size_distribution, ri_distribution):
    """Fixture for creating a default population."""
    return Population(
        particle_count=110 * units.particle,
        size=size_distribution,
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
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, default_digitizer):
    """Fixture for creating a default Flow Cytometer."""
    return FlowCytometer(
        signal_digitizer=default_digitizer,
        scatterer_collection=scatterer_collection,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
        coupling_mechanism='mie'
    )

# ----------------- UNIT TESTS -----------------

def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    signal = acquisition.analog['Signal']

    assert not np.all(signal == 0 * units.volt), "Acquisition signal is all zeros."
    assert np.std(signal) > 0 * units.volt, "Acquisition signal variance is zero, indicating no noise added."


def test_flow_cytometer_multiple_detectors(flow_cytometer):
    """Ensure that both detectors generate non-zero signals."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    signal_0 = acquisition.analog['Signal']
    signal_1 = acquisition.analog['Signal']

    assert not np.all(signal_0 == 0 * units.volt), "Detector 0 signal is all zeros."
    assert not np.all(signal_1 == 0 * units.volt), "Detector 1 signal is all zeros."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, flow_cytometer):
    """Test if the flow cytometer plots without error."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    acquisition.analog.plot()
    acquisition.analog.log()
    plt.close()

    acquisition.digital.plot()
    acquisition.digital.log()
    plt.close()

    acquisition.scatterer.log()


def test_flow_cytometer_triggered_acquisition(flow_cytometer):
    """Test triggered acquisition with a defined threshold."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    triggered_acquisition = acquisition.run_triggering(
        threshold=3.0 * units.millivolt,
        trigger_detector_name='default',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    assert triggered_acquisition is not None, "Triggered acquisition failed to return results."
    assert len(triggered_acquisition.analog) > 0, "Triggered acquisition has no signal data."


def test_flow_cytometer_signal_processing(flow_cytometer):
    """Test filtering and baseline restoration on the acquired signal."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    triggered_acquisition = acquisition.run_triggering(
        threshold=3.0 * units.millivolt,
        trigger_detector_name='default',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    # Apply filtering
    triggered_acquisition.apply_filters(
        lowpass_cutoff=1.5 * units.megahertz,
        highpass_cutoff=0.01 * units.kilohertz
    )

    # Apply baseline restoration
    triggered_acquisition.apply_baseline_restauration()

    assert np.std(triggered_acquisition.analog['Signal']) > 0, "Filtered signal has zero variance."


def test_peak_detection(flow_cytometer):
    """Ensure peak detection works correctly on the triggered acquisition."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    triggered_acquisition = acquisition.run_triggering(
        threshold=3.0 * units.millivolt,
        trigger_detector_name='default',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    algorithm = peak_locator.BasicPeakLocator()

    peaks = triggered_acquisition.detect_peaks(algorithm)

    assert len(peaks) > 0, "No peaks detected when they were expected."


@patch('matplotlib.pyplot.show')
def test_peak_plot(mock_show, flow_cytometer):
    """Ensure peak plots render correctly."""
    acquisition = flow_cytometer.get_acquisition(run_time=0.2 * units.millisecond)

    triggered_acquisition = acquisition.run_triggering(
        threshold=3.0 * units.millivolt,
        trigger_detector_name='default',
        max_triggers=35,
        pre_buffer=64,
        post_buffer=64
    )

    algorithm = peak_locator.BasicPeakLocator()

    peaks = triggered_acquisition.detect_peaks(algorithm)

    peaks.plot(x_detector='default', y_detector='default_bis')
    plt.close()



if __name__ == '__main__':
    pytest.main(["-W error", __file__])
