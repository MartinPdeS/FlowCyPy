"""
Flow Cytometry Simulation: FacsCanto System
============================================

This tutorial demonstrates how to set up and run a flow cytometry simulation using the FacsCanto instance from the FlowCyPy library.
It includes defining a particle population, configuring the flow cytometer, running the simulation, and visualizing the results.
"""

# %%
# Step 0: Global Settings and Imports
# -----------------------------------
from FlowCyPy.instances.flow_cytometer import FacsCanto, SampleFlowRate, SheathFlowRate
from FlowCyPy.fluidics import distribution, population
from TypedUnit import ureg


population_0 = population.Sphere(
    name="Pop 0",
    particle_count=5e9 * ureg.particle / ureg.milliliter,
    diameter=distribution.RosinRammler(150 * ureg.nanometer, spread=30),
    refractive_index=distribution.Normal(1.44 * ureg.RIU, std_dev=0.002 * ureg.RIU),
)

facs_canto = FacsCanto(
    sample_volume_flow=SampleFlowRate.MEDIUM,
    sheath_volume_flow=SheathFlowRate.DEFAULT,
    optical_power=20 * ureg.milliwatt,
    background_power=1 * ureg.nanowatt,
)

facs_canto.add_population(population_0)

facs_canto.dilute_sample(factor=100)

run_record = facs_canto.run(run_time=0.2 * ureg.millisecond)

run_record.plot_digital()
