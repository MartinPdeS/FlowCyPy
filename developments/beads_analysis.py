import numpy as np
from FlowCyPy import FlowCytometer, Analyzer, peak_finder, FlowCell, Source, Scatterer, distribution
from FlowCyPy.units import meter, micrometer, millisecond, second, degree, particle, milliliter, nanometer, RIU, milliwatt, AU, microsecond, millivolt, degree, ohm, megahertz, ampere, volt, kelvin, watt
from PyOptik import MaterialBank

np.random.seed(3)  # Ensure reproducibility


source = Source(numerical_aperture=0.1 * AU, wavelength=200 * nanometer, optical_power=100 * milliwatt)

ri = MaterialBank.polystyren.compute_refractive_index(source.wavelength)[0]


flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,
    flow_area=(10 * micrometer) ** 2,
    run_time=0.5 * millisecond
)

scatterer = Scatterer(medium_refractive_index=1.33 * RIU)

scatterer.add_population(
    name='100nm',
    concentration=1e9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=100 * nanometer, spread=500),
    refractive_index=distribution.Normal(mean=ri * RIU, std_dev=0.0001  * RIU)
)

scatterer.add_population(
    name='200nm',
    concentration=1e9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=200 * nanometer, spread=500),
    refractive_index=distribution.Normal(mean=ri * RIU, std_dev=0.0001  * RIU)
)

scatterer.add_population(
    name='300nm',
    concentration=1e9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=300 * nanometer, spread=500),
    refractive_index=distribution.Normal(mean=ri * RIU, std_dev=0.0001  * RIU)
)

scatterer.concentrations = 1e8 * particle / milliliter

scatterer.initialize(flow_cell=flow_cell)
scatterer.print_properties()
scatterer.plot()



cytometer = FlowCytometer(coupling_mechanism='mie', source=source, scatterer=scatterer)

cytometer.add_detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=100 * megahertz,          # Sampling frequency: 60 MHz
    saturation_level=100 * millivolt,        # Saturation level: 5000 mV (detector capacity)
    resistance=1 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,                # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

# Add side scatter detector
cytometer.add_detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=100 * megahertz,          # Sampling frequency: 60 MHz
    saturation_level=100 * millivolt,        # Saturation level: 5 V (detector capacity)
    resistance=1 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

cytometer.simulate_pulse()

# cytometer.plot()

algorithm = peak_finder.MovingAverage(
    threshold=0.05 * millivolt,
    window_size=1 * microsecond,
    min_peak_distance=1 * microsecond
)

analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

analyzer.run_analysis(compute_peak_area=False)

analyzer.plot_peak()

analyzer.get_coincidence(margin=1e-9 * microsecond)

analyzer.plot(log_plot=False)
