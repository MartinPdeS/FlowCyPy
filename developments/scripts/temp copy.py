
import numpy as np
from FlowCyPy import units
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import NoiseSetting
from FlowCyPy import peak_locator
from FlowCyPy import FlowCytometer
NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_RIN_noise = False


np.random.seed(3)  # Ensure reproducibility



source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,           # Numerical aperture
    wavelength=450 * units.nanometer,           # Wavelength
    optical_power=200 * units.milliwatt          # Optical power
)



flow_cell = FlowCell(
    sample_volume_flow=1 * units.microliter / units.second,
    sheath_volume_flow=6 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
)

from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Sphere, distribution

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

scatterer_collection.add_population(exosome, custom_population)

scatterer_collection.dilute(factor=1)

from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_rate=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin,
)

cytometer = FlowCytometer(
    source=source,
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell,
    background_power=0.1 * units.milliwatt
)

# Run the flow cytometry simulation
cytometer.prepare_acquisition(run_time=0.02 * units.millisecond)
acquisition = cytometer.get_acquisition()
acquisition.analog.plot()

triggered_acquisition = acquisition.run_triggering(
    threshold=5.25 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=64,
    post_buffer=64
)




peak_algorithm = peak_locator.SlidingWindowPeakLocator(window_size=10, compute_width=True)

peaks = triggered_acquisition.detect_peaks(peak_algorithm)




from FlowCyPy.classifier import KmeansClassifier

classifier = KmeansClassifier(number_of_cluster=2)

data = classifier.run(
    dataframe=peaks.unstack('Detector'),
    features=['Height'],
    detectors=['side', 'forward']
)

_ = data.plot(feature='Height', x='side', y='forward')