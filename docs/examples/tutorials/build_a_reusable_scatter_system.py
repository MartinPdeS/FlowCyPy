"""
Build a reusable two-channel scatter system
===========================================

Define the collection geometry once, then use it to create instruments with
different laser powers. This approach uses FlowCyPy's reference flow cell and
electronics. The component assembly tutorial shows how to choose those too.
"""

from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems import ScatterChannel, ScatterSystem
from FlowCyPy.units import ureg

# %%
# Define the illumination and collection angles
# ---------------------------------------------
# The first channel is the default trigger. The forward detector has a central
# obscuration, specified by its inner numerical aperture.

ssc = ScatterChannel(
    name="SSC",
    phi_angle=90 * ureg.degree,
    numerical_aperture=1.0,
    sampling=500,
)

fsc = ScatterChannel(
    name="FSC",
    phi_angle=0 * ureg.degree,
    numerical_aperture=0.3,
    cache_numerical_aperture=0.1,
    sampling=500,
)

scatter_system = ScatterSystem(
    wavelength=488 * ureg.nanometer,
    channels=(ssc, fsc),
)

# %%
# Instantiate and acquire at two laser powers
# -------------------------------------------
# Each call creates a fresh sample collection. Use identical beads and a fixed
# seed in both instruments so the particle arrivals match.

for power in (10, 20) * ureg.milliwatt:
    instrument = scatter_system(optical_power=power)
    beads = microbeads(
        name="200 nm beads",
        diameter=200 * ureg.nanometer,
        refractive_index=1.59,
        concentration=1e8 * ureg.particle / ureg.milliliter,
    )
    instrument.fluidics.scatterer_collection.add_population(beads)
    record = instrument.acquire(run_time=200 * ureg.microsecond, random_state=42)
    record.plot_analog(title=f"Scatter at {power:~P}", include_scatterer=False)
