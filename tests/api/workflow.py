
import matplotlib

matplotlib.use("Agg")

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest

from FlowCyPy import FlowCytometer
from FlowCyPy.digital_processing import DigitalProcessing, discriminator, peak_locator
from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distributions,
    populations,
)
from FlowCyPy.fluidics.event_collection import EventCollection
from FlowCyPy.fluidics.population_events import PopulationEvents
from FlowCyPy.opto_electronics import (
    Amplifier,
    Detector,
    Digitizer,
    OptoElectronics,
    circuits,
    source,
)
from FlowCyPy.run_record import RunRecord
from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame
from FlowCyPy.sub_frames.events import EventDataFrame
from FlowCyPy.sub_frames.peaks import PeakDataFrame
from FlowCyPy.units import ureg
from FlowCyPy.workflow import Workflow
from tests.api.event_collection import make_population_events

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
        random_state=42,
    )


def make_dynamic_window_discriminator() -> discriminator.DynamicWindow:
    return discriminator.DynamicWindow(
        trigger_channel="default",
        threshold="3 sigma",
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20,
    )


def make_workflow(detector_0, scatterer_collection, **overrides) -> Workflow:
    configuration = {
        "source": source.Gaussian(
            waist_z=10 * ureg.micrometer,
            waist_y=60 * ureg.micrometer,
            wavelength=1550 * ureg.nanometer,
            optical_power=100e-3 * ureg.watt,
        ),
        "sample_volume_flow": 1 * ureg.microliter / ureg.second,
        "sheath_volume_flow": 6 * ureg.microliter / ureg.second,
        "width": 10 * ureg.micrometer,
        "height": 6 * ureg.micrometer,
        "detectors": [detector_0],
        "bit_depth": 12,
        "sampling_rate": 5e6 * ureg.hertz,
        "population_list": scatterer_collection.populations,
        "gain": 100 * ureg.volt / ureg.ampere,
        "bandwidth": 1 * ureg.megahertz,
        "peak_locator": peak_locator.GlobalPeakLocator(),
        "discriminator": make_dynamic_window_discriminator(),
    }
    configuration.update(overrides)
    return Workflow(**configuration)


# ----------------- UNIT TESTS -----------------


@pytest.mark.parametrize("first_method", ["acquire", "run"])
def test_workflow_initializes_once(detector_0, scatterer_collection, first_method):
    workflow = make_workflow(detector_0, scatterer_collection)
    settings = {"run_time": 0.05 * ureg.millisecond, "random_state": 123}
    first = getattr(workflow, first_method)(**settings)
    instrument = workflow.cytometer
    second = workflow.run(**settings)
    assert workflow.cytometer is instrument
    if first_method == "acquire":
        assert first.digital_processing is None
        first = first.process(digital_processing=workflow.digital_processing)
    np.testing.assert_array_equal(
        first.signal.analog["default"].to("volt").magnitude,
        second.signal.analog["default"].to("volt").magnitude,
    )
    workflow.initialize()
    assert workflow.cytometer is not instrument


@pytest.mark.parametrize("use_filter", [False, True])
def test_process_thresholds_in_either_order(opto_electronics, use_filter):
    if use_filter:
        opto_electronics.analog_processing = [
            circuits.BaselineRestorationServo(time_constant=100 * ureg.microsecond)
        ]
    waveform = np.zeros(100)
    waveform[20:24] = 2
    waveform[60:64] = 4
    analog = {
        "Time": np.arange(100) / opto_electronics.digitizer.sampling_rate,
        "default": waveform * ureg.volt,
        "default_bis": waveform * ureg.volt,
    }
    acquisition = RunRecord(
        run_time=100 / opto_electronics.digitizer.sampling_rate,
        event_collection=EventCollection(),
        opto_electronics=opto_electronics,
    )
    acquisition.signal.analog = AcquisitionDataFrame._construct_from_signal_dict(analog)
    other = AcquisitionDataFrame._construct_from_signal_dict(
        {**analog, "default": waveform * 0 * ureg.volt}
    )
    assert acquisition.signal.analog.raw_data is not other.raw_data

    settings = [
        DigitalProcessing(
            discriminator=discriminator.FixedWindow(
                trigger_channel="default",
                threshold=level * ureg.volt,
                pre_buffer=2,
                post_buffer=5,
                max_triggers=-1,
            ),
            peak_locator=peak_locator.GlobalPeakLocator(),
        )
        for level in (1, 3)
    ]
    low, high = [
        acquisition.process(digital_processing=setting) for setting in settings
    ]
    high_again, low_again = [
        acquisition.process(digital_processing=setting)
        for setting in reversed(settings)
    ]
    assert low.number_of_triggers == 2
    assert high.number_of_triggers == 1
    assert acquisition.signal.digital is None
    assert acquisition.peaks is None
    for record, repeated in ((low, low_again), (high, high_again)):
        assert record.signal.analog.raw_data is low.signal.analog.raw_data
        assert record.signal.digital.equals(repeated.signal.digital)
        assert record.peaks.equals(repeated.peaks)


