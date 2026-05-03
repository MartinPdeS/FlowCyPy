# -*- coding: utf-8 -*-

import matplotlib

matplotlib.use("Agg")

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest

from FlowCyPy import FlowCytometer
from FlowCyPy.digital_processing import DigitalProcessing
from FlowCyPy.digital_processing import discriminator
from FlowCyPy.digital_processing import peak_locator
from FlowCyPy.fluidics import FlowCell
from FlowCyPy.fluidics import Fluidics
from FlowCyPy.fluidics import ScattererCollection
from FlowCyPy.fluidics import distributions
from FlowCyPy.fluidics import populations
from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.opto_electronics import Amplifier
from FlowCyPy.opto_electronics import Detector
from FlowCyPy.opto_electronics import Digitizer
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.opto_electronics import circuits
from FlowCyPy.opto_electronics import source
from FlowCyPy.run_record import RunRecord
from FlowCyPy.sub_frames.peaks import PeakDataFrame
from FlowCyPy.units import ureg
from tests.python_api.event_collection import make_population_events


# ----------------- FIXTURES -----------------


@pytest.fixture(autouse=True)
def close_all_matplotlib_figures():
    """
    Ensure that tests never leak matplotlib figures.

    The Agg backend prevents GUI windows from opening, and this fixture ensures
    that figures created during plotting tests are closed even if assertions fail.
    """
    yield
    plt.close("all")


@pytest.fixture
def amplifier():
    return Amplifier(
        gain=100 * ureg.volt / ureg.ampere,
        bandwidth=1 * ureg.megahertz,
    )


@pytest.fixture
def digitizer():
    return Digitizer(
        bit_depth=12,
        sampling_rate=5e6 * ureg.hertz,
        use_auto_range=True,
    )


@pytest.fixture
def detector_0():
    return Detector(
        name="default",
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,
    )


@pytest.fixture
def detector_1():
    return Detector(
        name="default_bis",
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,
    )


@pytest.fixture
def flow_cell():
    return FlowCell(
        sample_volume_flow=1 * ureg.microliter / ureg.second,
        sheath_volume_flow=6 * ureg.microliter / ureg.second,
        width=10 * ureg.micrometer,
        height=6 * ureg.micrometer,
    )


@pytest.fixture
def scatterer_collection():
    scatterer_collection = ScattererCollection()

    diameter_distribution = distributions.Normal(
        mean=1.0 * ureg.micrometer,
        standard_deviation=0.1 * ureg.micrometer,
    )

    refractive_index_distribution = distributions.Normal(
        mean=1.5 * ureg.RIU,
        standard_deviation=0.1 * ureg.RIU,
    )

    sampling_method = populations.ExplicitModel()

    sphere_population = populations.SpherePopulation(
        concentration=5e9 * ureg.particle / ureg.milliliter,
        diameter=diameter_distribution,
        refractive_index=refractive_index_distribution,
        medium_refractive_index=1.33 * ureg.RIU,
        name="Default population",
        sampling_method=sampling_method,
    )

    scatterer_collection.add_population(sphere_population)

    return scatterer_collection


@pytest.fixture
def opto_electronics(detector_0, detector_1, amplifier, digitizer):
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
    fluidics = Fluidics(
        scatterer_collection=scatterer_collection,
        flow_cell=flow_cell,
    )

    return FlowCytometer(
        fluidics=fluidics,
        background_power=0.01 * ureg.milliwatt,
    )


# ----------------- HELPERS -----------------


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
        event_collection=EventCollection(
            events_list=[
                make_population_events(name="A"),
            ]
        ),
        peaks=peak_dataframe,
    )


def make_short_run_record(flow_cytometer, opto_electronics) -> RunRecord:
    return flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(),
    )


def make_dynamic_window_discriminator() -> discriminator.DynamicWindow:
    return discriminator.DynamicWindow(
        trigger_channel="default",
        threshold="3 sigma",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )


# ----------------- UNIT TESTS -----------------


