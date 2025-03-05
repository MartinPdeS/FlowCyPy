import numpy as np
from FlowCyPy import units
from FlowCyPy import GaussianBeam, FlowCell, ScattererCollection, Population
from FlowCyPy import distribution, Detector, SignalDigitizer, FlowCytometer, peak_locator
from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_dark_current_noise = False

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,
    wavelength=400 * units.nanometer,
    optical_power=200 * units.milliwatt
)


flow_cell = FlowCell(
    source=source,
    volume_flow=0.3 * units.microliter / units.second,
    flow_area=(10 * units.micrometer) ** 2,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

population_0 = Population(
    name='250 nm | 1.40 RI',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=250 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.40 * units.RIU, std_dev=0.002 * units.RIU)
)
population_1 = Population(
    name='200 nm | 1.42 RI',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=200 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.42 * units.RIU, std_dev=0.002 * units.RIU)
)
population_2 = Population(
    name='150 nm | 1.44 RI',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=5),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

scatterer_collection.add_population(population_0, population_1, population_2)

scatterer_collection.dilute(factor=16)

scatterer_collection.plot(sampling=5000, use_ratio=False)

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.4 * units.AU,
    cache_numerical_aperture=0.00 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    resistance=1500 * units.ohm,
    temperature=300 * units.kelvin
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=0.4 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
)

cytometer = FlowCytometer(
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)

# Run the flow cytometry simulation
cytometer.prepare_acquisition(run_time=0.2 * 10 * units.millisecond)
acquisition = cytometer.get_acquisition()

cytometer.scatterer_collection.dataframe.plot(x='RefractiveIndex', y='Diameter')

# acquisition.scatterer.plot(x='RefractiveIndex', y='Diameter')

# acquisition.scatterer.plot(x='forward', y='side', z='det_2')
acquisition.scatterer.plot(x='forward', y='side')
# acquisition.scatterer.plot(x='forward', y='side', z='Diameter')

acquisition.analog.plot()

triggered_acquisition = acquisition.run_triggering(
    threshold=10 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=2000,
    pre_buffer=64,
    post_buffer=64
)

triggered_acquisition.analog.plot()

peak_algorithm = peak_locator.BasicPeakLocator()

peaks = triggered_acquisition.detect_peaks(peak_algorithm)
# print(peaks)
peaks.plot(x='forward', y='side')
# peaks.plot(x='forward', y='side', z='det_2')



from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=3)

data = classifier.run(
    dataframe=peaks.unstack('Detector'),
    features=['Height'],
    detectors=['side', 'forward']
)

data.plot(feature='Height', x='forward', y='side')
