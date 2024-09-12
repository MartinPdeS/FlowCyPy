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
from FlowCyPy import FlowCytometer, ScattererDistribution, FlowCell
from FlowCyPy.distribution import NormalDistribution
from FlowCyPy.population import Population
from FlowCyPy.units import second, nanometer, refractive_index_unit, particle, milliliter, meter, micrometer, millisecond
import numpy as np

# Set random seed for reproducibility
np.random.seed(20)

# Step 1: Define the Flow Parameters
flow = FlowCell(
    flow_speed=7.56 * meter / second,       # Flow speed: 8 micrometers per second
    flow_area=(10 * micrometer) ** 2,       # Flow area: 1 square micrometer
    total_time=0.1 * millisecond,           # Total simulation time: 8 milliseconds
)


# Step 2: Define Particle Size Distributions (Two Normal Distributions)
lp_size = NormalDistribution(
    mean=200 * nanometer,      # Mean particle size: 3 micrometers
    std_dev=10 * nanometer     # Standard deviation of particle size: 0.5 micrometer
)

ev_size = NormalDistribution(
    mean=50 * nanometer,      # Mean particle size: 30 micrometers
    std_dev=5.0 * nanometer   # Standard deviation of particle size: 1 micrometer
)

ev_ri = NormalDistribution(
    mean=1.39 * refractive_index_unit,    # Mean particle size: 30 micrometers
    std_dev=0.01 * refractive_index_unit  # Standard deviation of particle size: 1 micrometer
)

lp_ri = NormalDistribution(
    mean=1.45 * refractive_index_unit,    # Mean particle size: 30 micrometers
    std_dev=0.01 * refractive_index_unit  # Standard deviation of particle size: 1 micrometer
)

ev = Population(
    size=ev_size,
    refractive_index=ev_ri,
    concentration=1.8e+9 * particle / milliliter / 3,
    name='EV'
)

lp = Population(
    size=lp_size,
    refractive_index=lp_ri,
    concentration=1.8e+9 * particle / milliliter / 1,
    name='LP'
)


# %%
scatterer_distribution = ScattererDistribution(flow=flow, populations=[ev, lp])

scatterer_distribution.plot()

scatterer_distribution.print_properties()