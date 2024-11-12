"""
Flow Cytometry Simulation with Two Populations: Density Plot of Scattering Intensities
=====================================================================================

This example demonstrates how to simulate a flow cytometry experiment using the FlowCyPy library.
The simulation includes two populations of particles, and we analyze pulse signals from two detectors
to generate a 2D density plot of scattering intensities.

Workflow Summary:
1. Flow Setup: Configure flow parameters and define particle size distributions.
2. Laser Source and Detector Setup: Define the laser source characteristics and configure the forward and side detectors.
3. Run the Experiment: Simulate the flow cytometry experiment.
4. Data Analysis: Analyze the pulse signals and generate a 2D density plot of the scattering intensities.
"""

# Step 1: Configuring Flow Parameters
import numpy as np
from FlowCyPy import FlowCell
from FlowCyPy.units import meter, micrometer, millisecond, second, degree

np.random.seed(3)  # Ensure reproducibility

# Define the flow cell parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 m/s
    flow_area=(10 * micrometer) ** 2,        # Flow area: 10 x 10 µm²
    run_time=0.5 * millisecond               # Simulation run time: 0.5 ms
)

# Step 2: Defining Particle Populations
from FlowCyPy import Scatterer, distribution
from FlowCyPy.units import particle, milliliter, nanometer, RIU

# Initialize scatterer with a medium refractive index
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index of 1.33 (water)

# Define populations with size distribution and refractive index
scatterer.add_population(
    name='EV',  # Population name: Extracellular Vesicles
    concentration=1e9 * particle / milliliter,  # Concentration: 1e9 particles/milliliter
    size=distribution.RosinRammler(
        characteristic_size=50 * nanometer,  # Characteristic size: 50 nm
        spread=4.5                           # Spread factor for the distribution
    ),
    refractive_index=distribution.Normal(
        mean=1.39 * RIU,   # Mean refractive index: 1.39
        std_dev=0.02 * RIU # Standard deviation: 0.02 refractive index units
    )
)

scatterer.add_population(
    name='LP',  # Population name: Liposomes
    concentration=1e9 * particle / milliliter,  # Concentration: 1e9 particles/milliliter
    size=distribution.RosinRammler(
        characteristic_size=200 * nanometer, # Characteristic size: 200 nm
        spread=4.5                           # Spread factor for the distribution
    ),
    refractive_index=distribution.Normal(
        mean=1.45 * RIU,   # Mean refractive index: 1.45
        std_dev=0.02 * RIU # Standard deviation: 0.02 refractive index units
    )
)

scatterer.add_population(
    name='Cells',  # Population name: Cells
    concentration=1e9 * particle / milliliter,  # Concentration: 1e9 particles/milliliter
    size=distribution.RosinRammler(
        characteristic_size=1000 * nanometer, # Characteristic size: 1000 nm
        spread=4.5                            # Spread factor for the distribution
    ),
    refractive_index=distribution.Normal(
        mean=1.43 * RIU,    # Mean refractive index: 1.43
        std_dev=0.02 * RIU  # Standard deviation: 0.02 refractive index units
    )
)

scatterer.initialize(flow_cell=flow_cell)  # Link populations to flow cell
scatterer.print_properties()               # Display population properties
scatterer.plot()                           # Visualize the population distributions

# %%
# Step 3: Laser Source Configuration
from FlowCyPy import Source
from FlowCyPy.units import milliwatt, nanometer, AU

# Set up the laser source parameters
source = Source(
    numerical_aperture=0.3 * AU,          # Laser numerical aperture: 0.3
    wavelength=200 * nanometer,           # Laser wavelength: 200 nm
    optical_power=20 * milliwatt          # Laser optical power: 20 mW
)

# Step 4: Simulating the Flow Cytometry Experiment
from FlowCyPy import FlowCytometer
from FlowCyPy.units import degree, ohm, megahertz, ampere, volt, kelvin, watt, millivolt

# Initialize the cytometer and configure detectors
cytometer = FlowCytometer(coupling_mechanism='mie', source=source, scatterer=scatterer)

# Add forward scatter detector
cytometer.add_detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=5000 * millivolt,      # Saturation level: 5000 mV (detector capacity)
    resistance=1 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

# Add side scatter detector
cytometer.add_detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
    noise_level=0.0 * volt,                 # Noise level: 0 V
    saturation_level=5 * volt,              # Saturation level: 5 V (detector capacity)
    resistance=1 * ohm,                     # Resistance: 1 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
    n_bins='14bit'                          # Discretization bins: 14-bit resolution
)

# Run the flow cytometry simulation
cytometer.simulate_pulse()

# Visualize the scatter signals from both detectors
cytometer.plot()

# %%
# Step 5: Analyzing Pulse Signals
from FlowCyPy import Analyzer, peak_finder
from FlowCyPy.units import microsecond, millivolt

# Configure peak finding algorithm
algorithm = peak_finder.MovingAverage(
    threshold=0.1 * millivolt,          # Signal threshold: 0.1 mV
    window_size=1 * microsecond,        # Moving average window size: 1 µs
    min_peak_distance=0.3 * microsecond # Minimum distance between peaks: 0.3 µs
)

# Initialize analyzer with the cytometer and algorithm
analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

# Run the pulse signal analysis
analyzer.run_analysis(compute_peak_area=False)

# Plot the detected peaks
analyzer.plot_peak()

# Step 6: Coincidence Data and 2D Density Plot
# Extract coincidence data within a defined margin
analyzer.get_coincidence(margin=1e-9 * microsecond)

# Generate and plot the 2D density plot of scattering intensities
analyzer.plot(log_plot=True)