def test_peak_locator_compatibility():
    locator = peak_locator.GlobalPeakLocator()
    for processing in (
        DigitalProcessing(None, locator),
        DigitalProcessing(peak_algorithm=locator),
    ):
        assert processing.peak_locator is locator
        processing.peak_algorithm = None
        assert processing.peak_locator is None
        processing.peak_locator = locator
        assert processing.peak_algorithm is locator
    with pytest.raises(TypeError, match="only one"):
        DigitalProcessing(peak_locator=locator, peak_algorithm=locator)


def test_workflow_initialize_requires_a_population(detector_0, scatterer_collection):
    workflow = make_workflow(
        detector_0,
        scatterer_collection,
        population_list=[],
    )

    with pytest.raises(ValueError, match="at least one population"):
        workflow.initialize()


def test_workflow_initialize_requires_a_detector(detector_0, scatterer_collection):
    workflow = make_workflow(
        detector_0,
        scatterer_collection,
        detectors=[],
    )

    with pytest.raises(ValueError, match="at least one detector"):
        workflow.initialize()


def test_workflow_rejects_duplicate_detector_names(detector_0, scatterer_collection):
    workflow = make_workflow(
        detector_0,
        scatterer_collection,
        detectors=[detector_0, detector_0],
    )

    with pytest.raises(ValueError, match="Detector names must be unique"):
        workflow.initialize()


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("dilution_factor", 0, "dilution_factor"),
        ("bit_depth", -1, "bit_depth"),
        ("sampling_rate", 0 * ureg.hertz, "sampling_rate"),
        ("bandwidth", 3 * ureg.megahertz, "Nyquist"),
    ],
)
def test_workflow_rejects_nonphysical_configuration(
    detector_0,
    scatterer_collection,
    field,
    value,
    message,
):
    workflow = make_workflow(
        detector_0,
        scatterer_collection,
        **{field: value},
    )

    with pytest.raises((ValueError, TypeError), match=message):
        workflow.initialize()


@pytest.mark.parametrize(
    "run_time, exception",
    [(0 * ureg.second, ValueError), (-1 * ureg.second, ValueError), (1, TypeError)],
)
def test_flow_cytometer_rejects_invalid_run_time(
    flow_cytometer,
    opto_electronics,
    run_time,
    exception,
):
    with pytest.raises(exception, match="run_time"):
        flow_cytometer.acquire(run_time=run_time, opto_electronics=opto_electronics)


