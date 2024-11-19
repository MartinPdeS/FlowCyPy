"""
Flow Cytometry Simulation with Two Populations: Density Plot of Scattering Intensities
======================================================================================

This example demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation includes two populations of particles, and we analyze pulse signals from two detectors
to generate a 2D density plot of scattering intensities.

Workflow Summary:
1. Flow Setup: Configure flow parameters and define particle size distributions.
2. Laser GaussianBeam and Detector Setup: Define the laser source characteristics and configure the forward and side detectors.
3. Run the Experiment: Simulate the flow cytometry experiment.
4. Data Analysis: Analyze the pulse signals and generate a 2D density plot of the scattering intensities.
"""

# Step 1: Configuring Flow Parameters
import numpy as np
from FlowCyPy import FlowCell
from FlowCyPy.units import meter, micrometer, millisecond, second, degree
from FlowCyPy import Scatterer, distribution
from FlowCyPy.units import particle, milliliter, nanometer, RIU, milliwatt, AU
from FlowCyPy import FlowCytometer
from FlowCyPy.detector import Detector
from FlowCyPy.units import ohm, megahertz, ampere, volt, kelvin, watt, millivolt, microsecond, microvolt, nanovolt
from FlowCyPy import Analyzer, peak_finder
from FlowCyPy import GaussianBeam
from FlowCyPy import NoiseSetting
from FlowCyPy.populations_instances import LDL, HDL, Platelet, Exosome

NoiseSetting.include_noises = True

np.random.seed(3)  # Ensure reproducibility

# Define the flow cell parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 m/s
    flow_area=(10 * micrometer) ** 2,        # Flow area: 10 x 10 µm²
    run_time=0.3 * millisecond                # Simulation run time: 0.5 ms
)

spread = 10

# Step 2: Defining Particle Populations
# Initialize scatterer with a medium refractive index
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index of 1.33 (water)

scatterer.populations.append(Exosome)
scatterer.populations.append(LDL)
# scatterer.populations.append(HDL)
# scatterer.populations.append(Platelet)


scatterer.concentrations = 1e9 * particle / milliliter

HDL.concentration /= 3
LDL.concentration /= 3
# scatterer.dilute(1000)
# scatterer.concentrations = 1e7 * particle / milliliter
scatterer.initialize(flow_cell=flow_cell)  # Link populations to flow cell
scatterer.print_properties()               # Display population properties
# scatterer.plot()                           # Visualize the population distributions


# %%
# Step 3: Laser GaussianBeam Configuration
source = GaussianBeam(
    numerical_aperture=0.3 * AU,          # Laser numerical aperture: 0.3
    wavelength=488 * nanometer,           # Laser wavelength: 200 nm
    optical_power=50 * milliwatt          # Laser optical power: 20 mW
)

# Step 4: Simulating the Flow Cytometry Experiment
# Initialize the cytometer and configure detectors
# Add forward scatter detector
detector_0 = Detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=5 * millivolt,      # Saturation level: 5000 mV (detector capacity)
    resistance=50 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

# Add side scatter detector
detector_1 = Detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=5 * millivolt,              # Saturation level: 5 V (detector capacity)
    resistance=50 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    # n_bins='14bit'                          # Discretization bins: 14-bit resolution
)


cytometer = FlowCytometer(
    coupling_mechanism='mie',
    detectors=[detector_0, detector_1],
    source=source,
    scatterer=scatterer,
    background_power=0.00 * milliwatt
)

# Run the flow cytometry simulation
cytometer.simulate_pulse()

# Visualize the scatter signals from both detectors
# cytometer.plot()

# %%
# Step 5: Analyzing Pulse Signals
# Configure peak finding algorithm
algorithm = peak_finder.MovingAverage(
    threshold=0.06 * microvolt,           # Signal threshold: 0.1 mV
    window_size=1 * microsecond,         # Moving average window size: 1 µs
    min_peak_distance=0.3 * microsecond  # Minimum distance between peaks: 0.3 µs
)

# Initialize analyzer with the cytometer and algorithm
analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

# Run the pulse signal analysis
analyzer.run_analysis(compute_peak_area=False)

# Plot the detected peaks
# analyzer.plot_peak()

# Step 6: Coincidence Data and 2D Density Plot
# Extract coincidence data within a defined margin
analyzer.get_coincidence(margin=1e-9 * microsecond)

# Generate and plot the 2D density plot of scattering intensities
analyzer.plot(
    x_limits=(1 * nanovolt, 300 * microvolt),
    y_limits=(1 * nanovolt, 25 * microvolt),
    log_plot=False
    )