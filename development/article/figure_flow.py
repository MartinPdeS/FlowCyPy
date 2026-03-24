"""
Flow Cytometry Simulation: Full System Example
==============================================

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

# %%
# Step 0: Global Settings and Imports
# -----------------------------------
from TypedUnit import ureg

# %%
# Step 1: Define Flow Cell and Fluidics
# -------------------------------------
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    populations,
    SampleFlowRate,
    SheathFlowRate,
)
from FlowCyPy.opto_electronics import Detector, OptoElectronics, Amplifier, source
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    peak_locator,
    discriminator,
)
from FlowCyPy import FlowCytometer
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
    scale=50 * ureg.nanometer,
    shape=1.1,
    low_cutoff=0.0 * ureg.nanometer,
)

ri_dist = distributions.Normal(
    mean=1.44 * ureg.RIU,
    standard_deviation=0.8 * ureg.RIU,
    low_cutoff=1.33 * ureg.RIU,
)

sampling_method = populations.GammaModel(number_of_samples=10_000)

population_0 = populations.SpherePopulation(
    name="Pop 0",
    medium_refractive_index=medium_refractive_index,
    concentration=5e9 * ureg.particle / ureg.milliliter,
    diameter=diameter_dist,
    refractive_index=ri_dist,
    # sampling_method=sampling_method,
)


scatterer_collection.add_population(population_0)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)


source = source.Gaussian(
    waist_z=10e-6 * ureg.meter,  # Beam waist along flow direction (z-axis)
    waist_y=60e-6 * ureg.meter,
    wavelength=405 * ureg.nanometer,
    optical_power=200 * ureg.milliwatt,
    include_shot_noise=True,
    bandwidth=2 * ureg.megahertz,
    rin=-110 * ureg.dB_per_Hz,
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

amplifier = Amplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=2 * ureg.megahertz,
    voltage_noise_density=0.05 * ureg.nanovolt / ureg.sqrt_hertz,
    # current_noise_density=0.01 * ureg.femtoampere / ureg.sqrt_hertz,
)

opto_electronics = OptoElectronics(
    detectors=detectors, source=source, amplifier=amplifier
)

digitizer = Digitizer(
    sampling_rate=10 * ureg.megahertz,
    bit_depth=14,
    use_auto_range=True,
    output_signed_codes=True,
)

analog_processing = [
    circuits.BaselineRestorationServo(time_constant=100 * ureg.microsecond),
    circuits.BesselLowPass(cutoff_frequency=2 * ureg.megahertz, order=4, gain=2),
]

triggering = discriminator.DynamicWindow(
    trigger_channel="side",
    threshold="2sigma",
    pre_buffer=10,
    post_buffer=10,
    max_triggers=-1,
)

peak_algo = peak_locator.GlobalPeakLocator(compute_width=False, compute_area=True)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=analog_processing,
    discriminator=triggering,
    peak_algorithm=peak_algo,
)

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=0.01 * ureg.milliwatt,
)

run_record = cytometer.run(run_time=1 * ureg.millisecond)

# _ = run_record.event_collection.plot(x="Diameter")

# _ = run_record.event_collection.plot(x="forward")

_ = run_record.plot_analog(figure_size=(12, 8))

_ = run_record.plot_digital(figure_size=(12, 8))

_ = run_record.peaks.plot(
    x=("forward", "Height"),
    y=("side", "Height"),
    # yscale="log",
    # xscale='log',
    plot_type="scatter",
    # xlim=(1e3, 1e5),
    # ylim=(1e3, 1e5)
)
import matplotlib.pyplot as plt

plt.show()
