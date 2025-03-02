"""
Flow Cytometry Simulation [2 populations] Density Plot of Scattering Intensities
================================================================================

This example simulates a flow cytometer experiment using the FlowCyPy library,
analyzes pulse signals from two detectors, and generates a 2D density plot of the scattering intensities.

Steps:
1. Set flow parameters and particle size distributions.
2. Set up the laser source and detectors.
3. Simulate the flow cytometry experiment.
4. Analyze pulse signals and generate a 2D density plot.
"""

# Import necessary libraries and modules
import numpy as np
from FlowCyPy import FlowCytometer, ScattererCollection, EventCorrelator, Detector, GaussianBeam, FlowCell, Population
from FlowCyPy import peak_locator
from FlowCyPy.units import particle, milliliter, nanometer, RIU, second, micrometer, millisecond, meter
from FlowCyPy.units import degree, watt, ampere, millivolt, ohm, kelvin, milliampere, megahertz, microvolt
from FlowCyPy.units import microsecond
from FlowCyPy.units import milliwatt, AU
from FlowCyPy import NoiseSetting
from FlowCyPy.population import Exosome, HDL, get_microbeads


NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = True
NoiseSetting.include_RIN_noise = False

# Set random seed for reproducibility
np.random.seed(3)

# Step 1: Define Flow Parameters
flow_cell = FlowCell(
    flow_speed=7.56 * meter / second,      # Flow speed: 7.56 meters per second
    flow_area=(10 * micrometer) ** 2,      # Flow area: 10 x 10 micrometers
    run_time=.2 * millisecond             # Total simulation time: 0.3 milliseconds
)

# Step 2: Create Populations (Extracellular Vesicles and Liposomes)
scatterer = ScattererCollection(medium_refractive_index=1.33 * RIU)  # Medium refractive index: 1.33

population_0 = Population(
    name='Pop 0',
    particle_count=30 * particle,
    size=100 * nanometer,
    refractive_index=1.39 * RIU
)

scatterer.add_population(population_0)

# Initialize scatterer and link it to the flow cell
flow_cell.initialize(scatterer_collection=scatterer)

# Print and plot properties of the populations
scatterer._log_properties()

time = scatterer.dataframe['Time']


print(scatterer.dataframe)

import matplotlib.pyplot as plt

figure, ax = plt.subplots(1, 1)
plt.hist(time, bins='auto', alpha=0.6)
plt.show()