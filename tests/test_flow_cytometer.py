import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch
from FlowCyPy import FlowCytometer
from FlowCyPy.opto_electronics import OptoElectronics, Detector, source, TransimpedanceAmplifier
from FlowCyPy.fluidics import Fluidics, FlowCell, ScattererCollection, distribution, population
from FlowCyPy.signal_processing import SignalProcessing, Digitizer, triggering_system, circuits, peak_locator
from FlowCyPy import units
import FlowCyPy
FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging


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
    return Digitizer(
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
def flow_cell():
    """Fixture for creating a default flow cell."""
    return FlowCell(
        sample_volume_flow=1 * units.microliter / units.second,
        sheath_volume_flow=6 * units.microliter / units.second,
        width=10 * units.micrometer,
        height=6 * units.micrometer,
    )

@pytest.fixture
def scatterer_collection():
    """Fixture for creating a scatterer collection with a default population."""
    scatterer = ScattererCollection()

    diameter_distribution = distribution.Normal(
        mean=1.0 * units.micrometer,
        std_dev=0.1 * units.micrometer
    )

    ri_distribution = distribution.Normal(
        mean=1.5 * units.RIU,
        std_dev=0.1 * units.RIU
    )

    _population = population.Sphere(
        particle_count=110 * units.particle,
        diameter=diameter_distribution,
        refractive_index=ri_distribution,
        name="Default population"
    )

    scatterer.add_population(_population)
    return scatterer

@pytest.fixture
def flow_cytometer(detector_0, detector_1, scatterer_collection, flow_cell, amplifier, digitizer):
    """Fixture for creating a default Flow Cytometer."""

    beam = source.GaussianBeam(
        numerical_aperture=0.1 * units.AU,
        wavelength=1550 * units.nanometer,
        optical_power=100e-3 * units.watt,
    )

    opto_electronics = OptoElectronics(
        detectors=[detector_0, detector_1],
        source=beam,
        amplifier=amplifier
    )

    fluidics = Fluidics(
        scatterer_collection=scatterer_collection,
        flow_cell=flow_cell
    )

    signal_processing = SignalProcessing(
        digitizer=digitizer,

    )

    return FlowCytometer(
        opto_electronics=opto_electronics,
        fluidics=fluidics,
        signal_processing=signal_processing,
        background_power=0.01 * units.milliwatt,
    )


# ----------------- UNIT TESTS -----------------

def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    result = flow_cytometer.run(run_time=0.05 * units.millisecond)


    assert result.analog['default'].pint.quantity.check(units.volt), "Acquisition signal is not in volts."

    assert np.std(result.analog['default'].pint.quantity.magnitude) > 0, "Acquisition signal variance is zero, indicating no noise added."


def test_flow_cytometer_multiple_detectors(flow_cytometer):
    """Ensure that both detectors generate non-zero signals."""
    results = flow_cytometer.run(run_time=0.05 * units.millisecond)

    signal_0 = results.analog['default']
    signal_1 = results.analog['default']

    assert not np.all(signal_0 == 0 * units.volt), "Detector 0 signal is all zeros."
    assert not np.all(signal_1 == 0 * units.volt), "Detector 1 signal is all zeros."


@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show, flow_cytometer, digitizer):
    """Test if the flow cytometer plots without error."""
    results = flow_cytometer.run(run_time=0.05 * units.millisecond)

    results.analog.plot()
    plt.close()

    results.analog.digitalize(digitizer=digitizer).plot()
    plt.close()


def test_flow_cytometer_triggered_acquisition(flow_cytometer):
    """Test triggered acquisition with a defined threshold."""
    results = flow_cytometer.run(run_time=0.05 * units.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        trigger_detector_name='default',
        threshold='3 sigma',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_signal = _triggering_system.run(
        dataframe=results.analog,

    )

    assert triggered_signal is not None, "Triggered acquisition failed to return results."
    assert len(triggered_signal) > 0, "Triggered acquisition has no signal data."


def test_flow_cytometer_signal_processing(flow_cytometer):
    """Test filtering and baseline restoration on the acquired signal."""
    results = flow_cytometer.run(run_time=0.05 * units.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold='3 sigma',
    )

    triggered_signal = _triggering_system.run(
        dataframe=results.analog,

    )

    assert np.std(triggered_signal['default']) > 0, "Filtered signal has zero variance."


def test_peak_detection(flow_cytometer, digitizer):
    """Ensure peak detection works correctly on the triggered acquisition."""
    flow_cytometer.signal_processing.analog_processing = [
        circuits.BaselineRestorator(window_size=1000 * units.microsecond),
        circuits.BesselLowPass(cutoff=1 * units.megahertz, order=4, gain=2)
    ]

    results = flow_cytometer.run(run_time=0.05 * units.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        threshold='3 sigma',
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_acquisition = _triggering_system.run(
        dataframe=results.analog,
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    peaks = peak_algorithm.run(digital_signal)

    assert len(peaks) > 0, "No peaks detected when they were expected."


@patch('matplotlib.pyplot.show')
def test_peak_plot(mock_show, flow_cytometer, digitizer):
    """Ensure peak plots render correctly."""
    results = flow_cytometer.run(run_time=0.05 * units.millisecond)
    results.analog.plot()

    trigger = triggering_system.DynamicWindow(
        trigger_detector_name='default',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold='3 sigma',
    )

    triggered_acquisition = trigger.run(
        dataframe=results.analog,
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    peaks = peak_algorithm.run(digital_signal)

    peaks.plot(
        x=('default', 'Height'),
        y=('default_bis', 'Height')
    )

    plt.close()


if __name__ == '__main__':
    pytest.main(["-W error", "-s", __file__])
