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
import numpy as np
from TypedUnit import ureg

from FlowCyPy import SimulationSettings

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_amplifier_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True

np.random.seed(3)


# %%
# Step 1: Define Flow Cell and Fluidics
# -------------------------------------
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.fluidics import Fluidics, ScattererCollection, distribution, population

flow_cell = FlowCell(
    sample_volume_flow=80 * ureg.microliter / ureg.minute,
    sheath_volume_flow=1 * ureg.milliliter / ureg.minute,
    width=200 * ureg.micrometer,
    height=100 * ureg.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * ureg.RIU)

population_0 = population.Sphere(
    name="Pop 0",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(150 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(
        1.44 * ureg.RIU, standard_deviation=0.002 * ureg.RIU
    ),
)

population_1 = population.Sphere(
    name="Pop 1",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(200 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(
        1.44 * ureg.RIU, standard_deviation=0.002 * ureg.RIU
    ),
)

scatterer_collection.add_population(population_0, population_1)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(scatterer_collection=scatterer_collection, flow_cell=flow_cell)

# %%
# Step 2: Define Optical Subsystem
# --------------------------------
from FlowCyPy.opto_electronics import (
    Detector,
    OptoElectronics,
    TransimpedanceAmplifier,
    source,
)

source = source.GaussianBeam(
    numerical_aperture=0.1 * ureg.AU,
    wavelength=450 * ureg.nanometer,
    optical_power=200 * ureg.milliwatt,
    RIN=-140,
)

detectors = [
    Detector(
        name="forward",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
    Detector(
        name="side",
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
    Detector(
        name="det 2",
        phi_angle=30 * ureg.degree,
        numerical_aperture=0.3 * ureg.AU,
        responsivity=1 * ureg.ampere / ureg.watt,
    ),
]

amplifier = TransimpedanceAmplifier(
    gain=10 * ureg.volt / ureg.ampere,
    bandwidth=10 * ureg.megahertz,
    voltage_noise_density=0.1 * ureg.nanovolt / ureg.sqrt_hertz,
    current_noise_density=0.2 * ureg.femtoampere / ureg.sqrt_hertz,
)

opto_electronics = OptoElectronics(
    detectors=detectors, source=source, amplifier=amplifier
)


# %%
# Step 3: Signal Processing Configuration
# ---------------------------------------
from FlowCyPy.signal_processing import (
    Digitizer,
    SignalProcessing,
    circuits,
    peak_locator,
    triggering_system,
)

digitizer = Digitizer(
    bit_depth="14bit", saturation_levels="auto", sampling_rate=60 * ureg.megahertz
)

analog_processing = [
    circuits.BaselineRestorator(window_size=10 * ureg.microsecond),
    circuits.BesselLowPass(cutoff=2 * ureg.megahertz, order=4, gain=2),
]

triggering = triggering_system.DynamicWindow(
    trigger_detector_name="forward",
    threshold=10 * ureg.microvolt,
    pre_buffer=20,
    post_buffer=20,
    max_triggers=-1,
)

peak_algo = peak_locator.GlobalPeakLocator(compute_width=False)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=analog_processing,
    triggering_system=triggering,
    peak_algorithm=peak_algo,
)

# %%
# Step 4: Run Simulation
# ----------------------
from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=0.001 * ureg.milliwatt,
)

run_record = cytometer.run(run_time=0.4 * ureg.millisecond)

# %%
# Step 5: Plot Events and Raw Analog Signals
# ------------------------------------------
_ = run_record.event_frame.plot(x="side")


# %%
# Plot raw analog signals
# -----------------------
_ = run_record.plot_analog(figure_size=(12, 8))


# %%
# Step 6: Plot Triggered Analog Segments
# --------------------------------------
_ = run_record.plot_digital(figure_size=(12, 8))


# %%
# Step 7: Plot Peak Features
# --------------------------
_ = run_record.peaks.plot(x=("forward", "Height"))


# %%
# Step 8: Classify Events from Peak Features
# ------------------------------------------
from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

classified = classifier.run(
    dataframe=run_record.peaks.unstack("Detector"),
    features=["Height"],
    detectors=["side", "forward"],
)

_ = classified.plot(x=("side", "Height"), y=("forward", "Height"))
