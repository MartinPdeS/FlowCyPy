"""
Limit of detection
==================
"""

import numpy as np
from FlowCyPy import FlowCytometer, ScattererCollection, Detector, GaussianBeam, TransimpedanceAmplifier
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import units
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Sphere
from FlowCyPy import distribution
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import peak_locator
from FlowCyPy.triggering_system import TriggeringSystem, Scheme
from FlowCyPy import circuits

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_source_noise = False
NoiseSetting.include_dark_current_noise = False

np.random.seed(3)

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * units.nanometer,              # Laser wavelength: 800 nanometers
    optical_power=100 * units.milliwatt             # Laser optical power: 10 milliwatts
)

flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,        # Flow speed: 10 microliter per second
    sheath_volume_flow=0.1 * units.microliter / units.second,        # Flow speed: 10 microliter per second
    width=20 * units.micrometer,        # Flow area: 10 x 10 micrometers
    height=10 * units.micrometer,        # Flow area: 10 x 10 micrometers
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)  # Medium refractive index: 1.33

for size in [150, 100, 50, 30]:

    population = Sphere(
        name=f'{size} nanometer',
        particle_count=20 * units.particle,
        diameter=distribution.Delta(position=size * units.nanometer),
        refractive_index=distribution.Delta(position=1.39 * units.RIU)
    )

    scatterer_collection.add_population(population)

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,            # Sampling frequency: 60 MHz
)

detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * units.degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=.2 * units.AU,             # Numerical aperture: 1.2
    responsivity=1 * units.ampere / units.watt,        # Responsitivity: 1 ampere per watt
    dark_current=0.01 * units.milliampere,          # Dark current: 0.1 milliamps
)

detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * units.degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=.2 * units.AU,             # Numerical aperture: 1.2
    responsivity=1 * units.ampere / units.watt,        # Responsitivity: 1 ampere per watt
    dark_current=0.01 * units.milliampere,          # Dark current: 0.1 milliamps
)

transimpedance_amplifier = TransimpedanceAmplifier(
    gain=10000 * units.volt / units.ampere,
    bandwidth = 10 * units.megahertz
)

cytometer = FlowCytometer(
    source=source,
    transimpedance_amplifier=transimpedance_amplifier,
    digitizer=digitizer,
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,                     # Populations used in the experiment
    background_power=0.01 * units.milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the flow cytometry simulation
processing_steps = [
    circuits.BaselineRestorator(window_size=1000 * units.microsecond),
    # circuits.BesselLowPass(cutoff=3 * units.megahertz, order=4, gain=2)
]

cytometer.prepare_acquisition(run_time=0.2 * units.millisecond)
analog_acquisition = cytometer.get_acquisition(processing_steps=processing_steps)

# Visualize the scatter signals from both detectors
analog_acquisition.plot()

trigger = TriggeringSystem(
    dataframe=analog_acquisition,
    trigger_detector_name='forward',
    max_triggers=15,
    pre_buffer=64,
    post_buffer=64,
    digitizer=digitizer
)

analog_trigger = trigger.run(
    threshold=3 * units.millivolt,
    scheme=Scheme.FIXED,
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
