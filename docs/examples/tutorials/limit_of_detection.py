"""
Limit of Detection
==================

This example simulates the detection of small nanoparticles (90-150 nm diameter)
in a flow cytometry setup using a dual-detector configuration (side and forward scatter).
The simulation includes noise models, realistic fluidics, analog signal conditioning,
digitization, triggering, and peak detection.

The main goal is to evaluate whether such particles produce detectable and distinguishable
scatter signals in the presence of system noise and fluidic variability.
"""

from FlowCyPy.units import ureg
from FlowCyPy import FlowCytometer
from FlowCyPy.fluidics import (
    distributions,
    FlowCell,
    Fluidics,
    ScattererCollection,
    populations,
)
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    Digitizer,
    Amplifier,
    source,
    circuits,
)
from FlowCyPy.digital_processing import (
    DigitalProcessing,
    peak_locator,
    discriminator,
)

# %%
# Optical Source
source = source.Gaussian(
    waist_z=10 * ureg.micrometer,
    waist_y=60 * ureg.micrometer,
    wavelength=405 * ureg.nanometer,
    optical_power=100 * ureg.milliwatt,
)

# %%
# Flow Cell Configuration
flow_cell = FlowCell(
    sample_volume_flow=0.02 * ureg.microliter / ureg.second,
    sheath_volume_flow=0.1 * ureg.microliter / ureg.second,
    width=20 * ureg.micrometer,
    height=10 * ureg.micrometer,
)

# %%
# Define Scatterer Populations (90–150 nm spheres)
scatterer_collection = ScattererCollection()

for size in [150, 125, 100, 75, 50]:
    pop = populations.SpherePopulation(
        name=f"{size} nm",
        concentration=5e9 * ureg.particle / ureg.milliliter,
        diameter=distributions.Delta(value=size * ureg.nanometer),
        refractive_index=distributions.Delta(value=1.36 * ureg.RIU),
        medium_refractive_index=1.33 * ureg.RIU,
    )
    scatterer_collection.add_population(pop)

scatterer_collection.dilute(factor=100)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

digitizer = Digitizer(
    bit_depth=14, use_auto_range=True, sampling_rate=60 * ureg.megahertz
)

# %%
# Detectors
detector_side = Detector(
    name="side",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.2 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
    dark_current=0.1 * ureg.nanoampere,
)

detector_forward = Detector(
    name="forward",
    phi_angle=0 * ureg.degree,
    numerical_aperture=0.2 * ureg.AU,
    responsivity=1 * ureg.ampere / ureg.watt,
    dark_current=0.1 * ureg.nanoampere,
)

# %%
# Opto-Electronics Processing Pipeline
amplifier = Amplifier(
    gain=10_000 * ureg.volt / ureg.ampere, bandwidth=10 * ureg.megahertz
)

analog_processing = [
    circuits.BesselLowPass(cutoff_frequency=0.4 * ureg.megahertz, order=4, gain=2),
    circuits.BaselineRestorationServo(time_constant=50 * ureg.microsecond),
]

opto_electronics = OptoElectronics(
    digitizer=digitizer,
    analog_processing=analog_processing,
    detectors=[detector_side, detector_forward],
    source=source,
    amplifier=amplifier,
)

# %%
# Digital Processing Pipeline
discriminator = discriminator.FixedWindow(
    trigger_channel="side",
    threshold="4sigma",
    max_triggers=-1,
    pre_buffer=128,
    post_buffer=128,
)

digital_processing = DigitalProcessing(
    discriminator=discriminator,
    peak_algorithm=peak_locator.GlobalPeakLocator(),
)

# %% Create and Run the Cytometer Simulation
cytometer = FlowCytometer(
    fluidics=fluidics,
    background_power=0.1 * ureg.nanowatt,
)

run_record = cytometer.run(
    run_time=10.0 * ureg.millisecond,
    digital_processing=digital_processing,
    opto_electronics=opto_electronics,
)

# %%
# Plot Raw Analog Signal
run_record.plot_analog()

# %%
# Plot Triggered Analog Signal Segments
run_record.plot_digital()
