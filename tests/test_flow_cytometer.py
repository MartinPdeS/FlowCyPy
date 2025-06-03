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
from FlowCyPy.triggering_system import TriggeringSystem, Scheme
# ----------------- FIXTURES -----------------


@pytest.fixture
def amplifier():
    return TransimpedanceAmplifier(
        gain=100 * units.volt / units.ampere,
        bandwidth=10 * units.megahertz
    )

@pytest.fixture
def digitizer():
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
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, source, amplifier, digitizer):
    """Fixture for creating a default Flow Cytometer."""
    return FlowCytometer(
        source=source,
        transimpedance_amplifier=amplifier,
        digitizer=digitizer,
        scatterer_collection=scatterer_collection,
        detectors=[detector_0, detector_1],
        flow_cell=flow_cell,
    )

# ----------------- UNIT TESTS -----------------


def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    flow_cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    signal = acquisition['default']

    assert not np.all(signal == 0 * units.volt), "Acquisition signal is all zeros."
    assert np.std(signal) > 0 * units.volt, "Acquisition signal variance is zero, indicating no noise added."


def test_flow_cytometer_multiple_detectors(flow_cytometer):
    """Ensure that both detectors generate non-zero signals."""
    flow_cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    signal_0 = acquisition['default']
    signal_1 = acquisition['default']

    assert not np.all(signal_0 == 0 * units.volt), "Detector 0 signal is all zeros."
    assert not np.all(signal_1 == 0 * units.volt), "Detector 1 signal is all zeros."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, flow_cytometer, digitizer):
    """Test if the flow cytometer plots without error."""
    flow_cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    acquisition.plot()
    plt.close()

    acquisition.digitalize(digitizer=digitizer).plot()
    plt.close()


def test_flow_cytometer_triggered_acquisition(flow_cytometer):
    """Test triggered acquisition with a defined threshold."""
    flow_cytometer.prepare_acquisition(run_time=2 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    trigger = TriggeringSystem(
        dataframe=acquisition,
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        digitizer=digitizer
    )

    triggered_acquisition = trigger.run(
        scheme=Scheme.FIXED,
        threshold='3 sigma',
    )

    assert triggered_acquisition is not None, "Triggered acquisition failed to return results."
    assert len(triggered_acquisition) > 0, "Triggered acquisition has no signal data."


def test_flow_cytometer_signal_processing(flow_cytometer):
    """Test filtering and baseline restoration on the acquired signal."""
    flow_cytometer.prepare_acquisition(run_time=2.0 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()

    trigger = TriggeringSystem(
        dataframe=acquisition,
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        digitizer=digitizer
    )

    triggered_acquisition = trigger.run(
        scheme=Scheme.FIXED,
        threshold='3 sigma',
    )

    assert np.std(triggered_acquisition['default']) > 0, "Filtered signal has zero variance."


def test_peak_detection(flow_cytometer, digitizer):
    """Ensure peak detection works correctly on the triggered acquisition."""
    flow_cytometer.prepare_acquisition(run_time=2.0 * units.millisecond)

    processing_steps = [
        circuits.BaselineRestorator(window_size=1000 * units.microsecond),
        circuits.BesselLowPass(cutoff=1 * units.megahertz, order=4, gain=2)
    ]

    acquisition = flow_cytometer.get_acquisition(processing_steps=processing_steps)

    trigger = TriggeringSystem(
        dataframe=acquisition,
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        digitizer=digitizer
    )

    triggered_acquisition = trigger.run(
        scheme=Scheme.FIXED,
        threshold='3 sigma',
    )

    algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    peaks = algorithm.run(digital_signal)

    assert len(peaks) > 0, "No peaks detected when they were expected."


@patch('matplotlib.pyplot.show')
def test_peak_plot(mock_show, flow_cytometer, digitizer):
    """Ensure peak plots render correctly."""
    flow_cytometer.prepare_acquisition(run_time=2.0 * units.millisecond)
    acquisition = flow_cytometer.get_acquisition()
    acquisition.plot()

    trigger = TriggeringSystem(
        dataframe=acquisition,
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        digitizer=digitizer
    )

    triggered_acquisition = trigger.run(
        scheme=Scheme.FIXED,
        threshold='3 sigma',
    )
    algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    peaks = algorithm.run(digital_signal)

    peaks.plot(
        x=('default', 'Height'),
        y=('default_bis', 'Height')
    )
    plt.close()


if __name__ == '__main__':
    pytest.main(["-W error", "-s", __file__])
