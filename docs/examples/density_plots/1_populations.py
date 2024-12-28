"""
Flow Cytometry Simulation with One Populations: Density Plot of Scattering Intensities
======================================================================================

This example demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation includes one populations of particles, and we analyze pulse signals from two detectors
to generate a 2D density plot of scattering intensities.

Workflow Summary:

1. Flow Setup: Configure flow parameters and define particle size distributions.
2. Laser GaussianBeam and Detector Setup: Define the laser source characteristics and configure the forward and side detectors.
3. Run the Experiment: Simulate the flow cytometry experiment.
4. Data Analysis: Analyze the pulse signals and generate a 2D density plot of the scattering intensities.
"""

# Step 1: Configuring Flow Parameters
# -----------------------------------
import numpy as np
from FlowCyPy import FlowCell
from FlowCyPy.units import meter, micrometer, millisecond, second, degree
from FlowCyPy import Scatterer
from FlowCyPy.units import particle, milliliter, nanometer, RIU, AU, milliwatt
from FlowCyPy import FlowCytometer
from FlowCyPy.units import ohm, megahertz, ampere, volt, kelvin, watt, microvolt, microsecond
from FlowCyPy.detector import Detector
from FlowCyPy import EventCorrelator, peak_locator
from FlowCyPy import GaussianBeam
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome


NoiseSetting.include_noises = False

np.random.seed(3)  # Ensure reproducibility

# Define the flow cell parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 m/s
    flow_area=(10 * micrometer) ** 2,        # Flow area: 10 x 10 µm²
    run_time=0.1 * millisecond               # Simulation run time: 0.5 ms
)

# Initialize scatterer with a medium refractive index
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index of 1.33 (water)

# Define populations with size distribution and refractive index
scatterer.add_population(Exosome, particle_count=5e9 * particle / milliliter)

scatterer.initialize(flow_cell=flow_cell)  # Link populations to flow cell
scatterer._log_properties()               # Display population properties
scatterer.plot()                         # Visualize the population distributions

# Set up the laser source parameters
source = GaussianBeam(
    numerical_aperture=0.3 * AU,          # Laser numerical aperture: 0.3
    wavelength=200 * nanometer,           # Laser wavelength: 200 nm
    optical_power=20 * milliwatt          # Laser optical power: 20 mW
)

# Add forward scatter detector
detector_0 = Detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=10000 * microvolt,     # Saturation level: 10 mV (detector capacity)
    resistance=50 * ohm,                    # Resistance: 50 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

# Add side scatter detector
detector_1 = Detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=10000 * microvolt,     # Saturation level: 10 mV (detector capacity)
    resistance=50 * ohm,                    # Resistance: 50 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    n_bins='14bit'                          # Discretization bins: 14-bit resolution
)


# Step 4: Simulating the Flow Cytometry Experiment
# ------------------------------------------------
cytometer = FlowCytometer(
    coupling_mechanism='mie',
    source=source,
    detectors=[detector_0, detector_1],
    scatterer=scatterer,
    background_power=0.001 * milliwatt
)


# Run the flow cytometry simulation
cytometer.simulate_pulse()

# Visualize the scatter signals from both detectors
cytometer.plot()

# %%
# Step 5: Analyzing Pulse Signals
# -------------------------------
algorithm = peak_locator.MovingAverage(
    threshold=10 * microvolt,           # Signal threshold: 0.1 mV
    window_size=1 * microsecond,         # Moving average window size: 1 µs
    min_peak_distance=0.3 * microsecond  # Minimum distance between peaks: 0.3 µs
)

detector_0.set_peak_locator(algorithm)
detector_1.set_peak_locator(algorithm)

# Initialize analyzer with the cytometer and algorithm
analyzer = EventCorrelator(cytometer=cytometer)

# Run the pulse signal analysis
analyzer.run_analysis(compute_peak_area=False)

# %%
# Step 6: Coincidence Data and 2D Density Plot
# --------------------------------------------
# Extract coincidence data within a defined margin
analyzer.get_coincidence(margin=1e-9 * microsecond)

# Generate and plot the 2D density plot of scattering intensities
analyzer.plot(log_plot=False)
