"""
Full system simulation
======================

This tutorial demonstrates a complete flow cytometry simulation using the FlowCyPy library.
It models fluidics, optics, signal processing, and classification of multiple particle populations.

Steps Covered:
--------------
1. Configure simulation parameters and noise models
2. Define laser source, flow cell geometry, and fluidics
3. Add synthetic particle populations
4. Set up detectors, amplifier, and digitizer
5. Simulate analog and digital signal acquisition
6. Apply triggering and peak detection
7. Classify particle events based on peak features
"""


def format_figure(figure):
    for axis in figure.axes:
        axis.tick_params(labelsize=9)
        axis.xaxis.label.set_size(10)
        axis.yaxis.label.set_size(10)
        axis.title.set_size(12)
        legend = axis.get_legend()
        if legend is not None:
            legend.get_title().set_fontsize(9)
            for text in legend.get_texts():
                text.set_fontsize(9)
    figure.tight_layout()
    return figure


def format_signal_figure(figure, signal, title):
    time_unit = signal.attrs["units"]["Time"]
    window_end = (100 * ureg.microsecond).to(time_unit).magnitude
    channel_names = [column for column in signal.columns if column != "Time"]

    for axis, channel_name in zip(figure.axes, channel_names):
        axis.set_xlim(0, window_end)
        axis.yaxis.set_label_position("left")
        axis.yaxis.set_ticks_position("left")
        axis.tick_params(labelsize=9)
        axis.xaxis.label.set_size(10)
        axis.yaxis.label.set_size(10)
        axis.grid(True, alpha=0.2)
        if channel_name in signal.attrs["units"]:
            channel_label = {"side": "SSC", "forward": "FSC"}.get(
                channel_name, channel_name
            )
            channel_unit = format(signal.attrs["units"][channel_name], "~")
            axis.set_ylabel(f"{channel_label} [{channel_unit}]", fontsize=10)

        legend = axis.get_legend()
        if legend is not None:
            handles, labels = axis.get_legend_handles_labels()
            legend.remove()
            figure.legend(
                handles,
                [
                    "Analog signal"
                    if "analog" in label.lower()
                    else "Trigger threshold"
                    for label in labels
                ],
                loc="upper center",
                bbox_to_anchor=(0.5, 0.94),
                ncol=len(handles),
                frameon=False,
                fontsize=9,
            )

    figure.suptitle(title, fontsize=13)
    figure.axes[-1].set_xlabel(f"Time [{format(time_unit, '~')}]", fontsize=10)
    figure.tight_layout(rect=(0, 0, 1, 0.86 if figure.legends else 0.91))
    return figure


# %%
# Step 1: Define Flow Cell and Fluidics
# -------------------------------------
from FlowCyPy.units import ureg
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    populations,
    SampleFlowRate,
    SheathFlowRate,
)

from FlowCyPy.fluidics import distributions

flow_cell = FlowCell(
    sample_volume_flow=SampleFlowRate.MEDIUM.value,
    sheath_volume_flow=SheathFlowRate.MEDIUM.value,
    width=400 * ureg.micrometer,
    height=150 * ureg.micrometer,
)

scatterer_collection = ScattererCollection()

medium_refractive_index = distributions.Delta(1.33)

diameter_dist = distributions.RosinRammler(
    scale=200 * ureg.nanometer,
    shape=10,
)

ri_dist = distributions.Normal(
    mean=1.44,
    standard_deviation=0.002,
    low_cutoff=1.33,
)

sampling_method = populations.ExplicitModel()

population_0 = populations.SpherePopulation(
    name="Pop 0",
    medium_refractive_index=medium_refractive_index,
    concentration=1e10 * ureg.particle / ureg.milliliter,
    diameter=diameter_dist,
    refractive_index=ri_dist,
    sampling_method=sampling_method,
)


diameter_dist = distributions.RosinRammler(
    scale=30 * ureg.nanometer,
    shape=50,
)

ri_dist = distributions.Normal(
    mean=1.44,
    standard_deviation=0.002,
    low_cutoff=1.33,
)

