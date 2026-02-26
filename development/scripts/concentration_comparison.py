"""
Flow Cytometry Simulation: Full System Example
==============================================

This tutorial demonstrates a complete flow cytometry simulation using the FlowCyPy library.
It models fluidics, optics, signal processing, and classification of multiple particle populations.

Steps Covered:
--------------
1. Configure simulation parameters and noise models
2. Define laser source, flow cell geometry, and fluidics
3. Add synthetic particle populations
4. Set up detectors, amplifier, and digitizer
5. Simulate analog and digital signal acquisition
6. Apply triggering and peak detection
7. Classify particle events based on peak features
"""

# %%
# Step 0: Global Settings and Imports
# -----------------------------------
import numpy as np
from TypedUnit import ureg

from FlowCyPy import SimulationSettings

SimulationSettings.include_noises = False
SimulationSettings.include_shot_noise = True
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = True
SimulationSettings.include_amplifier_noise = True
SimulationSettings.assume_perfect_hydrodynamic_focusing = True
SimulationSettings.population_cutoff_bypass = False

# %%
# Step 1: Define Flow Cell and Fluidics
# -------------------------------------
# from FlowCyPy.fluidics import FlowCell
# from FlowCyPy.fluidics import Fluidics, ScattererCollection, populations


from FlowCyPy.binary import distributions, populations


medium_refractive_index = distributions.Delta(1.33 * ureg.RIU)

diameter_dist = distributions.RosinRammler(
    shape=150 * ureg.nanometer,
    scale=50 * ureg.nanometer,
    low_cutoff=50.0 * ureg.nanometer,
)

ri_dist = distributions.Normal(
    mean=1.44 * ureg.RIU,
    standard_deviation=0.002 * ureg.RIU,
    low_cutoff=1.33 * ureg.RIU,
)

sampling_method = populations.GammaModel(number_of_samples=10_000)

population_0 = populations.SpherePopulation(
    name="Pop 0",
    medium_refractive_index=medium_refractive_index,
    concentration=5e10 * ureg.particle / ureg.milliliter,
    diameter=diameter_dist,
    refractive_index=ri_dist,
    sampling_method=sampling_method,
)


# diameter_dist = distributions.RosinRammler(
#     shape=50 * ureg.nanometer,
#     scale=50 * ureg.nanometer,
# )

# ri_dist = distributions.Normal(
#     mean=1.44 * ureg.RIU,
#     standard_deviation=0.002 * ureg.RIU,
#     low_cutoff=1.33 * ureg.RIU,
# )

# population_1 = population.Sphere(
#     name="Pop 1",
#     medium_refractive_index=medium_refractive_index,
#     concentration=5e17 * ureg.particle / ureg.milliliter,
#     diameter=diameter_dist,
#     refractive_index=ri_dist,
#     sampling_method=GammaModel(mc_samples=10_000),
# )
