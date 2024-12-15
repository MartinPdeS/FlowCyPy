import numpy as np
from FlowCyPy import NoiseSetting

from FlowCyPy import (
    FlowCytometer, FlowCell, Detector, GaussianBeam, EventCorrelator,
    peak_locator, classifier, Scatterer, Population, distribution
)

from FlowCyPy.units import (
    particle, nanometer, RIU, milliwatt, AU, meter, micrometer, millisecond,
    second, degree, ohm, megahertz, ampere, volt, kelvin, watt, microsecond, microvolt
)

NoiseSetting.include_noises = False

np.random.seed(3)

flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,
    flow_area=(10 * micrometer) ** 2,
    run_time=0.4 * millisecond
)

scatterer = Scatterer(medium_refractive_index=1.33 * RIU)

for size in [150, 200, 250]:
    population = Population(
        name=f'Size: {size}nm',
        size=distribution.Normal(mean=size * nanometer, std_dev=10 * nanometer),
        refractive_index=distribution.Normal(mean=1.42 * RIU, std_dev=0.004 * RIU)
    )

    scatterer.add_population(population, particle_count=150 * particle)


scatterer.initialize(flow_cell=flow_cell)
# scatterer.distribute_time_linearly(sequential_population=True)
scatterer._log_properties()
scatterer.plot()

source = GaussianBeam(
    numerical_aperture=0.3 * AU,
    wavelength=488 * nanometer,
    optical_power=20 * milliwatt
)

detector_0 = Detector(
    name='forward',
    phi_angle=0 * degree,
    numerical_aperture=.2 * AU,
    responsitivity=1 * ampere / watt,
    sampling_freq=60 * megahertz,
    noise_level=0.0 * volt,
    # saturation_level=1600 * microvolt,
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
    # saturation_level=1600 * microvolt,
    resistance=150 * ohm,
    temperature=300 * kelvin,
)


cytometer = FlowCytometer(
    coupling_mechanism='mie',
    detectors=[detector_0, detector_1],
    source=source,
    scatterer=scatterer
)

cytometer.simulate_pulse()

cytometer.plot()

algorithm = peak_locator.MovingAverage(
    threshold=0.1 * microvolt,
    window_size=1 * microsecond,
    min_peak_distance=0.3 * microsecond
)

detector_0.set_peak_locator(algorithm)
detector_1.set_peak_locator(algorithm)

analyzer = EventCorrelator(cytometer=cytometer)

analyzer.run_analysis(compute_peak_area=False)

dataframe = analyzer.get_coincidence(margin=0.1 * microsecond)


clas = classifier.KmeansClassifier(dataframe)
clas.run(number_of_cluster=3, features=['Heights'])

analyzer.plot(log_plot=False)