population_1 = populations.SpherePopulation(
    name="Pop 1",
    medium_refractive_index=medium_refractive_index,
    concentration=5e11 * ureg.particle / ureg.milliliter,
    diameter=diameter_dist,
    refractive_index=ri_dist,
    sampling_method=populations.GammaModel(number_of_samples=5_000),
)

scatterer_collection.add_population(population_0, population_1)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# %%
# Step 2: Define Optical Subsystem
# --------------------------------
from FlowCyPy.opto_electronics import (
    Detector,
    Digitizer,
    OptoElectronics,
    Amplifier,
    source,
    circuits,
)

analog_processing = [
    circuits.BaselineRestorationServo(time_constant=100 * ureg.microsecond),
    circuits.BesselLowPass(cutoff_frequency=2 * ureg.megahertz, order=4, gain=2),
]

source = source.Gaussian(
    waist_z=10e-6 * ureg.meter,  # Beam waist along flow direction (z-axis)
    waist_y=60e-6 * ureg.meter,
    wavelength=405 * ureg.nanometer,
    optical_power=200 * ureg.milliwatt,
    rin=-140 * ureg.dB_per_Hz,
    bandwidth=10 * ureg.megahertz,
)

detectors = [
    Detector(
        name="side",
        phi_angle=90 * ureg.degree,
        numerical_aperture=1.1,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
    Detector(
        name="forward",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.3,
        cache_numerical_aperture=0.1,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
]

digitizer = Digitizer(
    sampling_rate=60 * ureg.megahertz,
    bit_depth=14,
    use_auto_range=True,
    channel_range_mode="shared",
)

amplifier = Amplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=10 * ureg.megahertz,
    voltage_noise_density=0.0 * ureg.nanovolt / ureg.sqrt_hertz,
    current_noise_density=0.0 * ureg.femtoampere / ureg.sqrt_hertz,
)

opto_electronics = OptoElectronics(
    digitizer=digitizer,
    detectors=detectors,
    source=source,
    amplifier=amplifier,
    analog_processing=analog_processing,
)


# %%
# Step 3: Signal Processing Configuration
# ---------------------------------------
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    peak_locator,
    discriminator,
)

triggering = discriminator.FixedWindow(
    trigger_channel="side",
    threshold="4sigma",
    pre_buffer=40,
    post_buffer=40,
    max_triggers=-1,
)

peak_algo = peak_locator.GlobalPeakLocator()

digital_processing = DigitalProcessing(
    discriminator=triggering,
    peak_algorithm=peak_algo,
)

# %%
# Step 4: Run Simulation
# ----------------------
from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=0.001 * ureg.milliwatt,
)

run_record = cytometer.run(
    opto_electronics=opto_electronics,
    digital_processing=digital_processing,
    run_time=1 * ureg.millisecond,
)


# %%
# Inspect particle sizes
# ----------------------
# Check the sampled diameter distribution before examining the detector response.

_ = format_figure(
    run_record.event_collection.plot(
        x="Diameter",
        figure_size=(8, 5),
        yscale="log",
        title="Particle diameter distributions",
    )
)

# %%
# Step 5: Plot Events and Raw Analog Signals
# ------------------------------------------
_ = format_figure(
    run_record.event_collection.plot(
        x="forward",
        figure_size=(8, 5),
        title="Forward-scatter event distribution",
    )
)


# %%
# Plot raw analog signals
# -----------------------
_ = format_signal_figure(
    run_record.plot_analog(figure_size=(12, 6), include_scatterer=False),
    run_record.signal.analog,
    "Analog detector signals (first 100 µs)",
)


# %%
# Step 6: Plot Triggered Analog Segments
# --------------------------------------
_ = format_signal_figure(
    run_record.plot_digital(figure_size=(12, 6), include_scatterer=False),
    run_record.signal.digital,
    "Triggered segments (first 100 µs)",
)


# %%
# Step 7: Plot Peak Features
# --------------------------
_ = format_figure(
    run_record.plot_peaks(
        x=("forward", "Height"),
        figure_size=(8, 5),
        title="Forward-scatter peak heights",
    )
)
