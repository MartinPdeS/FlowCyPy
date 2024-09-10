"""
Simulating and Analyzing Flow Cytometer Signals
===============================================

This script demonstrates how to simulate flow cytometer signals using the `FlowCytometer` class
and analyze the results using the `PulseAnalyzer` class from the `FlowCyPy` library.

Flow cytometers measure forward scatter (FSC) and side scatter (SSC) signals when particles pass through a laser beam,
providing information about particle size, complexity, and other characteristics.

Steps in this Workflow:
-----------------------
1. Define a particle size distribution using `ScattererDistribution`.
2. Simulate flow cytometer signals using `FlowCytometer`.
3. Analyze the forward scatter signal with `PulseAnalyzer` to extract features like peak height, width, and area.
4. Visualize the generated signals and display the extracted pulse features.
"""

# %%
# Step 1: Import necessary modules from FlowCyPy
from FlowCyPy import FlowCytometer, ScattererDistribution, Analyzer, Detector, Source, FlowCell
from FlowCyPy.distribution import NormalDistribution

# %%
# Example usage of the Flow class
flow = FlowCell(
    flow_speed=80e-6,       # 80 micrometers per second
    flow_area=1e-6,         # 1 square micrometer
    total_time=1.0,         # 1 second of flow
    scatterer_density=1e12  # 1e12 particles per cubic meter
)

# %%
# Step 2: Define the particle size distribution
# ---------------------------------------------
# Using a normal size distribution with a mean of 10 µm and a standard deviation of 0.8 µm.
# This defines the scatterers (particles) that will interact with the laser source.
size_distribution = NormalDistribution(
    mean=10e-6,         # Mean particle size: 10 µm
    std_dev=0.8e-8,     # Standard deviation of particle size: 0.8 µm
)

refractive_index_distribution_0 = NormalDistribution(
    scale_factor=1,
    mean=1.5,
    std_dev=0.01
)

refractive_index_distribution_1 = NormalDistribution(
    scale_factor=1,
    mean=1.7,
    std_dev=0.01
)


scatterer_distribution = ScattererDistribution(
    flow=flow,
    refractive_index=[refractive_index_distribution_0, refractive_index_distribution_1],        # Refractive index of the particles
    size=[size_distribution] # Normal distribution
)

scatterer_distribution.plot()

# Step 3: Define the light source
# -------------------------------
# Define a laser source that illuminates the particles. The wavelength and power of the laser are crucial
# for determining how the particles scatter light (e.g., Rayleigh scattering is wavelength-dependent).
source = Source(
    NA=0.3,                      # Numerical aperture of the focusing optics
    wavelength=1550e-9,          # Wavelength of the laser source: 1550 nm
    optical_power=200e-3,        # Optical power of the laser source: 200 milliwatt
)

# Step 4: Define the detector
# ---------------------------
# A detector is used to measure the scattered light. The detector's numerical aperture and responsitivity
# affect how much light it collects and converts to an electrical signal.
detector = Detector(
    phi_angle=90,              # Angle of the detector relative to the incident light beam
    NA=0.4,                      # Numerical aperture of the detector optics
    name='first detector',       # Name or identifier for this detector
    responsitivity=1,            # Responsitivity of the detector (efficiency of detecting scattered light)
    acquisition_frequency=1e4,   # Sampling frequency: 10,000 Hz
    noise_level=0e-2,            # Signal noise level: 1 millivolt
    baseline_shift=0.01,         # Baseline shift of the detector output
    saturation_level=1e30,       # Saturation level of the detector signal
    n_bins=1024                  # Discretization bins for digitizing the signal
)

# Step 5: Simulate Flow Cytometer Signals
# ---------------------------------------
# Create a FlowCytometer instance to simulate forward and side scatter (FSC/SSC) signals.
# The source, particle size distribution, and detector are passed in as parameters.
cytometer = FlowCytometer(
    coupling_mechanism='empirical',    # Use Rayleigh scattering for small particles
    source=source,                    # Laser source defined above
    scatterer_distribution=scatterer_distribution,  # Particle size distribution defined above
    detectors=[detector]              # List of detectors used in the simulation (only one here)
)

# Simulate the pulse signals generated as particles pass through the laser beam.
cytometer.simulate_pulse()

# Display the properties of the simulated cytometer, including laser power, flow speed, etc.
cytometer.print_properties()

# Visualize the simulated signals for FSC/SSC channels.
cytometer.plot()

"""
Summary:
--------
This script simulates flow cytometer signals, processes them to detect peaks in the forward scatter channel,
and extracts important features. The process is visualized through signal plots, and key properties are displayed.
"""
