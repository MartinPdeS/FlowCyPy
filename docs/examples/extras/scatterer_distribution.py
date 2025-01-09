"""
Scatterer Collection
====================

This script simulates a flow cytometer using the FlowCyPy library. It models light scattering from particles
detected by two detectors (Forward Scatter and Side Scatter) and visualizes the scattering intensities in a 2D hexbin plot.

Flow cytometry is used to analyze the physical and chemical properties of particles as they flow through a laser beam.

Steps in the Workflow:
----------------------
1. Define the flow parameters (e.g., speed, area, and total simulation time).
2. Create particle size and refractive index distributions.
3. Set up a laser source and detectors.
4. Simulate the flow cytometry experiment.
5. Visualize the scattering intensity in a 2D hexbin plot.
"""

# Import necessary libraries and modules
from FlowCyPy import ScattererCollection, FlowCell
from FlowCyPy import distribution, Population
from FlowCyPy.units import second, nanometer, RIU, particle, milliliter, meter, micrometer, millisecond
import numpy as np

# Set random seed for reproducibility
np.random.seed(20)


# Step 1: Define Particle Size and Refractive Index Distributions
# ---------------------------------------------------------------
# Two particle populations are defined with different sizes and refractive indices.
scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * RIU)

population_0 = Population(
    name='EV',
    particle_count=2e+9 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=50 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.39 * RIU, std_dev=0.05 * RIU)
)

population_1 = Population(
    name='LP',
    particle_count=1e+10 * particle / milliliter,
    size=distribution.RosinRammler(characteristic_size=200 * nanometer, spread=4.5),
    refractive_index=distribution.Normal(mean=1.45 * RIU, std_dev=0.05 * RIU)
)

scatterer_collection.add_population(population_0, population_1)

scatterer_collection.plot()

"""
Summary:
--------
This script defines a flow cytometer simulation, sets up the particle size and refractive index distributions,
and visualizes the scatterer distribution in a 2D density plot. It provides insight into the scattering properties
of two different particle populations.
"""
