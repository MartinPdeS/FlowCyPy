
import numpy as np
from FlowCyPy import FlowCytometer, ScattererCollection, EventCorrelator, Detector, GaussianBeam, FlowCell
from FlowCyPy import peak_locator
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz, microvolt
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU
from FlowCyPy import NoiseSetting
from FlowCyPy import Population, distribution
from FlowCyPy.population import Exosome, HDL

NoiseSetting.include_noises = True

np.random.seed(3)

source = GaussianBeam(
    numerical_aperture=0.3 * AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=100 * milliwatt             # Laser optical power: 10 milliwatts
)

flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
    run_time=.2 * millisecond             # Total simulation time: 0.3 milliseconds
)

scatterer = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

population_0 = Population(
    name='Pop 0',
    particle_count=100 * particle,
    size=distribution.RosinRammler(characteristic_size=100 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.02 * RIU)
)

scatterer.add_population(population_0)
# scatterer.add_population(hdl)


flow_cell.initialize(scatterer_collection=scatterer)

scatterer._log_properties()

source.print_properties()  # Print the laser source properties

detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 60 MHz
    saturation_level=0.04 * millivolt,          # Saturation level: 2 millivolts
    # n_bins='16bit',                          # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)

detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 60 MHz
    saturation_level=0.04 * millivolt,          # Saturation level: 2 millivolts
    # n_bins='16bit',                          # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)


detector_1.print_properties()  # Print the properties of the forward scatter detector

cytometer = FlowCytometer(                      # Laser source used in the experiment
    flow_cell=flow_cell,                     # Populations used in the experiment
    background_power=0.0 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

cytometer.run_coupling_analysis()

cytometer.initialize_signal()

cytometer.simulate_pulse()

cytometer.plot.signals()

algorithm = peak_locator.MovingAverage(
    threshold=10 * microvolt,       # Signal threshold: 0.1 mV
    window_size=1 * microsecond,         # Moving average window size: 1 µs
    min_peak_distance=0.1 * microsecond  # Minimum distance between peaks: 0.3 µs
)

detector_0.set_peak_locator(algorithm)
detector_1.set_peak_locator(algorithm)

cytometer.plot.signals(add_peak_locator=True)

analyzer = EventCorrelator(cytometer=cytometer)

analyzer.run_analysis(compute_peak_area=False)

analyzer.get_coincidence(margin=0.1 * microsecond)

analyzer.plot(log_plot=False)
