from FlowCyPy import units, NoiseSetting
from FlowCyPy import GaussianBeam, ScattererCollection, Detector, SignalDigitizer, TransimpedanceAmplifier, FlowCell
from FlowCyPy.population import Sphere, distribution
from FlowCyPy import FlowCytometer, circuits
from FlowCyPy import OptoElectronics, Fluidics

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = True
NoiseSetting.include_source_noise = True
NoiseSetting.include_amplifier_noise = True
NoiseSetting.assume_perfect_hydrodynamic_focusing = True

source = GaussianBeam(
    numerical_aperture=0.1 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=200 * units.milliwatt,
    RIN=-140
)

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=100 * units.micrometer,
    height=100 * units.micrometer,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

custom_population = Sphere(
    name='Population 1',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

scatterer_collection.add_population(custom_population)

scatterer_collection.dilute(factor=80)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)


amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=10 * units.megahertz,
    voltage_noise_density=.1 * units.nanovolt / units.sqrt_hertz,
    current_noise_density=.2 * units.femtoampere / units.sqrt_hertz
)

opto_electronics = OptoElectronics(
    detectors=[detector_0, detector_1],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
)

cytometer = FlowCytometer(
    fluidics=fluidics,
    opto_electronics=opto_electronics,
    background_power=0.001 * units.milliwatt
)

processing_steps = [
    circuits.BaselineRestorator(window_size=10 * units.microsecond),
    circuits.BesselLowPass(cutoff=2 * units.megahertz, order=4, gain=2)
]

analog, event_df = cytometer.get_acquisition(
    run_time=2.5 * units.millisecond,
    processing_steps=processing_steps
)

analog.normalize_units(signal_units='max', time_units='max')

analog.plot()

# trigger = TriggeringSystem(
#     dataframe=acquisition,
#     trigger_detector_name='forward',
#     max_triggers=-1,
#     pre_buffer=20,
#     post_buffer=20,
#     digitizer=digitizer
# )

# analog_triggered = trigger.run(
#     scheme=Scheme.DYNAMIC,
#     threshold=10 * units.microvolt
# )

# analog_triggered.plot()
