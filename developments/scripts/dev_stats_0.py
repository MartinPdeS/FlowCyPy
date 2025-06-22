"""
Limit of detection
==================
"""

import numpy as np
from FlowCyPy import FlowCytometer, ScattererCollection, GaussianBeam, TransimpedanceAmplifier
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import units
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Sphere
from FlowCyPy import distribution
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import peak_locator
from FlowCyPy.triggering_system import DynamicWindow, DoubleThreshold, FixedWindow
from FlowCyPy import circuits
from FlowCyPy import OptoElectronics, Fluidics
from FlowCyPy import PMT

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_source_noise = True
NoiseSetting.include_dark_current_noise = True
NoiseSetting.assume_perfect_hydrodynamic_focusing = True

np.random.seed(3)

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,
    wavelength=488 * units.nanometer,
    optical_power=100 * units.milliwatt
)

flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,
    sheath_volume_flow=0.1 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
    event_scheme='uniform-sequential'
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

for size in np.linspace(110, 30, 5):
    size = int(size)
    population = Sphere(
        name=f'{size} nanometer',
        particle_count=5 * units.particle,
        diameter=distribution.Delta(position=size * units.nanometer),
        refractive_index=distribution.Delta(position=1.39 * units.RIU)
    )

    scatterer_collection.add_population(population)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,            # Sampling frequency: 60 MHz
)

detector_0 = PMT(
    name='side',                                  # Detector name: Side scatter detector
    phi_angle=90 * units.degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=.7 * units.AU,               # Numerical aperture: 1.2
)

detector_1 = PMT(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * units.degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=.2 * units.AU,             # Numerical aperture: 1.2
    cache_numerical_aperture=.1 * units.AU,             # Numerical aperture: 1.2
)

amplifier = TransimpedanceAmplifier(
    gain=10000 * units.volt / units.ampere,
    bandwidth = 10 * units.megahertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_1, detector_0],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
)

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    background_power=0.01 * units.milliwatt,
)

# Run the flow cytometry simulation
processing_steps = [
    circuits.BaselineRestorator(window_size=1000 * units.microsecond),
    circuits.BesselLowPass(cutoff=0.4 * units.megahertz, order=4, gain=2)
]

analog_acquisition, _ = cytometer.get_acquisition(
    run_time=0.1 * units.millisecond,
    processing_steps=processing_steps
)

# Visualize the scatter signals from both detectors

analog_acquisition.normalize_units(signal_units='max')
analog_acquisition.plot()

trigger = FixedWindow(
    dataframe=analog_acquisition,
    trigger_detector_name='side',
    max_triggers=15,
    pre_buffer=64,
    post_buffer=64,
    digitizer=digitizer
)



analog_trigger = trigger.run(
    threshold="3sigma",
)

analog_trigger.plot()

digital_trigger = analog_trigger.digitalize(digitizer=digitizer)

digital_trigger.plot()

peak_algorithm = peak_locator.GlobalPeakLocator()

peaks = peak_algorithm.run(digital_trigger)

peaks.plot(
    x=('side', 'Height'),
    y=('forward', 'Height')
)