def test_flow_cytometer_acquisition(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    assert run_record.signal.analog["default"].units == ureg.volt
    assert np.std(run_record.signal.analog["default"].magnitude) > 0


def test_flow_cytometer_multiple_detectors(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    detector_0_signal = run_record.signal.analog["default"]
    detector_1_signal = run_record.signal.analog["default_bis"]

    assert not np.all(detector_0_signal == 0 * ureg.volt)
    assert not np.all(detector_1_signal == 0 * ureg.volt)


@patch("matplotlib.pyplot.show")
def test_flow_cytometer_plot_is_called_without_rendering(
    mocked_show,
    flow_cytometer,
    opto_electronics,
):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    with patch.object(run_record, "plot_analog", autospec=True) as mocked_plot_analog:
        run_record.plot_analog()

    mocked_plot_analog.assert_called_once_with()
    mocked_show.assert_not_called()


def test_flow_cytometer_triggered_acquisition(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    dynamic_window_discriminator = make_dynamic_window_discriminator()

    triggered_signal = dynamic_window_discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    assert triggered_signal is not None
    assert len(triggered_signal) > 0


def test_flow_cytometer_digital_processing(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    dynamic_window_discriminator = make_dynamic_window_discriminator()

    triggered_signal = dynamic_window_discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    assert np.std(triggered_signal["default"]) > 0


def test_peak_detection(flow_cytometer, digitizer, opto_electronics):
    opto_electronics.analog_processing = [
        circuits.BaselineRestorationServo(
            time_constant=10 * ureg.microsecond,
        ),
        circuits.BesselLowPass(
            cutoff_frequency=1 * ureg.megahertz,
            order=4,
            gain=2,
        ),
    ]

    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    dynamic_window_discriminator = make_dynamic_window_discriminator()

    triggered_acquisition = dynamic_window_discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    digitizer.capture_signal(run_record.signal.analog.raw_data["default"])

    digital_signal_dict = digitizer.digitize_data_dict(triggered_acquisition)

    peak_algorithm = peak_locator.GlobalPeakLocator()

    peaks = peak_algorithm.run(digital_signal_dict)

    assert len(peaks) > 0


@patch("matplotlib.pyplot.show")
def test_peak_plot_dependencies_are_called_without_rendering(
    mocked_show,
    flow_cytometer,
    digitizer,
    opto_electronics,
):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    with patch.object(run_record, "plot_analog", autospec=True) as mocked_plot_analog:
        run_record.plot_analog()

    dynamic_window_discriminator = make_dynamic_window_discriminator()

    triggered_acquisition = dynamic_window_discriminator.run_with_dict(
        run_record.signal.analog.raw_data
    )

    digitizer.capture_signal(run_record.signal.analog.raw_data["default"])

    digital_signal_dict = digitizer.digitize_data_dict(triggered_acquisition)

    peak_algorithm = peak_locator.GlobalPeakLocator()

    with patch.object(
        peak_algorithm,
        "run",
        wraps=peak_algorithm.run,
    ) as mocked_peak_algorithm_run:
        peaks = peak_algorithm.run(digital_signal_dict)

    mocked_plot_analog.assert_called_once_with()
    mocked_peak_algorithm_run.assert_called_once_with(digital_signal_dict)
    mocked_show.assert_not_called()
    assert len(peaks) > 0


def test_run_record_plot_peak_hist_returns_figure():
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peaks(
        x=("default", "Height"),
    )

    assert isinstance(figure, plt.Figure)


def test_run_record_plot_peak_hist_applies_event_style_options(tmp_path):
    run_record = make_run_record_with_peaks()

    output_path = tmp_path / "peak_hist.png"

    figure = run_record.plot_peaks(
        x=("default", "Height"),
        xscale="log",
        yscale="linear",
        figure_size=(7, 5),
        title="Custom Peak Hist",
        xlabel="Custom Peak X",
        ylabel="Custom Peak Y",
        save_as=str(output_path),
    )

    axes = figure.axes[0]

    assert tuple(figure.get_size_inches()) == pytest.approx((7.0, 5.0))
    assert axes.get_title() == "Custom Peak Hist"
    assert axes.get_xlabel() == "Custom Peak X"
    assert axes.get_ylabel() == "Custom Peak Y"
    assert axes.get_xscale() == "log"
    assert axes.get_yscale() == "linear"
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_run_record_plot_peak_hist_savefig_can_be_mocked(tmp_path):
    run_record = make_run_record_with_peaks()

    output_path = tmp_path / "mocked_peak_hist.png"

    with patch.object(plt.Figure, "savefig", autospec=True) as mocked_savefig:
        figure = run_record.plot_peaks(
            x=("default", "Height"),
            save_as=str(output_path),
        )

    mocked_savefig.assert_called_once()
    assert mocked_savefig.call_args.args[0] is figure
    assert mocked_savefig.call_args.args[1] == str(output_path)
    assert not output_path.exists()


def test_run_record_plot_peak_2d_returns_figure():
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peaks(
        x=("default", "Height"),
        y=("default_bis", "Height"),
        plot_type="scatter",
    )

    assert isinstance(figure, plt.Figure)


def test_run_record_plot_peak_2d_has_marginals_by_default():
    run_record = make_run_record_with_peaks()

    figure = run_record.plot_peaks(
        x=("default", "Height"),
        y=("default_bis", "Height"),
    )

    joint_axes, marginal_x_axes, marginal_y_axes = figure.axes

    figure.canvas.draw()

    assert joint_axes.get_xlabel().startswith("default | Height")
    assert joint_axes.get_ylabel().startswith("default_bis | Height")
    assert all(not tick.get_visible() for tick in marginal_x_axes.get_xticklabels())
    assert all(not tick.get_visible() for tick in marginal_y_axes.get_yticklabels())
    assert len(marginal_x_axes.patches) > 0
    assert len(marginal_y_axes.patches) > 0


if __name__ == "__main__":
    pytest.main(["-W", "error", __file__])