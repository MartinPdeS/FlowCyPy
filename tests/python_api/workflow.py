from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from TypedUnit import ureg

from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distribution,
    population,
)
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    TransimpedanceAmplifier,
    source,
)
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    peak_locator,
    triggering_system,
)


# ----------------- FIXTURES -----------------


@pytest.fixture
def amplifier():
    return TransimpedanceAmplifier(
        gain=100 * ureg.volt / ureg.ampere, bandwidth=10 * ureg.megahertz
    )


@pytest.fixture
def digitizer():
    """Fixture for creating a default signal digitizer."""
    return Digitizer(
        bit_depth=1024,
        saturation_levels="auto",
        sampling_rate=5e6 * ureg.hertz,
    )


@pytest.fixture
def detector_0():
    """Fixture for creating the first default detector."""
    return Detector(
        name="default",
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,
    )


@pytest.fixture
def detector_1():
    """Fixture for creating the second default detector."""
    return Detector(
        name="default_bis",
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,
    )


@pytest.fixture
def flow_cell():
    """Fixture for creating a default flow cell."""
    return FlowCell(
        sample_volume_flow=1 * ureg.microliter / ureg.second,
        sheath_volume_flow=6 * ureg.microliter / ureg.second,
        width=10 * ureg.micrometer,
        height=6 * ureg.micrometer,
    )


@pytest.fixture
def scatterer_collection():
    """Fixture for creating a scatterer collection with a default population."""
    scatterer = ScattererCollection()

    diameter_distribution = distribution.Normal(
        mean=1.0 * ureg.micrometer, standard_deviation=0.1 * ureg.micrometer
    )

    ri_distribution = distribution.Normal(
        mean=1.5 * ureg.RIU, standard_deviation=0.1 * ureg.RIU
    )

    _population = population.Sphere(
        particle_count=110 * ureg.particle,
        diameter=diameter_distribution,
        refractive_index=ri_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
    )

    scatterer.add_population(_population)
    return scatterer


@pytest.fixture
def flow_cytometer(
    detector_0, detector_1, scatterer_collection, flow_cell, amplifier, digitizer
):
    """Fixture for creating a default Flow Cytometer."""

    beam = source.GaussianBeam(
        numerical_aperture=0.1 * ureg.AU,
        wavelength=1550 * ureg.nanometer,
        optical_power=100e-3 * ureg.watt,
    )

    opto_electronics = OptoElectronics(
        detectors=[detector_0, detector_1], source=beam, amplifier=amplifier
    )

    fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

    signal_processing = SignalProcessing(
        digitizer=digitizer,
    )

    return FlowCytometer(
        opto_electronics=opto_electronics,
        fluidics=fluidics,
        signal_processing=signal_processing,
        background_power=0.01 * ureg.milliwatt,
    )


# ----------------- UNIT TESTS -----------------


def test_flow_cytometer_acquisition(flow_cytometer):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    result = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    assert result.signal.analog["default"].pint.quantity.check(
        ureg.volt
    ), "Acquisition signal is not in volts."

    assert (
        np.std(result.signal.analog["default"].pint.quantity.magnitude) > 0
    ), "Acquisition signal variance is zero, indicating no noise added."


def test_flow_cytometer_multiple_detectors(flow_cytometer):
    """Ensure that both detectors generate non-zero signals."""
    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    signal_0 = run_record.signal.analog["default"]
    signal_1 = run_record.signal.analog["default"]

    assert not np.all(signal_0 == 0 * ureg.volt), "Detector 0 signal is all zeros."
    assert not np.all(signal_1 == 0 * ureg.volt), "Detector 1 signal is all zeros."


@patch("matplotlib.pyplot.show")
def test_flow_cytometer_plot(mock_show, flow_cytometer, digitizer):
    """Test if the flow cytometer plots without error."""
    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    run_record.plot_analog()
    plt.close()

    run_record.signal.analog.digitalize(digitizer=digitizer)
    plt.close()


def test_flow_cytometer_triggered_acquisition(flow_cytometer):
    """Test triggered acquisition with a defined threshold."""
    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        trigger_detector_name="default",
        threshold="3 sigma",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_signal = _triggering_system.run(
        dataframe=run_record.signal.analog,
    )

    assert (
        triggered_signal is not None
    ), "Triggered acquisition failed to return run_record."
    assert len(triggered_signal) > 0, "Triggered acquisition has no signal data."


def test_flow_cytometer_signal_processing(flow_cytometer):
    """Test filtering and baseline restoration on the acquired signal."""
    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        trigger_detector_name="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold="3 sigma",
    )

    triggered_signal = _triggering_system.run(
        dataframe=run_record.signal.analog,
    )

    assert np.std(triggered_signal["default"]) > 0, "Filtered signal has zero variance."


def test_peak_detection(flow_cytometer, digitizer):
    """Ensure peak detection works correctly on the triggered acquisition."""
    flow_cytometer.signal_processing.analog_processing = [
        circuits.BaselineRestorator(window_size=1000 * ureg.microsecond),
        circuits.BesselLowPass(cutoff=1 * ureg.megahertz, order=4, gain=2),
    ]

    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)

    _triggering_system = triggering_system.DynamicWindow(
        threshold="3 sigma",
        trigger_detector_name="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_acquisition = _triggering_system.run(
        dataframe=run_record.signal.analog,
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    peaks = peak_algorithm.run(digital_signal)

    assert len(peaks) > 0, "No peaks detected when they were expected."


@patch("matplotlib.pyplot.show")
def test_peak_plot(mock_show, flow_cytometer, digitizer):
    """Ensure peak plots render correctly."""
    run_record = flow_cytometer.run(run_time=0.05 * ureg.millisecond)
    run_record.plot_analog()

    trigger = triggering_system.DynamicWindow(
        trigger_detector_name="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold="3 sigma",
    )

    triggered_acquisition = trigger.run(
        dataframe=run_record.signal.analog,
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digital_signal = triggered_acquisition.digitalize(digitizer=digitizer)

    _ = peak_algorithm.run(digital_signal)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
