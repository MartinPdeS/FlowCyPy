import numpy as np
from FlowCyPy import NoiseSetting

from FlowCyPy import (
    FlowCytometer, FlowCell, Detector, GaussianBeam, EventCorrelator,
    peak_locator, classifier, Scatterer, Population, distribution
)

from FlowCyPy.units import (
    particle, nanometer, RIU, milliwatt, AU, meter, micrometer, millisecond, milliliter,
    second, degree, ohm, megahertz, ampere, volt, kelvin, watt, microsecond, microvolt
)

from FlowCyPy.plottings import MetricPlotter

NoiseSetting.include_noises = False
NoiseSetting.include_shot_noise = False
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

np.random.seed(3)

flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,
    flow_area=(10 * micrometer) ** 2,
    run_time=0.2 * millisecond
)

scatterer = Scatterer(medium_refractive_index=1.33 * RIU)


combinations = [
    # (50, 1.42),
    (150, 1.42),
    # (250, 1.45)
]


particule_number = 40
for size, ri in combinations:
    population = Population(
        name=f'Size: {size}nm',
        size=distribution.Normal(mean=size * nanometer, std_dev=size/20000 * nanometer),
        refractive_index=distribution.Normal(mean=ri * RIU, std_dev=0.00001 * RIU)
    )

    # scatterer.add_population(population, particle_count=particule_number * particle)
    scatterer.add_population(population, particle_count=2 * particle)


scatterer.initialize(flow_cell=flow_cell)

scatterer.distribute_time_linearly(sequential_population=True)

scatterer._log_properties()
# scatterer.plot()

source = GaussianBeam(
    numerical_aperture=0.3 * AU,
    wavelength=488 * nanometer,
    optical_power=200 * milliwatt
)



detector_0 = Detector(
    name='forward',
    phi_angle=0 * degree,
    numerical_aperture=.2 * AU,
    responsitivity=1 * ampere / watt,
    sampling_freq=60 * megahertz,
    # noise_level=0.0 * volt,
    # saturation_level=1600 * microvolt,
    resistance=1500 * ohm,
    temperature=30 * kelvin,
)

detector_1 = Detector(
    name='side',
    phi_angle=90 * degree,
    numerical_aperture=1.2 * AU,
    responsitivity=1 * ampere / watt,
    sampling_freq=60 * megahertz,
    # noise_level=0.0 * volt,
    # saturation_level=1600 * microvolt,
    resistance=1500 * ohm,
    temperature=30 * kelvin,
)


cytometer = FlowCytometer(
    detectors=[detector_0, detector_1],
    source=source,
    scatterer=scatterer
)

cytometer.simulate_pulse()


print(scatterer.dataframe)

# cytometer.plot()

# algorithm = peak_locator.MovingAverage(
#     threshold=0.001 * microvolt,
#     window_size=1 * microsecond,
#     min_peak_distance=0.3 * microsecond
# )

# detector_0.set_peak_locator(algorithm)
# detector_1.set_peak_locator(algorithm)

# analyzer = EventCorrelator(cytometer=cytometer)

# analyzer.run_analysis(compute_peak_area=False)

# dataframe = analyzer.get_coincidence(margin=0.1 * microsecond)


# # clas = classifier.KmeansClassifier(dataframe)
# # clas.run(number_of_cluster=3, features=['Heights'])

# clas = classifier.RangeClassifier(dataframe)

# clas.run(
#     ranges={
#         'Population 0': (0, particule_number),
#         'Population 1': (particule_number, 2 * particule_number),
#         'Population 2': (2 * particule_number, 3 * particule_number)}
# )

# print(dataframe)

# plotter = MetricPlotter(
#     detector_names=['forward', 'side'],
#     coincidence_dataframe=dataframe,
# )

# plotter.plot(
#     feature='Heights',
#     show=True,
#     log_plot=False,
#     equal_axes=False
# )

