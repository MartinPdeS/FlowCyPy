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
from FlowCyPy import FlowCytometer, Scatterer, EventCorrelator, Detector, GaussianBeam, FlowCell
from FlowCyPy import peak_locator
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz, microvolt
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome, HDL

NoiseSetting.include_noises = False

# Set random seed for reproducibility
np.random.seed(3)

# Step 1: Define Flow Parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
    run_time=.2 * millisecond             # Total simulation time: 0.3 milliseconds
)

# Step 2: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

scatterer.add_population(Exosome, particle_count=3e+8 * particle / milliliter)
scatterer.add_population(HDL, particle_count=3e+8 * particle / milliliter)

# Initialize scatterer and link it to the flow cell
scatterer.initialize(flow_cell=flow_cell)

# Print and plot properties of the populations
scatterer._log_properties()
scatterer.plot()

# %%
# Step 4: Set up the Laser GaussianBeam
source = GaussianBeam(
    numerical_aperture=0.3 * AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=100 * milliwatt             # Laser optical power: 10 milliwatts
)

source.print_properties()  # Print the laser source properties

# Step 5: Configure Detectors
# Side scatter detector
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

# Forward scatter detector
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

# Step 6: Simulate Flow Cytometry Experiment
cytometer = FlowCytometer(
    coupling_mechanism='mie',                # Scattering mechanism: Mie scattering
    source=source,                           # Laser source used in the experiment
    scatterer=scatterer,                     # Populations used in the experiment
    background_power=0.0 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the simulation of pulse signals
cytometer.simulate_pulse()

# Plot the results from both detectors
cytometer.plot()

# %%
# Step 5: Analyzing Pulse Signals
algorithm = peak_locator.MovingAverage(
    threshold=0.1e-20 * microvolt,       # Signal threshold: 0.1 mV
    window_size=1 * microsecond,         # Moving average window size: 1 µs
    min_peak_distance=0.1 * microsecond  # Minimum distance between peaks: 0.3 µs
)

detector_0.set_peak_locator(algorithm)
detector_1.set_peak_locator(algorithm)

cytometer.plot(add_peak_locator=True)

analyzer = EventCorrelator(cytometer=cytometer)

# Run the pulse signal analysis without computing peak area
analyzer.run_analysis(compute_peak_area=False)

# %%
# Step 8: Extract and Plot Coincidence Data
analyzer.get_coincidence(margin=0.1 * microsecond)  # Coincidence data with 0.1 µs margin

# Plot the 2D density plot of scattering intensities
analyzer.plot(log_plot=False)  # Plot with a linear scale (log_plot=False)
