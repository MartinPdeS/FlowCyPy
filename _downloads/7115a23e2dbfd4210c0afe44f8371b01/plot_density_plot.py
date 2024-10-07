"""
Flow Cytometry Simulation [2 populations] Density Plot of Scattering Intensities
================================================================================

This example simulates a flow cytometer experiment using the FlowCyPy library,
analyzes pulse signals from two detectors, and generates a 2D density plot of the scattering intensities.

Steps:
1. Set flow parameters and particle size distributions.
2. Set up the laser source and detectors.
3. Simulate the flow cytometry experiment.
4. Analyze pulse signals and generate a 2D density plot.
"""

# Import necessary libraries and modules
import numpy as np
from FlowCyPy import FlowCytometer, Scatterer, Analyzer, Detector, Source, FlowCell
from FlowCyPy import distribution
from FlowCyPy import peak_finder
from FlowCyPy.units import (
    microsecond, micrometer, meter, refractive_index_unit, milliliter, second, millivolt,
    millisecond, nanometer, milliwatt, degree, volt, watt, megahertz, particle, ampere
)

# Set random seed for reproducibility
np.random.seed(3)

# Step 1: Define Flow Parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,        # Flow area: 10 x 10 micrometers
    total_time=0.5 * millisecond             # Total simulation time: 0.3 milliseconds
)

# %%
# Step 2: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = Scatterer(medium_refractive_index=1.33)

scatterer.add_population(
    name='EV',
    concentration=1e+9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=50 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * refractive_index_unit, std_dev=0.05 * refractive_index_unit)
)


scatterer.add_population(
    name='LP',
    concentration=1e+9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=200 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.45 * refractive_index_unit, std_dev=0.05 * refractive_index_unit)
)

scatterer.initialize(flow_cell=flow_cell)

scatterer.print_properties()

# Plot scatterer distribution
scatterer.plot()

# %%
# Step 4: Set up the Laser Source
source = Source(
    numerical_aperture=0.3,                  # Numerical aperture of the laser: 0.2
    wavelength=200 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=100 * milliwatt            # Laser optical power: 20 milliwatts
)

# Step 5: Configure Detectors
detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=1.2,                  # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 volt per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 10 MHz
    noise_level=0.0 * volt,                  # Noise level: 0 volts
    saturation_level=0.1 * volt,             # Saturation level: 100 volts
    n_bins='14bit'                           # Discretization bins: 14-bit resolution
)

detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=180 * degree,                  # Angle: 180 degrees (Forward Scatter)
    numerical_aperture=1.2,                  # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 volt per watt
    sampling_freq=60 * megahertz,            # Sampling frequency: 10 MHz
    noise_level=0.0 * volt,                  # Noise level: 0 volts
    saturation_level=100 * millivolt,        # Saturation level: 100 volts
    n_bins='14bit'                           # Discretization bins: 14-bit resolution
)

# Step 6: Simulate Flow Cytometry Experiment
cytometer = FlowCytometer(
    coupling_mechanism='mie',                # Use Mie scattering for particle simulation
    source=source,                           # Laser source
    scatterer=scatterer, # Particle size and refractive index distribution
    detectors=[detector_0, detector_1]       # Two detectors: Side scatter and Forward scatter
)

# Run the simulation
cytometer.simulate_pulse()

# Plot the results of scattering signals from both detectors
# cytometer.plot()

# %%
# Step 7: Analyze Pulse Signals
algorithm = peak_finder.MovingAverage(
    threshold=0.1 * millivolt,
    window_size=1 * microsecond,
    min_peak_distance=0.3 * microsecond

)

analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

# Analyze pulse signals
analyzer.run_analysis(compute_peak_area=False)  # Analysis with no peak area computation

# Plot the analyzed pulse signals
analyzer.plot_peak()

# %%
# Step 8: Extract and Plot Coincidence Data
analyzer.get_coincidence(margin=1e-9 * microsecond)

# Plot the 2D density plot
analyzer.plot(log_plot=True)
