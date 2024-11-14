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
from FlowCyPy import FlowCytometer, Scatterer, Analyzer, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution
from FlowCyPy import peak_finder
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU

# Set random seed for reproducibility
np.random.seed(3)

# Step 1: Define Flow Parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
    run_time=0.4 * millisecond             # Total simulation time: 0.3 milliseconds
)

# Step 2: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

scatterer.concentrations = 1e+9 / 30 * particle / milliliter

# Initialize scatterer and link it to the flow cell
scatterer.initialize(flow_cell=flow_cell)

# Print and plot properties of the populations
scatterer.print_properties()
# scatterer.plot(bandwidth_adjust=0.01)


# %%
# Step 4: Set up the Laser GaussianBeam
source = GaussianBeam(
    numerical_aperture=0.3 * AU,             # Numerical aperture of the laser: 0.3
    wavelength=488 * nanometer,              # Laser wavelength: 800 nanometers
    optical_power=200 * milliwatt             # Laser optical power: 10 milliwatts
)

source.print_properties()  # Print the laser source properties

# Step 5: Configure Detectors
# Side scatter detector
detector_0 = Detector(
    name='side',                             # Detector name: Side scatter detector
    phi_angle=90 * degree,                   # Angle: 90 degrees (Side Scatter)
    numerical_aperture=1.2 * AU,             # Numerical aperture: 1.2
    responsitivity=1 * ampere / watt,        # Responsitivity: 1 ampere per watt
    sampling_freq=18 * megahertz,            # Sampling frequency: 60 MHz
    saturation_level=3 * millivolt,          # Saturation level: 2 millivolts
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
    saturation_level=3 * millivolt,          # Saturation level: 2 millivolts
    n_bins='16bit',                          # Number of bins: 14-bit resolution
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
    background_power=0.02 * milliwatt,
    detectors=[detector_0, detector_1]       # List of detectors: Side scatter and Forward scatter
)

# Run the simulation of pulse signals
cytometer.simulate_pulse()

print(detector_0.dataframe.RawSignal)

cytometer.plot()
