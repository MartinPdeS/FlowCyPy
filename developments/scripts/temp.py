import numpy as np
from FlowCyPy import Detector, FlowCytometer, ScattererCollection, FlowCell, units, NoiseSetting, GaussianBeam, SignalDigitizer
from FlowCyPy.population import Exosome, Population, distribution

NoiseSetting.include_noises = True

source = GaussianBeam(
    numerical_aperture=0.3 * units.AU,
    wavelength=200 * units.nanometer,
    optical_power=20 * units.milliwatt
)

flow_cell = FlowCell(
    source=source,
    volume_flow=0.1 * units.microliter / units.second,
    flow_area=(10 * units.micrometer) ** 2,
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Population(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=150 * units.nanometer, spread=30),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

scatterer_collection.add_population(exosome, custom_population)

scatterer_collection.dilute(factor=4)

# scatterer_collection.plot()

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_freq=60 * units.megahertz,
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * units.degree,
    numerical_aperture=1.2 * units.AU,
    responsitivity=1 * units.ampere / units.watt,
    resistance=50 * units.ohm,
    temperature=300 * units.kelvin
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,
    numerical_aperture=1.2 * units.AU,
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

acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

# acquisition.scatterer.plot(x='side', y='forward')

# acquisition.analog.plot()

triggered_acquisition = acquisition.run_triggering(
    threshold=1.0 * units.millivolt,
    trigger_detector_name='forward',
    max_triggers=35,
    pre_buffer=63,
    post_buffer=64
)

# triggered_acquisition.analog.plot()

from FlowCyPy.triggered_acquisition import scipy_peak_detector

peaks = triggered_acquisition.detect_peaks(peak_detection_func=scipy_peak_detector)

peaks.plot(
    feature='Height',
    x_detector='side',
    y_detector='forward'
)