def test_flow_cytometer_acquisition(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    assert run_record.signal.analog["default"].units == ureg.volt
    assert np.std(run_record.signal.analog["default"].magnitude) > 0


def test_explicit_pulses_wrap_with_mixed_units(flow_cytometer, opto_electronics):
    """Check boundary pulses and detector amplitudes against explicit periodic copies."""
    frame = EventDataFrame()
    frame.set_column("Time", [1000, 50000, 99000], unit=ureg.nanosecond)
    frame.set_column("Velocity", [100, 200, 300], unit=ureg.centimeter / ureg.second)
    frame.set_column("default", [2, 3, 5], unit=ureg.microwatt)
    frame.set_column("default_bis", [7, 11, 13], unit=ureg.nanowatt)
    events = PopulationEvents(
        dataframe=frame,
        population=object(),
        sampling_method=populations.ExplicitModel(),
        name="boundary events",
        scatterer_type="Sphere",
        metadata={},
    )
    sample_times = np.arange(100) * ureg.microsecond
    signals = {
        "Time": sample_times,
        "default": np.ones(100) * ureg.nanowatt,
        "default_bis": np.ones(100) * ureg.nanowatt,
    }
    flow_cytometer._add_explicit_model_signals(
        event_collection=EventCollection(events_list=[events]),
        signal_dict=signals,
        opto_electronics=opto_electronics,
    )

    for detector in opto_electronics.detectors:
        expected = opto_electronics.source.generate_pulses(
            velocities=np.array([3, 1, 2, 3, 1]) * ureg.meter / ureg.second,
            pulse_centers=np.array([-1, 1, 50, 99, 101]) * ureg.microsecond,
            pulse_amplitudes=events.get_quantity(detector.name)[[2, 0, 1, 2, 0]].to(
                "watt"
            ),
            time_array=sample_times.to("second"),
            base_level=1 * ureg.nanowatt,
        )
        assert signals[detector.name].shape == sample_times.shape
        np.testing.assert_allclose(
            signals[detector.name].magnitude, expected.to("nanowatt").magnitude
        )


def test_sphere_coupling_accepts_scaled_refractive_index_units(
    flow_cytometer, opto_electronics
):
    """The same refractive indices in milli-RIU yield the same coupled powers."""
    events = flow_cytometer.fluidics.generate_event_collection(
        run_time=0.01 * ureg.millisecond,
        sampling_rate=opto_electronics.digitizer.sampling_rate,
        random_state=123,
    )
    scaled = events.convert_units(
        column_units={
            "RefractiveIndex": "milliRIU",
            "MediumRefractiveIndex": "milliRIU",
        },
        inplace=False,
    )
    for collection in (events, scaled):
        opto_electronics.add_coupling_to_dataframe(event_collection=collection)
    for detector in opto_electronics.detectors:
        expected = events[0].get_quantity(detector.name).to("watt")
        assert expected.size > 0
        np.testing.assert_allclose(
            scaled[0].get_quantity(detector.name).m_as("watt"),
            expected.magnitude,
            rtol=1e-10,
            atol=0,
        )


def test_flow_cytometer_multiple_detectors(flow_cytometer, opto_electronics):
    run_record = make_short_run_record(
        flow_cytometer=flow_cytometer,
        opto_electronics=opto_electronics,
    )

    detector_0_signal = run_record.signal.analog["default"]
    detector_1_signal = run_record.signal.analog["default_bis"]

    assert not np.all(detector_0_signal == 0 * ureg.volt)
    assert not np.all(detector_1_signal == 0 * ureg.volt)


def test_workflow_gamma_and_explicit_models_complete_acquisition(
    detector_0,
    scatterer_collection,
):
    explicit_workflow = make_workflow(
        detector_0,
        scatterer_collection,
    )
    explicit_workflow.initialize()
    explicit_record = explicit_workflow.run(
        0.05 * ureg.millisecond,
        random_state=123,
    )

    gamma_population = populations.SpherePopulation(
        name="Gamma population",
        concentration=5e9 * ureg.particle / ureg.milliliter,
        diameter=distributions.Delta(1 * ureg.micrometer),
        refractive_index=distributions.Delta(1.5 * ureg.RIU),
        medium_refractive_index=1.33 * ureg.RIU,
        sampling_method=populations.GammaModel(number_of_samples=250),
    )
    gamma_workflow = make_workflow(
        detector_0,
        scatterer_collection,
        population_list=[gamma_population],
    )
    gamma_workflow.initialize()
    gamma_record = gamma_workflow.run(
        0.05 * ureg.millisecond,
        random_state=123,
    )

    for record in (explicit_record, gamma_record):
        signal = record.signal.analog["default"].to("volt").magnitude
        assert signal.size > 0
        assert np.all(np.isfinite(signal))
        assert np.std(signal) > 0

    gamma_events = gamma_record.event_collection[0]
    assert gamma_events.metadata["ExpectedNumberOfParticles"] > 0
    assert "ParticleTrace" in gamma_events.metadata


def test_analog_plot_displays_each_acquired_channel(flow_cytometer, opto_electronics):
    """Each detector axis shows its acquired voltages on the acquisition time grid."""
    record = make_short_run_record(flow_cytometer, opto_electronics)
    analog = record.signal.analog
    time = analog["Time"]
    voltages = {name: analog[name] for name in record.detector_names}

    with patch.object(plt, "show") as show:
        figure = record.plot_analog(include_scatterer=False)
    show.assert_not_called()

    for name, axis in zip(record.detector_names, figure.axes, strict=True):
        assert name in axis.get_ylabel()
        (line,) = axis.lines
        np.testing.assert_allclose(
            line.get_xdata(orig=False), time.m_as(analog.time_units)
        )
        np.testing.assert_allclose(
            line.get_ydata(orig=False), voltages[name].m_as(analog.signal_units)
        )


def test_run_reports_maximum_of_each_digitized_segment(
    flow_cytometer, opto_electronics
):
    """Verify every reported peak against the recorded ADC samples for that channel."""
    opto_electronics.analog_processing = [
        circuits.BaselineRestorationServo(time_constant=10 * ureg.microsecond),
        circuits.BesselLowPass(cutoff_frequency=1 * ureg.megahertz, order=4, gain=2),
    ]
    record = flow_cytometer.run(
        run_time=0.05 * ureg.millisecond,
        opto_electronics=opto_electronics,
        digital_processing=DigitalProcessing(
            discriminator=discriminator.DynamicWindow(
                trigger_channel="default", threshold="1 sigma",
                pre_buffer=4, post_buffer=4, max_triggers=-1,
            ),
            peak_locator=peak_locator.GlobalPeakLocator(),
        ),
        random_state=42,
    )

    assert record.number_of_triggers > 0
    assert record.signal.digital["default"].nunique() > 1
    assert len(record.peaks) == record.number_of_triggers * len(record.detector_names)
    for segment_id, segment in record.signal.digital.groupby(level="SegmentID"):
        for detector in record.detector_names:
            samples = segment[detector].to_numpy()
            peak = record.peaks.loc[(detector, segment_id, 0)]
            assert samples.min() >= 0
            assert samples.max() < 2**opto_electronics.digitizer.bit_depth
            assert peak["Height"] == samples.max()
            assert peak["Index"] == np.argmax(samples)


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
