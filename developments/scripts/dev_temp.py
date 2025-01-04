import numpy as np
from FlowCyPy import FlowCell
from FlowCyPy.units import meter, micrometer, millisecond, second, degree
from FlowCyPy import ScattererCollection
from FlowCyPy.units import particle, milliliter, nanometer, RIU, milliwatt, AU
from FlowCyPy import FlowCytometer
from FlowCyPy import Population, distribution
from FlowCyPy.detector import Detector
from FlowCyPy.units import ohm, megahertz, ampere, volt, kelvin, watt, microsecond, microvolt
from FlowCyPy import EventCorrelator, peak_locator
from FlowCyPy import GaussianBeam
from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = False

np.random.seed(3)

source = GaussianBeam(
    numerical_aperture=0.3 * AU,
    wavelength=988 * nanometer,
    optical_power=20 * milliwatt
)


flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * meter / second,
    flow_area=(10 * micrometer) ** 2,
    run_time=0.2 * millisecond
)


scatterer = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index of 1.33 (water)

lymphocyte = Population(
    name='lymphocyte',
    particle_count=200 * particle,
    size=distribution.Normal(mean=14_000 * nanometer, std_dev=1000 * nanometer),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.001 * RIU)
)


monocyte = Population(
    name='monocyte',
    particle_count=200 * particle,
    size=distribution.Normal(mean=23_000 * nanometer, std_dev=1000 * nanometer),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.001 * RIU)
)


scatterer.add_population(lymphocyte, monocyte)

flow_cell.initialize(scatterer_collection=scatterer)

scatterer.plot()


detector_0 = Detector(
    name='forward',
    phi_angle=0 * degree,
    numerical_aperture=.2 * AU,
    responsitivity=1 * ampere / watt,
    sampling_freq=60 * megahertz,
    noise_level=0.0 * volt,
    saturation_level=1600 * microvolt,
    resistance=150 * ohm,
    temperature=300 * kelvin,
)


detector_1 = Detector(
    name='side',
    phi_angle=90 * degree,
    numerical_aperture=.2 * AU,
    responsitivity=1 * ampere / watt,
    sampling_freq=60 * megahertz,
    noise_level=0.0 * volt,
    saturation_level=1600 * microvolt,
    resistance=150 * ohm,
    temperature=300 * kelvin,
)


cytometer = FlowCytometer(
    detectors=[detector_0, detector_1],
    flow_cell=flow_cell
)


cytometer.run_coupling_analysis()

cytometer.initialize_signal()

cytometer.simulate_pulse()

cytometer.plot.coupling_distribution(log_scale=True, equal_limits=True)
