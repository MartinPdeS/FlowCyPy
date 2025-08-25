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
from FlowCyPy.workflow import Workflow, Sphere, distribution, Detector, circuits, triggering_system, peak_locator

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_amplifier_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True

np.random.seed(3)

population_0 = Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

detectors = [
    Detector(name='forward', phi_angle=0 * units.degree,  numerical_aperture=0.3 * units.AU, responsivity=1 * units.ampere / units.watt),
    Detector(name='side',    phi_angle=90 * units.degree, numerical_aperture=0.3 * units.AU, responsivity=1 * units.ampere / units.watt),
]

analog_processing = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=2 * units.megahertz, order=4, gain=2)
]

trigger = triggering_system.DynamicWindow(
    trigger_detector_name='forward',
    threshold=50 * units.microvolt,
    pre_buffer=20,
    post_buffer=20,
    max_triggers=-1
)

peak_locator = peak_locator.GlobalPeakLocator(compute_width=False)

workflow = Workflow(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=200 * units.micrometer,
    height=100 * units.micrometer,
    medium_refractive_index=1.33 * units.RIU,

    populations=[population_0],

    source_numerical_aperture=0.1 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=200 * units.milliwatt,

    detectors=detectors,
    gain=10 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz,

    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
    trigger=trigger,
    peak_locator=peak_locator
)

workflow.initialize()

workflow.run(run_time=0.2 * units.millisecond)

workflow.results.events.plot(x='side', y='forward', z='RefractiveIndex')
