"""
Simulating Flow Cytometer Signals with Rayleigh Scattering
==========================================================

This script simulates signals from a flow cytometer using Rayleigh scattering to model the interaction
of particles with a laser beam. It demonstrates how to generate Forward Scatter (FSC) and Side Scatter (SSC) signals
using FlowCyPy and visualize the results.

Steps:
1. Define the flow parameters and particle size distribution.
2. Set up the laser source and detectors.
3. Simulate the flow cytometer signals.
4. Visualize and analyze the signals from FSC and SSC detectors.
"""

# Step 1: Import the necessary libraries
from FlowCyPy import FlowCytometer, Scatterer, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution, Population
from FlowCyPy.units import (
    RIU, milliliter, particle, nanometer, degree, microvolt, AU,
    megahertz, milliwatt, micrometer, millisecond, meter, second
)

# Step 2: Define the flow parameters
# ----------------------------------
# Flow speed is set to 80 micrometers per second, with a flow area of 1 square micrometer and a total simulation time of 1 second.
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,        # Flow speed: 7.56 meters per second
    flow_area=(20 * micrometer) ** 2,        # Flow area: 10 x 10 micrometers
    run_time=0.5 * millisecond             # Total simulation time: 0.3 milliseconds
)

flow_cell.print_properties()

# Step 3: Define the particle size distribution
# ---------------------------------------------
# We define a normal distribution for particle sizes with a mean of 200 nm, standard deviation of 10 nm,
# and a refractive index of 1.39 with a small variation of 0.01.
scatterer = Scatterer(medium_refractive_index=1.33 * RIU)

population_0 = Population(
    name='EV',
    size=distribution.RosinRammler(characteristic_size=50 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.05 * RIU)
)

population_1 = Population(
    name='LP',
    size=distribution.RosinRammler(characteristic_size=200 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.45 * RIU, std_dev=0.05 * RIU)
)

scatterer.add_population(population_0, particle_count=1e+9 * particle / milliliter)
scatterer.add_population(population_1, particle_count=1e+9 * particle / milliliter)

scatterer.initialize(flow_cell=flow_cell)

scatterer._log_properties()

# Step 4: Set up the light source
# -------------------------------
# A laser with a wavelength of 1550 nm, optical power of 2 mW, and a numerical aperture of 0.4 is used.
source = GaussianBeam(
    numerical_aperture=0.4 * AU,     # Numerical aperture: 0.4
    wavelength=1550 * nanometer,     # Wavelength: 1550 nm
    optical_power=200 * milliwatt    # Optical power: 2 mW
)

# Step 5: Set up the detectors
# ----------------------------
# Two detectors are used: Forward Scatter (FSC) and Side Scatter (SSC). Each detector is configured
# with its own numerical aperture, responsitivity, noise level, and acquisition frequency.
detector_fsc = Detector(
    name='FSC',                         # Forward Scatter detector
    numerical_aperture=1.2 * AU,        # Numerical aperture: 0.2
    phi_angle=0 * degree,               # Angle: 180 degrees for forward scatter
    sampling_freq=10 * megahertz,       # Sampling frequency: 10 MHz
    saturation_level=1000 * microvolt,  # Saturation level: 10 volts
    n_bins='14bit',                     # Number of discretization bins: 512
)

detector_ssc = Detector(
    name='SSC',                         # Side Scatter detector
    numerical_aperture=1.2 * AU,        # Numerical aperture: 0.2
    phi_angle=90 * degree,              # Angle: 90 degrees for side scatter
    sampling_freq=10 * megahertz,       # Sampling frequency: 10 MHz
    saturation_level=1000 * microvolt,  # Saturation level: 10 volts
    n_bins='14bit',                     # Number of discretization bins: 1024
)

# Step 6: Create a FlowCytometer instance
# ---------------------------------------
# The flow cytometer is configured with the source, scatterer distribution, and detectors.
# The 'mie' coupling mechanism models how the particles interact with the laser beam.
cytometer = FlowCytometer(
    source=source,                # Laser source
    scatterer=scatterer,  # Particle size distribution
    detectors=[detector_fsc, detector_ssc],  # Detectors: FSC and SSC
    coupling_mechanism='mie'      # Scattering model: Mie
)

# Step 7: Simulate flow cytometer signals
# ---------------------------------------
# Simulate the signals for both detectors (FSC and SSC) as particles pass through the laser beam.
cytometer.simulate_pulse()

# Step 8: Display the properties of the simulation
# ------------------------------------------------
# Print the properties of the simulation setup to better understand flow speed, particle density, and source power.
cytometer._log_statistics()

# Step 9: Visualize the generated signals
# ---------------------------------------
# Plot the simulated signals for both FSC and SSC detectors.
cytometer.plot()

# %%
#
# The above plot shows the raw simulated signals for Forward Scatter (FSC) and
# Side Scatter (SSC) channels. These signals provide insights into particle size
# and complexity and can be further analyzed for feature extraction, such as peak height and width.
