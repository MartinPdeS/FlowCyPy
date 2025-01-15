"""
Generating Signal
=================

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
from FlowCyPy import FlowCytometer, ScattererCollection, Detector, GaussianBeam, FlowCell
from FlowCyPy import distribution, Population
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import units

# Step 2: Set up the light source
# -------------------------------
# A laser with a wavelength of 1550 nm, optical power of 2 mW, and a numerical aperture of 0.4 is used.
source = GaussianBeam(
    numerical_aperture=0.4 * units.AU,     # Numerical aperture: 0.4
    wavelength=1550 * units.nanometer,     # Wavelength: 1550 nm
    optical_power=200 * units.milliwatt    # Optical power: 2 mW
)

# Step 3: Define the flow parameters
# ----------------------------------
# Flow speed is set to 80 micrometers per second, with a flow area of 1 square micrometer and a total simulation time of 1 second.
flow_cell = FlowCell(
    source=source,
    flow_speed=7.56 * units.meter / units.second,        # Flow speed: 7.56 meters per second
    flow_area=(20 * units.micrometer) ** 2,        # Flow area: 10 x 10 micrometers
)

# Step 4: Define the particle size distribution
# ---------------------------------------------
# We define a normal distribution for particle sizes with a mean of 200 nm, standard deviation of 10 nm,
# and a refractive index of 1.39 with a small variation of 0.01.
scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

population_0 = Population(
    name='EV',
    particle_count=1e+9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=50 * units.nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * units.RIU, std_dev=0.05 * units.RIU)
)

population_1 = Population(
    name='LP',
    particle_count=1e+9 * units.particle / units.milliliter,
    size=distribution.RosinRammler(characteristic_size=200 * units.nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.45 * units.RIU, std_dev=0.05 * units.RIU)
)

scatterer_collection.add_population(population_0, population_1)

# Step 5: Set up the detectors
# ----------------------------
# Two detectors are used: Forward Scatter (FSC) and Side Scatter (SSC). Each detector is configured
# with its own numerical aperture, responsitivity, noise level, and acquisition frequency.
signal_digitizer = SignalDigitizer(
    bit_depth=1024,
    saturation_levels='auto',
    sampling_freq=10 * units.megahertz,           # Sampling frequency: 10 MHz
)

detector_fsc = Detector(
    name='FSC',                         # Forward Scatter detector
    numerical_aperture=1.2 * units.AU,        # Numerical aperture: 0.2
    phi_angle=0 * units.degree,               # Angle: 180 degrees for forward scatter
)

detector_ssc = Detector(
    name='SSC',                         # Side Scatter detector
    numerical_aperture=1.2 * units.AU,        # Numerical aperture: 0.2
    phi_angle=90 * units.degree,              # Angle: 90 degrees for side scatter
)

# Step 6: Create a FlowCytometer instance
# ---------------------------------------
# The flow cytometer is configured with the source, scatterer distribution, and detectors.
# The 'mie' coupling mechanism models how the particles interact with the laser beam.
cytometer = FlowCytometer(
    signal_digitizer=signal_digitizer,
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,  # Particle size distribution
    detectors=[detector_fsc, detector_ssc],  # Detectors: FSC and SSC
)

# Step 7: Simulate flow cytometer signals
# ---------------------------------------
# Simulate the signals for both detectors (FSC and SSC) as particles pass through the laser beam.
# Run the flow cytometry simulation
acquisition = cytometer.get_acquisition(run_time=0.2 * units.millisecond)

# Visualize the scatter signals from both detectors
acquisition.plot.signals()

# %%
#
# The above plot shows the raw simulated signals for Forward Scatter (FSC) and
# Side Scatter (SSC) channels. These signals provide insights into particle size
# and complexity and can be further analyzed for feature extraction, such as peak height and width.
