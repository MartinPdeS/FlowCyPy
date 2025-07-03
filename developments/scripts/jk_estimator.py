import numpy as np
from FlowCyPy import units
from FlowCyPy import NoiseSetting
from FlowCyPy import GaussianBeam
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy import ScattererCollection
from FlowCyPy.population import Sphere, CoreShell
from FlowCyPy.instances import Exosome, distribution
from FlowCyPy.detector import Detector
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier

from FlowCyPy import OptoElectronics, Fluidics, FlowCytometer
from FlowCyPy.calibration import JEstimator

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_source_noise = False
NoiseSetting.include_amplifier_noise = False
NoiseSetting.assume_perfect_hydrodynamic_focusing = True
NoiseSetting.assume_amplifier_bandwidth_is_infinite = True
NoiseSetting.assume_perfect_digitizer = True

np.random.seed(3)  # Ensure reproducibility

flow_cell = FlowCell(
    sample_volume_flow=80 * units.microliter / units.minute,
    sheath_volume_flow=1 * units.milliliter / units.minute,
    width=400 * units.micrometer,
    height=400 * units.micrometer,
    event_scheme='sequential-uniform'
)

scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell
)

source = GaussianBeam(
    numerical_aperture=0.2 * units.AU,
    wavelength=450 * units.nanometer,
    optical_power=0 * units.watt
)

digitizer = SignalDigitizer(
    bit_depth='16bit',
    saturation_levels=(0 * units.volt, 2 * units.volt),
    sampling_rate=60 * units.megahertz,
)

amplifier = TransimpedanceAmplifier(
    gain=10 * units.volt / units.ampere,
    bandwidth=60 * units.megahertz,
)

detector_0 = Detector(
    name='default',
    phi_angle=0 * units.degree,                  # Forward scatter angle
    numerical_aperture=0.2 * units.AU,
    cache_numerical_aperture=0.0 * units.AU,
    responsivity=1 * units.ampere / units.watt,
)

opto_electronics = OptoElectronics(
    detectors=[detector_0],
    digitizer=digitizer,
    source=source,
    amplifier=amplifier
)

flow_cytometer = FlowCytometer(
    opto_electronics=opto_electronics,
    fluidics=fluidics,
    background_power=source.optical_power * 0.00
)


j_estimator = JEstimator(debug_mode=False)

j_estimator.add_batch(
    illumination_powers=np.linspace(10, 280, 45) * units.milliwatt,
    bead_diameter=400 * units.nanometer,
    flow_cytometer=flow_cytometer,
    particle_count=50 * units.particle

)

j_estimator.plot()