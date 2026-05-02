from unittest.mock import patch
import matplotlib.pyplot as plt
import numpy as np
import pytest

from FlowCyPy.units import ureg
from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distributions,
    populations,
)
from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    Amplifier,
    source,
    Digitizer,
    circuits,
)
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    peak_locator,
    discriminator,
    classifier,
)
from FlowCyPy.run_record import RunRecord
from FlowCyPy.sub_frames.peaks import PeakDataFrame
from tests.python_api.event_collection import make_population_events


# ----------------- FIXTURES -----------------
@pytest.fixture
def amplifier():
    return Amplifier(gain=100 * ureg.volt / ureg.ampere, bandwidth=1 * ureg.megahertz)


@pytest.fixture
def digitizer():
    """Fixture for creating a default signal digitizer."""
    return Digitizer(bit_depth=12, sampling_rate=5e6 * ureg.hertz, use_auto_range=True)


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

    diameter_distributions = distributions.Normal(
        mean=1.0 * ureg.micrometer, standard_deviation=0.1 * ureg.micrometer
    )

    ri_distributions = distributions.Normal(
        mean=1.5 * ureg.RIU, standard_deviation=0.1 * ureg.RIU
    )

    sampling_method = populations.ExplicitModel()

    _population = populations.SpherePopulation(
        concentration=5e9 * ureg.particle / ureg.milliliter,
        diameter=diameter_distributions,
        refractive_index=ri_distributions,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
        sampling_method=sampling_method,
    )

    scatterer.add_population(_population)
    return scatterer


@pytest.fixture
def opto_electronics(detector_0, detector_1, amplifier, digitizer):
    """Fixture for creating a default optical source."""
    beam = source.Gaussian(
        waist_z=10 * ureg.micrometer,
        waist_y=60 * ureg.micrometer,
        wavelength=1550 * ureg.nanometer,
        optical_power=100e-3 * ureg.watt,
    )

    return OptoElectronics(
        detectors=[detector_0, detector_1],
        source=beam,
        amplifier=amplifier,
        digitizer=digitizer,
    )


@pytest.fixture
def flow_cytometer(scatterer_collection, flow_cell):
    """Fixture for creating a default Flow Cytometer."""
    fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

    return FlowCytometer(
        fluidics=fluidics,
        background_power=0.01 * ureg.milliwatt,
    )


# ----------------- UNIT TESTS -----------------


def test_flow_cytometer_acquisition(flow_cytometer, opto_electronics):
    """Test if the Flow Cytometer generates a non-zero acquisition signal."""
    result = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    assert (
        result.signal.analog["default"].units == ureg.volt
    ), "Acquisition signal is not in volts."

    assert (
        np.std(result.signal.analog["default"].magnitude) > 0
    ), "Acquisition signal variance is zero, indicating no noise added."


def test_flow_cytometer_multiple_detectors(flow_cytometer, opto_electronics):
    """Ensure that both detectors generate non-zero signals."""
    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    signal_0 = run_record.signal.analog["default"]
    signal_1 = run_record.signal.analog["default"]

    assert not np.all(signal_0 == 0 * ureg.volt), "Detector 0 signal is all zeros."
    assert not np.all(signal_1 == 0 * ureg.volt), "Detector 1 signal is all zeros."


@patch("matplotlib.pyplot.show")
def test_flow_cytometer_plot(mock_show, flow_cytometer, digitizer, opto_electronics):
    """Test if the flow cytometer plots without error."""
    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    run_record.plot_analog()
    plt.close()

    digitizer.capture_signal(run_record.signal.analog.raw_data["default"])

    plt.close()


