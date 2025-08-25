"""
Flow Cytometry Simulation [2 populations] Density Plot of Scattering Intensities
================================================================================

This example simulates a flow cytometer experiment using the FlowCyPy library,
analyzes pulse signals from two detectors, and generates a 2D density plot of the scattering intensities.

Steps:
1. Set flow parameters and particle size distributions.
2. Set up the laser GaussianBeam and detectors.
3. Simulate the flow cytometry experiment.
4. Analyze pulse signals and generate a 2D density plot.
"""

# Import necessary libraries and modules
import numpy as np
from FlowCyPy import FlowCytometer, Scatterer, Analyzer, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution
from FlowCyPy import peak_finder
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU

# Set random seed for reproducibility
# np.random.seed(30)

# Step 1: Define Flow Parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
    run_time=0.4 * millisecond             # Total simulation time: 0.3 milliseconds
)

# Step 2: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

# Add first population (Extracellular Vesicles)
scatterer.add_population(
    name='EV',  # Population name: Extracellular Vesicles (EV)
    concentration=1e+9 * particle / milliliter,  # Concentration: 1e9 particles per milliliter
    size=distribution.RosinRammler(
        characteristic_size=150 * nanometer,  # Characteristic size: 50 nanometers
        spread=10.5                           # Spread factor for size distribution
    ),
    refractive_index=distribution.Normal(
        mean=1.41 * RIU,    # Mean refractive index: 1.39
        std_dev=0.02 * RIU  # Standard deviation: 0.05 refractive index units
    )
)

# Add second population (Liposomes)
scatterer.add_population(
    name='LP',  # Population name: Liposomes (LP)
    concentration=5e+9 * particle / milliliter,  # Concentration: 1e9 particles per milliliter
    size=distribution.RosinRammler(
        characteristic_size=60 * nanometer,  # Characteristic size: 200 nanometers
        spread=1.5                           # Spread factor for size distribution
    ),
    refractive_index=distribution.Normal(
        mean=1.45 * RIU,    # Mean refractive index: 1.45
        std_dev=0.02 * RIU  # Standard deviation: 0.05 refractive index units
    )
)

# scatterer.concentrations = 1e+9 * particle / milliliter

# Initialize scatterer and link it to the flow cell
scatterer.initialize(flow_cell=flow_cell)

# Print and plot properties of the populations
scatterer.print_properties()
scatterer.plot(bandwidth_adjust=1)


# %%
# Step 4: Set up the Laser GaussianBeam
GaussianBeam = GaussianBeam(
    numerical_aperture=0.3 * AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=200 * milliwatt             # Laser optical power: 10 milliwatts
)

GaussianBeam.print_properties()  # Print the laser GaussianBeam properties

# Step 5: Configure Detectors
# Side scatter detector
detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=1.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=18 * megahertz,            # Sampling frequency: 60 MHz
    # saturation_level=3 * millivolt,          # Saturation level: 2 millivolts
    n_bins='16bit',                          # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)

# Forward scatter detector
detector_1 = Detector(
    name='forward',                          # Detector name: Forward scatter detector
    phi_angle=0 * degree,                    # Angle: 0 degrees (Forward Scatter)
    numerical_aperture=1.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=18 * megahertz,            # Sampling frequency: 60 MHz
    # saturation_level=3 * millivolt,          # Saturation level: 2 millivolts
    n_bins='16bit',                          # Number of bins: 14-bit resolution
    resistance=50 * ohm,                     # Detector resistance: 50 ohms
    dark_current=0.1 * milliampere,          # Dark current: 0.1 milliamps
    temperature=300 * kelvin                 # Operating temperature: 300 Kelvin
)


detector_1.print_properties()  # Print the properties of the forward scatter detector

# Step 6: Simulate Flow Cytometry Experiment
cytometer = FlowCytometer(
    coupling_mechanism='mie',                # Scattering mechanism: Mie scattering
    GaussianBeam=GaussianBeam,                           # Laser GaussianBeam used in the experiment
    scatterer=scatterer,                     # Populations used in the experiment
    background_power=0.02 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the simulation of pulse signals
cytometer.simulate_pulse()

# Plot the results from both detectors
cytometer.plot()

# %%
# Step 7: Analyze Pulse Signals
algorithm = peak_finder.MovingAverage(
    threshold=0.001 * millivolt,              # Peak detection threshold: 0.03 millivolts
    window_size=10 * microsecond,             # Moving average window size: 1 microsecond
    min_peak_distance=1 * microsecond      # Minimum distance between peaks: 0.2 microseconds
)

analyzer = Analyzer(cytometer=cytometer, algorithm=algorithm)

# Run the pulse signal analysis without computing peak area
analyzer.run_analysis(compute_peak_area=False)

# Plot the analyzed pulse signals
analyzer.plot_peak()

# %%
# Step 8: Extract and Plot Coincidence Data
analyzer.get_coincidence(margin=0.1 * microsecond)  # Coincidence data with 0.1 µs margin

# Plot the 2D density plot of scattering intensities
analyzer.plot(log_plot=False)  # Plot with a linear scale (log_plot=False)
