import numpy as np
from FlowCyPy import FlowCytometer, Analyzer, peak_finder, FlowCell, Source, Scatterer, distribution
from FlowCyPy.units import meter, micrometer, millisecond, second, degree, particle, milliliter, nanometer, RIU, milliwatt, AU, microsecond, millivolt, ohm, megahertz, ampere, kelvin, watt
from PyOptik import MaterialBank

np.random.seed(3)


source = Source(numerical_aperture=0.1 * AU, wavelength=480 * nanometer, optical_power=100 * milliwatt)

ri = MaterialBank.polystyren.compute_refractive_index(source.wavelength)


flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,
    flow_area=(10 * micrometer) ** 2,
    run_time=1 * millisecond
)

scatterer = Scatterer(medium_refractive_index=1.33 * RIU)


scatterer.add_population(
    name='LP',
    concentration=1e10 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=20 * nanometer, spread=5),
    refractive_index=distribution.Normal(mean=1.46 * RIU, std_dev=0.0001 * RIU)
)

scatterer.add_population(
    name='EV',
    concentration=1e8 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=300 * nanometer, spread=5),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.0001 * RIU)
)


# scatterer.concentrations = 2e8 * particle / milliliter

scatterer.initialize(flow_cell=flow_cell)
scatterer.print_properties()
# scatterer.plot()


cytometer = FlowCytometer(source=source, scatterer=scatterer)

cytometer.add_detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=10 * megahertz,          # Sampling frequency: 60 MHz
    # saturation_level=100 * millivolt,        # Saturation level: 5000 mV (detector capacity)
    resistance=10_000 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,                # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
    # include_noises=False
    # include_thermal_noise=False,
    # include_dark_current_noise=False
)

# Add side scatter detector
cytometer.add_detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=10 * megahertz,          # Sampling frequency: 60 MHz
    # saturation_level=100 * millivolt,        # Saturation level: 5 V (detector capacity)
    resistance=10_000 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
    # include_noises=False
    # include_thermal_noise=False,
    # include_dark_current_noise=False
    # background_cross_section=10 * meter * meter

)

cytometer.simulate_pulse()

cytometer.plot()

# algorithm = peak_finder.MovingAverage(
#     threshold=50 * millivolt,
#     window_size=1 * microsecond,
#     min_peak_distance=1 * microsecond
# )

# analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

# analyzer.run_analysis(compute_peak_area=False)

# analyzer.plot_peak()

# analyzer.get_coincidence(margin=1e-9 * microsecond)

# analyzer.plot(log_plot=False)
