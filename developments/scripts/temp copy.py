import numpy as np
from FlowCyPy import units
from FlowCyPy import FlowCytometer, circuits
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import GaussianBeam
from FlowCyPy import ScattererCollection
from FlowCyPy.population import Exosome, Sphere, distribution
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import TransimpedanceAmplifier

source = GaussianBeam(
    numerical_aperture=0.1 * units.AU,           # Numerical aperture
    wavelength=450 * units.nanometer,           # Wavelength
    optical_power=200 * units.milliwatt          # Optical power
)

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=100 * units.micrometer,
    height=100 * units.micrometer,
)


scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

exosome = Exosome(particle_count=5e9 * units.particle / units.milliliter)

custom_population = Sphere(
    name='Pop 0',
    particle_count=5e9 * units.particle / units.milliliter,
    diameter=distribution.RosinRammler(characteristic_property=150 * units.nanometer, spread=3000),
    refractive_index=distribution.Normal(mean=1.44 * units.RIU, std_dev=0.002 * units.RIU)
)

scatterer_collection.add_population(exosome, custom_population)

scatterer_collection.dilute(factor=8)

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
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * units.degree,                 # Side scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)


detector_2 = Detector(
    name='det_2',
    phi_angle=30 * units.degree,                 # Side scatter angle
    numerical_aperture=0.3 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)


transimpedance_amplifier = TransimpedanceAmplifier(
    gain=100 * units.volt / units.ampere,
    bandwidth = 100 * units.megahertz
)

cytometer = FlowCytometer(
    source=source,
    transimpedance_amplifier=transimpedance_amplifier,
    scatterer_collection=scatterer_collection,
    signal_digitizer=signal_digitizer,
    detectors=[detector_0, detector_1, detector_2],
    flow_cell=flow_cell,
    background_power=0.001 * units.milliwatt
)

processing_steps = [
    circuits.BaselineRestorator(window_size=1000 * units.microsecond),
    circuits.BesselLowPass(cutoff=3 * units.megahertz, order=4, gain=2)
]

cytometer.prepare_acquisition(run_time=0.01 * units.millisecond)
acquisition = cytometer.get_acquisition(processing_steps=processing_steps)
acquisition.analog.plot()

# cpp code: 0.0007882118225097656
# numpy code: 0.0002582073211669922



# cpp code: 2.5987625122070312e-05
# numpy code: 0.0002808570861816406