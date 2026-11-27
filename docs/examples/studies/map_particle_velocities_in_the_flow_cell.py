"""
Map particle velocities across a focused flow cell
==================================================

This example shows how to simulate particle trajectories in a rectangular
flow cell and visualize their transverse positions.

The figure highlights three pieces of information:

1. the full channel cross section, shown as the sheath region
2. the focused sample core, shown as the sample region
3. the simulated particle positions, colored by their local axial velocity

This is a convenient way to inspect how hydrodynamic focusing shapes the
particle distribution before optical interrogation.
"""

# sphinx_gallery_thumbnail_number = 1

import matplotlib.pyplot as plt

from FlowCyPy.units import ureg
from FlowCyPy.fluidics import (
    Fluidics,
    FlowCell,
    ScattererCollection,
    SampleFlowRate,
    SheathFlowRate,
    populations,
    distributions,
)


# %%
# Define the flow cell
# --------------------
# The flow cell geometry and the sample and sheath flow rates determine the
# size of the focused sample core.

flow_cell = FlowCell(
    sample_volume_flow=SampleFlowRate.HIGH.value,
    sheath_volume_flow=SampleFlowRate.HIGH.value * 1,
    width=400 * ureg.micrometer,
    height=400 * ureg.micrometer,
)


# %%
# Define the particle population
# ------------------------------
# Here we construct a single spherical population with user-defined
# distributions for particle diameter and refractive index.

scatterer_collection = ScattererCollection()

medium_refractive_index = distributions.Delta(1.33)

diameter_dist = distributions.RosinRammler(
    scale=200 * ureg.nanometer,
    shape=10,
)

ri_dist = distributions.Normal(
    mean=1.44,
    standard_deviation=0.002,
    low_cutoff=1.33,
)

sampling_method = populations.ExplicitModel()

population_0 = populations.SpherePopulation(
    name="Pop 0",
    medium_refractive_index=medium_refractive_index,
    concentration=1e10 * ureg.particle / ureg.milliliter,
    diameter=diameter_dist,
    refractive_index=ri_dist,
    sampling_method=sampling_method,
)

scatterer_collection.add_population(population_0)

# Dilute the initial collection to reduce the number of sampled particles.
scatterer_collection.dilute(factor=80)


# %%
# Generate particle events
# ------------------------
# The Fluidics object uses the flow cell and the scatterer collection to
# generate particle events over the requested run time.

fluidics = Fluidics(
    scatterer_collection=scatterer_collection,
    flow_cell=flow_cell,
)

event_collection = fluidics.generate_event_collection(
    run_time=5 * ureg.millisecond,
    sampling_rate=10 * ureg.megahertz,
)

df = event_collection[0].to_dataframe()


# %%
# Plot the transverse particle distribution
# -----------------------------------------
# The outer rectangle represents the full channel cross section.
# The inner rectangle represents the focused sample core.
# Particle positions are colored by their local velocity.

figure, ax = plt.subplots()
for region, label in [(flow_cell.sheath, "Sheath"), (flow_cell.sample, "Sample")]:
    width = region.width.m_as("micrometer")
    height = region.height.m_as("micrometer")
    channel_outline = plt.Rectangle((-width / 2, -height / 2), width, height, fill=False)
    ax.add_patch(channel_outline)
    ax.annotate(label, (0, height / 2))

particles = ax.scatter(
    df.x.to("micrometer").magnitude,
    df.y.to("micrometer").magnitude,
    c=df.Velocity.to("meter/second").magnitude,
)
ratio = (flow_cell.sheath.volume_flow / flow_cell.sample.volume_flow).magnitude
ax.set(xlabel="x position [µm]", ylabel="y position [µm]", title=f"Sheath/sample flow ratio = {ratio:.2f}", aspect="equal")
figure.colorbar(particles, ax=ax, label="Velocity [m/s]")
plt.show()
