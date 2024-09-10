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
"""

# Import necessary libraries and modules
from FlowCyPy import FlowCytometer, ScattererDistribution, Analyzer, Detector, Source, FlowCell, Plotter
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.peak_detector import MovingAveragePeakDetector
import numpy as np

# Set random seed for reproducibility
np.random.seed(20)

# Step 1: Define the Flow Parameters
flow = FlowCell(
    flow_speed=8e-6,           # Flow speed: 8 micrometers per second
    flow_area=1e-6,            # Flow area: 1 square micrometer
    total_time=8.0,            # Total simulation time: 8 seconds
    scatterer_density=1e13     # Particle density: 1e12 particles per cubic meter
)

# Step 2: Define Particle Size Distributions (Two Normal Distributions)
size_distribution_0 = NormalDistribution(
    scale_factor=10,
    mean=3e-6,                 # Mean particle size: 3 micrometers
    std_dev=0.5e-6             # Standard deviation of particle size: 0.5 micrometer
)

size_distribution_1 = NormalDistribution(
    scale_factor=1,
    mean=30e-6,                # Mean particle size: 30 micrometers
    std_dev=3e-6               # Standard deviation of particle size: 1 micrometer
)

refractive_index_distribution = NormalDistribution(
    scale_factor=1,
    mean=1.5,
    std_dev=0.1
)

scatterer_distribution = ScattererDistribution(
    flow=flow,
    refractive_index=[refractive_index_distribution],      # Refractive index of the particles
    size=[size_distribution_0, size_distribution_1]  # List of distributions for different scatterer populations
)


# %%
scatterer_distribution.plot()

scatterer_distribution.print_properties()