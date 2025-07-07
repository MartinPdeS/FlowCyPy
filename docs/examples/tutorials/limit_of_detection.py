"""
Limit of Detection
==================

This example simulates the detection of small nanoparticles (90–150 nm diameter)
in a flow cytometry setup using a dual-detector configuration (side and forward scatter).
The simulation includes noise models, realistic fluidics, analog signal conditioning,
digitization, triggering, and peak detection.

The main goal is to evaluate whether such particles produce detectable and distinguishable
scatter signals in the presence of system noise and fluidic variability.
"""

# %% Imports
import numpy as np
from FlowCyPy.fluidics import Fluidics, FlowCell, population, distribution, ScattererCollection
from FlowCyPy.opto_electronics import OptoElectronics, source, TransimpedanceAmplifier, Detector
from FlowCyPy.signal_processing import SignalProcessing, Digitizer, circuits, peak_locator, triggering_system
from FlowCyPy import FlowCytometer, SimulationSettings, units

# %% Simulation Configuration
SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True
SimulationSettings.evenly_spaced_events = True
SimulationSettings.sorted_population = True

np.random.seed(3)

# %% Optical Source
source = source.GaussianBeam(
    numerical_aperture=0.1 * units.AU,
    wavelength=488 * units.nanometer,
    optical_power=200 * units.milliwatt
)

# %% Flow Cell Configuration
flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,
    sheath_volume_flow=0.1 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
)

# %% Define Scatterer Populations (90–150 nm spheres)
scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

for size in [150, 130, 110, 90]:
    pop = population.Sphere(
        name=f'{size} nm',
        particle_count=20 * units.particle,
        diameter=distribution.Delta(position=size * units.nanometer),
        refractive_index=distribution.Delta(position=1.39 * units.RIU)
    )
    scatterer_collection.add_population(pop)

# %% Fluidics Subsystem
fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

# %% Signal Digitizer
digitizer = Digitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz
)

# %% Detectors
detector_side = Detector(
    name='side',
    phi_angle=90 * units.degree,
    numerical_aperture=0.2 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    dark_current=0.001 * units.milliampere
)

detector_forward = Detector(
    name='forward',
    phi_angle=0 * units.degree,
    numerical_aperture=0.2 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    dark_current=0.001 * units.milliampere
)

# %% Amplifier and Opto-Electronics
amplifier = TransimpedanceAmplifier(
    gain=10000 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_side, detector_forward],
    source=source,
    amplifier=amplifier
)

# %% Analog Processing Pipeline
analog_processing = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=1 * units.megahertz, order=4, gain=2)
]

# %% Triggering and Peak Detection
triggering_system = triggering_system.DynamicWindow(
    trigger_detector_name='forward',
    threshold=0.4 * units.millivolt,
    max_triggers=-1,
    pre_buffer=64,
    post_buffer=64
)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=analog_processing,
    triggering_system=triggering_system,
    peak_algorithm=peak_locator.GlobalPeakLocator()
)

# %% Create and Run the Cytometer Simulation
cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=0.0001 * units.milliwatt
)

results = cytometer.run(run_time=1.0 * units.millisecond)

# %% Plot Raw Analog Signal
results.analog.normalize_units(time_units='max', signal_units='max')
results.analog.plot()

# %% Plot Triggered Analog Signal Segments
results.triggered_analog.plot()

# %% Plot Peak Features (Side vs Forward Height)
results.peaks.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)