def test_flow_cytometer_triggered_acquisition(flow_cytometer, opto_electronics):
    """Test triggered acquisition with a defined threshold."""
    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    _discriminator = discriminator.DynamicWindow(
        trigger_channel="default",
        threshold="3 sigma",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_signal = _discriminator.run_with_dict(run_record.signal.analog.raw_data)

    assert (
        triggered_signal is not None
    ), "Triggered acquisition failed to return run_record."
    assert len(triggered_signal) > 0, "Triggered acquisition has no signal data."


def test_flow_cytometer_digital_processing(flow_cytometer, opto_electronics):
    """Test filtering and baseline restoration on the acquired signal."""
    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    _discriminator = discriminator.DynamicWindow(
        trigger_channel="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold="3 sigma",
    )

    triggered_signal = _discriminator.run_with_dict(run_record.signal.analog.raw_data)

    assert np.std(triggered_signal["default"]) > 0, "Filtered signal has zero variance."


def test_peak_detection(flow_cytometer, digitizer, opto_electronics):
    """Ensure peak detection works correctly on the triggered acquisition."""
    opto_electronics.analog_processing = [
        circuits.BaselineRestorationServo(time_constant=10 * ureg.microsecond),
        circuits.BesselLowPass(cutoff_frequency=1 * ureg.megahertz, order=4, gain=2),
    ]

    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )

    _discriminator = discriminator.DynamicWindow(
        threshold="3 sigma",
        trigger_channel="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )

    triggered_acquisition = _discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digitizer.capture_signal(run_record.signal.analog.raw_data["default"])

    digital_signal_dict = digitizer.digitize_data_dict(triggered_acquisition)

    peaks = peak_algorithm.run(digital_signal_dict)

    assert len(peaks) > 0, "No peaks detected when they were expected."


@patch("matplotlib.pyplot.show")
def test_peak_plot(mock_show, flow_cytometer, digitizer, opto_electronics):
    """Ensure peak plots render correctly."""
    run_record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )
    run_record.plot_analog()

    _discriminator = discriminator.DynamicWindow(
        trigger_channel="default",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
        threshold="3 sigma",
    )

    triggered_acquisition = _discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    peak_algorithm = peak_locator.GlobalPeakLocator()

    digitizer.capture_signal(run_record.signal.analog.raw_data["default"])

    digital_signal_dict = digitizer.digitize_data_dict(triggered_acquisition)

    _ = peak_algorithm.run(digital_signal_dict)


def make_run_record_with_peaks() -> RunRecord:
    peak_dataframe = PeakDataFrame._construct_from_dict(
        {
            0: {
                "default": {
                    "Height": [1.0, 2.0],
                    "Area": [10.0, 12.0],
                },
                "default_bis": {
                    "Height": [1.5, 2.5],
                    "Area": [11.0, 13.0],
                },
            }
        }
    )

    return RunRecord(
        run_time=1 * ureg.millisecond,
        event_collection=EventCollection(events_list=[make_population_events(name="A")]),
        peaks=peak_dataframe,
    )


def test_run_record_plot_peak_hist_returns_figure() -> None:
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peak(x=("default", "Height"))

    assert isinstance(figure, plt.Figure)
    plt.close(figure)


def test_run_record_plot_peak_hist_applies_event_style_options(tmp_path) -> None:
    run_record = make_run_record_with_peaks()
    output_path = tmp_path / "peak_hist.png"

    figure = run_record.plot_peak(
        x=("default", "Height"),
        xscale="log",
        yscale="linear",
        figure_size=(7, 5),
        title="Custom Peak Hist",
        xlabel="Custom Peak X",
        ylabel="Custom Peak Y",
        save_as=str(output_path),
    )
    ax = figure.axes[0]

    assert tuple(figure.get_size_inches()) == pytest.approx((7.0, 5.0))
    assert ax.get_title() == "Custom Peak Hist"
    assert ax.get_xlabel() == "Custom Peak X"
    assert ax.get_ylabel() == "Custom Peak Y"
    assert ax.get_xscale() == "log"
    assert ax.get_yscale() == "linear"
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    plt.close(figure)


def test_run_record_plot_peak_2d_returns_figure() -> None:
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peak(
        x=("default", "Height"),
        y=("default_bis", "Height"),
        plot_type="scatter",
    )

    assert isinstance(figure, plt.Figure)
    plt.close(figure)


def test_run_record_plot_peak_2d_has_marginals_by_default() -> None:
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peak(
        x=("default", "Height"),
        y=("default_bis", "Height"),
    )
    joint_ax, marginal_x_ax, marginal_y_ax = figure.axes

    figure.canvas.draw()

    assert joint_ax.get_xlabel().startswith("default | Height")
    assert joint_ax.get_ylabel().startswith("default_bis | Height")
    assert all(not tick.get_visible() for tick in marginal_x_ax.get_xticklabels())
    assert all(not tick.get_visible() for tick in marginal_y_ax.get_yticklabels())
    assert len(marginal_x_ax.patches) > 0
    assert len(marginal_y_ax.patches) > 0

    plt.close(figure)


if __name__ == "__main__":
    pytest.main(["-W error", __file__])
