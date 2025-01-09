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
from FlowCyPy import ScattererCollection
from FlowCyPy.units import particle, milliliter, nanometer, RIU, AU, milliwatt
from FlowCyPy import FlowCytometer
from FlowCyPy.units import ohm, megahertz, ampere, kelvin, watt, microvolt, microsecond
from FlowCyPy.detector import Detector
from FlowCyPy import EventCorrelator, peak_locator
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import GaussianBeam
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome


NoiseSetting.include_noises = False

np.random.seed(3)  # Ensure reproducibility

# Set up the laser source parameters
source = GaussianBeam(
    numerical_aperture=0.3 * AU,          # Laser numerical aperture: 0.3
    wavelength=200 * nanometer,           # Laser wavelength: 200 nm
    optical_power=20 * milliwatt          # Laser optical power: 20 mW
)

# Define the flow cell parameters
flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 m/s
    flow_area=(10 * micrometer) ** 2,        # Flow area: 10 x 10 µm²
)

# Initialize scatterer with a medium refractive index
scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index of 1.33 (water)

# Define populations with size distribution and refractive index
exosome = Exosome(particle_count=5e9 * particle / milliliter)
scatterer_collection.add_population(exosome)

scatterer_collection.plot()

# %%
# Add forward scatter detector
signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels=16_000 * microvolt,
    sampling_freq=60 * megahertz,           # Sampling frequency: 60 MHz
)

detector_0 = Detector(
    name='forward',                         # Detector name: Forward scatter
    phi_angle=0 * degree,                   # Detector angle: 0 degrees (forward scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    signal_digitizer=signal_digitizer,
    resistance=50 * ohm,                    # Resistance: 50 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
)

# Add side scatter detector
detector_1 = Detector(
    name='side',                            # Detector name: Side scatter
    phi_angle=90 * degree,                  # Detector angle: 90 degrees (side scatter)
    numerical_aperture=1.2 * AU,            # Detector numerical aperture: 1.2
    responsitivity=1 * ampere / watt,       # Responsitivity: 1 A/W (detector response)
    signal_digitizer=signal_digitizer,
    resistance=50 * ohm,                    # Resistance: 50 ohm
    temperature=300 * kelvin,               # Operating temperature: 300 K (room temperature)
)


# Step 4: Simulating the Flow Cytometry Experiment
# ------------------------------------------------
cytometer = FlowCytometer(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,
    detectors=[detector_0, detector_1],
    background_power=0.001 * milliwatt
)


# Run the flow cytometry simulation
experiment = cytometer.get_continous_acquisition(run_time=0.2 * millisecond)

# Visualize the scatter signals from both detectors
experiment.plot.signals()

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
