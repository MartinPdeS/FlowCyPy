"""
WorkFlow
========

This script simulates flow cytometer signals using the `FlowCytometer` class and analyzes the results using
the `PulseAnalyzer` class from the FlowCyPy library. The signals generated (forward scatter and side scatter)
provide insights into the physical properties of particles passing through the laser beam.

Workflow:
---------
1. Define a particle size distribution using `ScattererCollection`.
2. Simulate flow cytometer signals using `FlowCytometer`.
3. Analyze the forward scatter signal with `PulseAnalyzer` to extract features like peak height, width, and area.
4. Visualize the generated signals and display the extracted pulse features.
"""

# %%
# Step 1: Import necessary modules from FlowCyPy
from FlowCyPy import FlowCytometer, ScattererCollection, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution
from FlowCyPy.population import Population
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy.units import nanometer, millisecond, meter, micrometer, second, RIU, milliliter, particle, watt, megahertz, degree, ampere, milliwatt, AU

# %%
# Step 2: Define the laser source
# -------------------------------
# Set up a laser source with a wavelength of 1550 nm, optical power of 200 mW, and a numerical aperture of 0.3.
source = GaussianBeam(
    numerical_aperture=0.3 * AU,  # Numerical aperture: 0.3
    wavelength=800 * nanometer,   # Laser wavelength: 800 nm
    optical_power=20 * milliwatt  # Optical power: 20 milliwatts
)

# %%
# Step 3: Define flow parameters
# ------------------------------
# Set the flow speed to 80 micrometers per second and a flow area of 1 square micrometer, with a total simulation time of 1 second.
flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 meters per second
    flow_area=(20 * micrometer) ** 2,        # Flow area: 10 x 10 micrometers
)

# %%
# Step 4: Define the particle size distribution
# ---------------------------------------------
# Use a normal size distribution with a mean size of 200 nanometers and a standard deviation of 10 nanometers.
# This represents the population of scatterers (particles) that will interact with the laser source.
ev_size = distribution.Normal(
    mean=200 * nanometer,       # Mean particle size: 200 nanometers
    std_dev=10 * nanometer      # Standard deviation: 10 nanometers
)

ev_ri = distribution.Normal(
    mean=1.39 * RIU,    # Mean refractive index: 1.39
    std_dev=0.01 * RIU  # Standard deviation: 0.01
)

ev = Population(
    particle_count=1.8e+9 * particle / milliliter,
    size=ev_size,               # Particle size distribution
    refractive_index=ev_ri,     # Refractive index distribution
    name='EV'                   # Name of the particle population: Extracellular Vesicles (EV)
)

scatterer_collection = ScattererCollection()

scatterer_collection.add_population(ev)


# Step 5: Define the detector
# ---------------------------
# The detector captures the scattered light. It is positioned at 90 degrees relative to the incident light beam
# and configured with a numerical aperture of 0.4 and responsitivity of 1.
signal_digitizer = SignalDigitizer(
    bit_depth=1024,
    saturation_levels='auto',
    sampling_freq=1 * megahertz,        # Sampling frequency: 1 MHz
)

detector_0 = Detector(
    phi_angle=90 * degree,              # Detector angle: 90 degrees (Side Scatter)
    numerical_aperture=0.4 * AU,        # Numerical aperture of the detector
    name='first detector',              # Detector name
    responsitivity=1 * ampere / watt,   # Responsitivity of the detector (light to signal conversion efficiency)
    signal_digitizer=signal_digitizer
)

detector_1 = Detector(
    phi_angle=0 * degree,               # Detector angle: 90 degrees (Sid e Scatter)
    numerical_aperture=0.4 * AU,        # Numerical aperture of the detector
    name='second detector',             # Detector name
    responsitivity=1 * ampere / watt,   # Responsitivity of the detector (light to signal conversion efficiency)
    signal_digitizer=signal_digitizer
)

# Step 6: Simulate Flow Cytometer Signals
# ---------------------------------------
# Create a FlowCytometer instance to simulate the signals generated as particles pass through the laser beam.
cytometer = FlowCytometer(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,                # Particle size distribution
    detectors=[detector_0, detector_1]  # List of detectors used in the simulation
)

# Run the flow cytometry simulation
experiment = cytometer.get_continous_acquisition(run_time=0.2 * millisecond)

# Visualize the scatter signals from both detectors
experiment.plot.signals()

experiment.logger.scatterer()
experiment.logger.detector()

"""
Summary:
--------
This script simulates flow cytometer signals, processes them to detect peaks in the forward scatter channel,
and extracts important features. The process is visualized through signal plots, and key properties are displayed.
"""
