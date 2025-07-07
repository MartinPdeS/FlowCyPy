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
from FlowCyPy import units, SimulationSettings

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
from FlowCyPy.fluidics import Fluidics, ScattererCollection, population, distribution

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=200 * units.micrometer,
    height=100 * units.micrometer
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

scatterer_collection.add_population(population.Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * units.RIU, std_dev=0.002 * units.RIU)
))

scatterer_collection.add_population(population.Sphere(
    name='Pop 1',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(200 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * units.RIU, std_dev=0.002 * units.RIU)
))

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

# %%
# Step 2: Define Optical Subsystem
# --------------------------------
from FlowCyPy.opto_electronics import source, Detector, TransimpedanceAmplifier, OptoElectronics

source = source.GaussianBeam(
    numerical_aperture=0.1 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=200 * units.milliwatt,
    RIN=-140
)

detectors = [
    Detector(name='forward', phi_angle=0 * units.degree,  numerical_aperture=0.3 * units.AU, responsivity=1 * units.ampere / units.watt),
    Detector(name='side',    phi_angle=90 * units.degree, numerical_aperture=0.3 * units.AU, responsivity=1 * units.ampere / units.watt),
    Detector(name='det 2',   phi_angle=30 * units.degree, numerical_aperture=0.3 * units.AU, responsivity=1 * units.ampere / units.watt),
]

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz,
    voltage_noise_density=0.1 * units.nanovolt / units.sqrt_hertz,
    current_noise_density=0.2 * units.femtoampere / units.sqrt_hertz
)

opto_electronics = OptoElectronics(
    detectors=detectors,
    source=source,
    amplifier=amplifier
)

# %%
# Step 3: Signal Processing Configuration
# ---------------------------------------
from FlowCyPy.signal_processing import SignalProcessing, Digitizer, circuits, peak_locator, triggering_system

digitizer = Digitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz
)

analog_processing = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=2 * units.megahertz, order=4, gain=2)
]

triggering = triggering_system.DynamicWindow(
    trigger_detector_name='forward',
    threshold=10 * units.microvolt,
    pre_buffer=20,
    post_buffer=20,
    max_triggers=-1
)

peak_algo = peak_locator.GlobalPeakLocator(compute_width=False)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=analog_processing,
    triggering_system=triggering,
    peak_algorithm=peak_algo
)

# %%
# Step 4: Run Simulation
# ----------------------
from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=0.001 * units.milliwatt
)

results = cytometer.run(run_time=0.8 * units.millisecond)

# %%
# Step 5: Plot Events and Raw Analog Signals
# ------------------------------------------
_ = results.events.plot(x='side', y='forward', z='RefractiveIndex')


# %%
# Plot raw analog signals
# -----------------------
results.analog.normalize_units(signal_units='max')
_ = results.analog.plot()

# %%
# Step 6: Plot Triggered Analog Segments
# --------------------------------------
_ = results.triggered_analog.plot()

# %%
# Step 7: Classify Events from Peak Features
# ------------------------------------------
from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

classified = classifier.run(
    dataframe=results.peaks.unstack('Detector'),
    features=['Height'],
    detectors=['side', 'forward']
)

_ = classified.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)
