import numpy as np
from FlowCyPy import units

from FlowCyPy import SimulationSettings

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_amplifier_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True
np.random.seed(3)


from FlowCyPy.fluidics import Fluidics, ScattererCollection, FlowCell, distribution, population

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=200 * units.micrometer,
    height=100 * units.micrometer,
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

from FlowCyPy.opto_electronics import OptoElectronics, Detector, TransimpedanceAmplifier, source

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

from FlowCyPy.signal_processing import SignalProcessing, triggering_system, Digitizer, circuits, peak_locator

analog_processing = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=2 * units.megahertz, order=4, gain=2)
]

digitizer = Digitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz
)

_triggering_system = triggering_system.FixedWindow(#DynamicWindow(
    trigger_detector_name='forward',
    threshold=1 * units.microvolt,
    pre_buffer=20,
    post_buffer=20,
    max_triggers=-1
)

peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)

signal_processing = SignalProcessing(
    digitizer=digitizer,
    analog_processing=analog_processing,
    triggering_system=_triggering_system,
    peak_algorithm=peak_algorithm
)

from FlowCyPy import FlowCytometer

cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    signal_processing=signal_processing,
    background_power=0.001 * units.milliwatt
)

results = cytometer.run(run_time=0.01 * units.millisecond)

results = cytometer.run(run_time=0.2 * units.millisecond)