"""
Flow Cytometry Simulation and 2D Density Plot of Scattering Intensities
=======================================================================

This example demonstrates how to simulate a flow cytometer using the FlowCyPy library, analyze the pulse
signals from two detectors, and plot a 2D density plot of the scattering intensities.

Flow cytometry is a technique used to analyze the physical and chemical properties of particles as they flow
through a laser beam. This script simulates the behavior of particles in a flow, models the light scattering
detected by two detectors, and visualizes the scattering intensity data in a 2D hexbin plot.

Steps in the Script:
--------------------
1. Define the flow parameters (e.g., speed, area, scatterer density).
2. Create a particle size distribution.
3. Set up a laser source and detectors.
4. Simulate the flow cytometry experiment.
5. Analyze the pulse signals from both detectors.
6. Plot a 2D density plot of the scattering intensities from the two detectors.

LP: 1.45
EV 1.39
"""

# Import necessary libraries and modules
import numpy as np
from FlowCyPy import FlowCytometer, ScattererDistribution, Analyzer, Detector, Source, FlowCell, Plotter
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.peak_detector import BasicPeakDetector
from FlowCyPy.population import Population
from FlowCyPy.units import (
    microsecond,
    micrometer,
    meter,
    refractive_index_unit,
    milliliter,
    millisecond,
    second,
    particle,
    nanometer,
    milliwatt,
    degree,
    volt,
    watt,
    megahertz
)

# Set random seed for reproducibility
np.random.seed(3)

# Step 1: Define the Flow Parameters
flow = FlowCell(
    flow_speed=7.56 * meter / second,       # Flow speed: 8 micrometers per second
    flow_area=(10 * micrometer) ** 2,       # Flow area: 1 square micrometer
    total_time=0.1 * millisecond,           # Total simulation time: 8 milliseconds
)

# %%
# Step 2: Define Particle Size Distributions (Two Normal Distributions)
size_lp = NormalDistribution(
    mean=200 * nanometer,      # Mean particle size: 3 micrometers
    std_dev=10 * nanometer     # Standard deviation of particle size: 0.5 micrometer
)

size_ev = NormalDistribution(
    mean=50 * nanometer,      # Mean particle size: 30 micrometers
    std_dev=5.0 * nanometer   # Standard deviation of particle size: 1 micrometer
)

ri_ev = NormalDistribution(
    mean=1.39 * refractive_index_unit,    # Mean particle size: 30 micrometers
    std_dev=0.01 * refractive_index_unit  # Standard deviation of particle size: 1 micrometer
)

ri_lp = NormalDistribution(
    mean=1.45 * refractive_index_unit,    # Mean particle size: 30 micrometers
    std_dev=0.01 * refractive_index_unit  # Standard deviation of particle size: 1 micrometer
)

ev = Population(
    size=size_ev,
    refractive_index=ri_ev,
    concentration=1.8e+9 * particle / milliliter / 3,
    name='EV'
)

lp = Population(
    size=size_lp,
    refractive_index=ri_lp,
    concentration=1.8e+9 * particle / milliliter / 1,
    name='LP'
)

scatterer_distribution = ScattererDistribution(flow=flow, populations=[ev, lp])

scatterer_distribution.plot()


# %%
# Step 3: Set up the Laser Source
source = Source(
    NA=0.2,                       # Numerical aperture of the laser optics
    wavelength=800 * nanometer,   # Laser wavelength: 800 nm
    optical_power=20 * milliwatt   # Laser optical power: 200 milliwatt
)

# Step 4: Set up Detectors (Two Detectors at Different Angles)
detector_0 = Detector(
    phi_angle=90 * degree,                # Angle: 90 degrees (Side Scatter)
    NA=1.2,                               # Numerical aperture of the detector optics
    name='Side',                          # Name of the detector
    responsitivity=1 * volt / watt,       # Responsitivity of the detector
    acquisition_frequency=10 * megahertz, # Sampling frequency: 10,000 Hz
    noise_level=0e-2 * volt,              # No noise
    baseline_shift=0.00 * volt,           # No baseline shift
    saturation_level=100 * volt,          # No signal saturation
    n_bins='14bit'                        # Discretization bins
)

detector_1 = Detector(
    phi_angle=180 * degree,               # Angle: 180 degrees (Front Scatter)
    NA=1.2,                               # Numerical aperture of the detector optics
    name='Front',                         # Name of the detector
    responsitivity=1 * volt / watt,       # Responsitivity of the detector
    acquisition_frequency=10 * megahertz, # Sampling frequency: 10,000 Hz
    noise_level=0e-2 * volt,              # No noise
    baseline_shift=0.00 * volt,           # No baseline shift
    saturation_level=100 * volt,          # No signal saturation
    n_bins='14bit'                         # Discretization bins
)

# Step 5: Simulate the Flow Cytometry Experiment
cytometer = FlowCytometer(
    coupling_mechanism='mie',                       # Use Mie scattering for particle simulation
    source=source,                                  # Laser source
    scatterer_distribution=scatterer_distribution,  # Particle size distribution
    detectors=[detector_0, detector_1]              # Two detectors in the setup
)

# Run the simulation to generate the scattering signals
cytometer.simulate_pulse()

# Plot the scattering signals for both detectors
cytometer.plot()

# Step 6: Analyze the Pulse Signals
analyzer = Analyzer(detector_0, detector_1, algorithm=BasicPeakDetector())

# Analyze and extract data from both detectors
analyzer.run_analysis(
    compute_peak_area=False,   # Set whether to compute peak area
)
analyzer.plot()

# %%
# Get coincidence data from the two detectors
datasets = analyzer.get_coincidence_dataset(coincidence_margin=0.1 * microsecond)

# Step 7: Plot the 2D Density of Scattering Intensities
plotter = Plotter(
    dataset_0=datasets[0],  # Processed data from the first detector
    dataset_1=datasets[1],  # Processed data from the second detector
)

# %%
# Plot the 2D density plot
plotter.plot()
