"""
Simulating Flow Cytometer Signals with Rayleigh Scattering
==========================================================

This example demonstrates how to simulate signals from a flow cytometer using
the `FlowCytometer` class in combination with two detectors: Forward Scatter (FSC) and Side Scatter (SSC).

Flow cytometers generate signals (e.g., forward scatter and side scatter) when
particles pass through a laser beam. These signals provide valuable information about
the size, complexity, and other properties of the particles passing through the flow.

In this simulation, we use Rayleigh scattering to model how particles interact with
the laser beam. We simulate particles with a uniform size distribution and analyze
their scattering properties.
"""

# Step 1: Import the necessary libraries
# --------------------------------------
from FlowCyPy import FlowCytometer, ScattererDistribution, Detector, Source, FlowCell
from FlowCyPy.distribution import NormalDistribution

# Example usage of the Flow class
flow = FlowCell(
    flow_speed=80e-6,  # 80 micrometers per second
    flow_area=1e-6,  # 1 square micrometer
    total_time=1.0,  # 1 second of flow
    scatterer_density=5e11  # 1e12 particles per cubic meter
)

flow.print_properties()

# Step 2: Define the particle size distribution
# ---------------------------------------------
# In this case, we're using a uniform particle size distribution. Particles are modeled
# with a refractive index of 1.5, a mean size of 1 µm, and a standard deviation of 0.1 µm.
# The total particle density is 4 x 10^10 particles per cubic meter.
# %%
size_distribution = NormalDistribution(
    mean=10e-6,         # Mean particle size: 10 µm
    std_dev=0.8e-8,     # Standard deviation of particle size: 0.8 µm
)

refractive_index_distribution = NormalDistribution(
    scale_factor=1,
    mean=1.5,
    std_dev=0.1
)


scatterer_distribution = ScattererDistribution(
    flow=flow,
    refractive_index=[refractive_index_distribution],         # Refractive index of the particles
    size=[size_distribution]  # Normal distribution of particle sizes
)

# %%
scatterer_distribution.plot()

scatterer_distribution.print_properties()

# Step 3: Define the light source
# -------------------------------
# The light source used for the simulation is a laser with a wavelength of 1550 nm
# and an optical power of 1 mW. The laser's focusing optics are characterized by a
# numerical aperture (NA) of 0.4.
source = Source(
    NA=0.4,                       # Numerical aperture of the source
    wavelength=1550e-9,           # Wavelength of the laser source: 1550 nm
    optical_power=20e-3            # Optical power of the laser: 2 mW
)

# Step 4: Define two detectors
# ----------------------------
# The first detector (FSC) is for Forward Scatter, and the second detector (SSC) is for
# Side Scatter. Each detector has different numerical apertures and settings. These detectors
# will capture the light scattered by the particles.
detector_fsc = Detector(
    name='FSC',                   # Forward Scatter (FSC) detector
    NA=0.2,                       # Numerical aperture of the detector
    phi_angle=180,              # Angle relative to the light beam
    acquisition_frequency=1e3,    # Acquisition frequency: 1000 Hz
    noise_level=1e-3,             # Noise floor of 0.0001 volt
    saturation_level=10,          # Maximum signal before saturation
    baseline_shift=0.0,           # No baseline shift
    n_bins=512,                   # Number of bins for signal discretization
    responsitivity=1              # Responsitivity of the detector
)

detector_ssc = Detector(
    name='SSC',                   # Side Scatter (SSC) detector
    NA=0.2,                       # Numerical aperture of the SSC detector
    phi_angle=90,               # Positioned at 90 degrees to detect side scatter
    acquisition_frequency=1e3,    # Acquisition frequency: 1000 Hz
    noise_level=1e-3,             # Noise floor of 0.0001 volt
    saturation_level=10,          # Maximum signal before saturation
    baseline_shift=0.0,           # No baseline shift
    n_bins=1024,                  # Fewer bins for lower resolution
    responsitivity=1              # Responsitivity of the detector
)

# Step 5: Create a FlowCytometer instance
# ---------------------------------------
# We define a flow cytometer setup where particles pass through the laser beam at a flow speed of
# 80 µm/s and in a flow area of 1 µm². The source, detectors, and particle distribution are passed
# to the FlowCytometer instance. Rayleigh scattering is used as the coupling mechanism to model
# how the particles interact with the laser beam.
cytometer = FlowCytometer(
    source=source,  # Laser source
    scatterer_distribution=scatterer_distribution,  # Particle size distribution
    detectors=[detector_fsc, detector_ssc],  # List of detectors (FSC and SSC)
    coupling_mechanism='mie'  # Mie [PyMieSim] scattering model
)

# Step 6: Simulate the flow cytometer signals
# -------------------------------------------
# The signals generated by the flow cytometer for both detectors (FSC and SSC) are
# simulated as particles pass through the laser beam.
cytometer.simulate_pulse()


# Step 7: Display the properties of the simulation
# ------------------------------------------------
# Print the properties of the cytometer, including the source power, particle density,
# and flow speed, to understand the simulation setup better.
cytometer.print_properties()

# Step 8: Visualize the generated signals
# ---------------------------------------
# Plot the simulated signals for both Forward Scatter (FSC) and Side Scatter (SSC) detectors.
# %%
cytometer.plot()

# #############################################################################
# The above plot shows the raw simulated signals for the Forward Scatter (FSC) and
# Side Scatter (SSC) channels. These signals can be analyzed further to extract
# features such as peak height, width, and area. Such analyses provide insights
# into the properties of the particles, such as size and shape complexity.

# This simulation can serve as a basis for developing and testing signal processing
# algorithms in flow cytometry.
