"""
Threshold Sensitivity: Event Detection Near the Noise Floor
===========================================================

This tutorial investigates how discriminator threshold affects event recovery
for weak signals close to baseline noise.
"""

from FlowCyPy.units import ureg
from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    populations,
    distributions,
    SampleFlowRate,
    SheathFlowRate,
)
from FlowCyPy.opto_electronics import (
    Detector,
    Digitizer,
    OptoElectronics,
    Amplifier,
    source,
    circuits,
)
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    discriminator,
    peak_locator,
)

# %%
# Step 1: Build a weak-signal simulation
# --------------------------------------
flow_cell = FlowCell(
    sample_volume_flow=SampleFlowRate.MEDIUM.value,
    sheath_volume_flow=SheathFlowRate.MEDIUM.value,
    width=400 * ureg.micrometer,
    height=150 * ureg.micrometer,
)

scatterer_collection = ScattererCollection()

population = populations.SpherePopulation(
    name="Near-threshold population",
    medium_refractive_index=distributions.Delta(1.33),
    concentration=1e10 * ureg.particle / ureg.milliliter,
    diameter=distributions.RosinRammler(
        scale=100 * ureg.nanometer,
        shape=12,
    ),
    refractive_index=distributions.Normal(
        mean=1.40,
        standard_deviation=0.002,
        low_cutoff=1.33,
    ),
    sampling_method=populations.ExplicitModel(),
)

scatterer_collection.add_population(population)

scatterer_collection.dilute(100)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,
)

analog_processing = [
    circuits.BaselineRestorationServo(time_constant=10 * ureg.microsecond),
    circuits.BesselLowPass(cutoff_frequency=1 * ureg.megahertz, order=4, gain=2),
]

excitation_source = source.Gaussian(
    waist_z=10e-6 * ureg.meter,
    waist_y=60e-6 * ureg.meter,
    wavelength=405 * ureg.nanometer,
    optical_power=25 * ureg.milliwatt,
    rin=-140 * ureg.dB_per_Hz,
    bandwidth=10 * ureg.megahertz,
)

detectors = [
    Detector(
        name="side",
        phi_angle=90 * ureg.degree,
        numerical_aperture=1.1,
        responsivity=1 * ureg.ampere / ureg.watt,
    )
]

amplifier = Amplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=10 * ureg.megahertz,
    voltage_noise_density=0.001 * ureg.nanovolt / ureg.sqrt_hertz,
    current_noise_density=0.001 * ureg.femtoampere / ureg.sqrt_hertz,
)

digitizer = Digitizer(
    sampling_rate=60 * ureg.megahertz,
    bit_depth=14,
    use_auto_range=True,
    channel_range_mode="shared",
)

opto_electronics = OptoElectronics(
    digitizer=digitizer,
    detectors=detectors,
    source=excitation_source,
    amplifier=amplifier,
    analog_processing=analog_processing,
)

cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=0 * ureg.picowatt,
)

# %%
# Step 2: Sweep discriminator threshold
# -------------------------------------
threshold_values = ["2sigma", "3sigma", "4sigma", "5sigma"]
run_records = []

for threshold_value in threshold_values:
    digital_processing = DigitalProcessing(
        discriminator=discriminator.DynamicWindow(
            trigger_channel="side",
            threshold=threshold_value,
            pre_buffer=40,
            post_buffer=40,
            max_triggers=-1,
        ),
        peak_algorithm=peak_locator.GlobalPeakLocator(),
    )

    run_record = cytometer.run(
        opto_electronics=opto_electronics,
        digital_processing=digital_processing,
        run_time=1 * ureg.millisecond,
    )

    run_records.append((threshold_value, run_record))

# %%
# Step 3: Compare recovered events
# --------------------------------
for threshold_value, run_record in run_records:
    print(f"Threshold: {threshold_value}")
    _ = run_record.plot_analog(figure_size=(12, 4))
    _ = run_record.plot_digital(figure_size=(12, 4), xlim=(0, 0.1 * ureg.millisecond))
    _ = run_record.peaks.plot(x=("side", "Height"))
