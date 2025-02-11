from FlowCyPy import FlowCytometer, ScattererCollection, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution, Population
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import units

source = GaussianBeam(
    numerical_aperture=0.4 * units.AU,     # Numerical aperture: 0.4
    wavelength=1550 * units.nanometer,     # Wavelength: 1550 nm
    optical_power=200 * units.milliwatt    # Optical power: 2 mW
)

flow_cell = FlowCell(
    source=source,
    volume_flow=10 * units.microliter / units.second, # Flow speed: 10 microliter per second
    flow_area=(40 * units.micrometer) ** 2, # Flow area: 40 x 40 micrometers
)

LP_concentration = 40_000

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

population_0 = Population(
    name='EV',
    particle_count=1e+9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=200 * units.nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.42 * units.RIU, std_dev=0.05 * units.RIU)
)

population_1 = Population(
    name='LP',
    particle_count=LP_concentration * 1e+9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=100 * units.nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * units.RIU, std_dev=0.05 * units.RIU)
)

scatterer_collection.add_population(population_1, population_0)

scatterer_collection.dilute(100)

signal_digitizer = SignalDigitizer(
    bit_depth=1024,
    saturation_levels='auto',
    sampling_freq=10 * units.megahertz,           # Sampling frequency: 10 MHz
)

detector_fsc = Detector(
    name='FSC',                         # Forward Scatter detector
    numerical_aperture=1.2 * units.AU,        # Numerical aperture: 0.2
    phi_angle=0 * units.degree,               # Angle: 180 degrees for forward scatter
)

detector_ssc = Detector(
    name='SSC',                         # Side Scatter detector
    numerical_aperture=1.2 * units.AU,        # Numerical aperture: 0.2
    phi_angle=90 * units.degree,              # Angle: 90 degrees for side scatter
)

cytometer = FlowCytometer(
    signal_digitizer=signal_digitizer,
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,
    detectors=[detector_fsc, detector_ssc],  # Detectors: FSC and SSC
)

acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

acquisition.plot.signals(
    show_populations=['EV'],
    # save_filename=f'LP_{LP_concentration}.png'
)
