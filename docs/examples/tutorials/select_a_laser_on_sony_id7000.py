"""
Choose a laser on the Sony ID7000
=================================

The two ID7000 factories model different scatter channels. Use the 405 nm
factory for side scatter (SSC) and the 488 nm factory for forward scatter
(FSC). Here we configure the violet channel for a faster acquisition and
inspect the analog voltage trace from each configuration.
"""

import matplotlib.pyplot as plt
from FlowCyPy.fluidics.populations import SpherePopulation
from FlowCyPy.systems.sony import id7000_405, id7000_488
from FlowCyPy.units import ureg

# %%
# Choose the channels and sampling rates
# --------------------------------------
# Both factories return independent workflows. Doubling the violet system's
# sampling rate gives it a 50 ns sample interval. The blue system keeps its
# default 100 ns interval.

violet = id7000_405(optical_power=20 * ureg.milliwatt)
blue = id7000_488(optical_power=20 * ureg.milliwatt)
violet.opto_electronics.digitizer.sampling_rate = 20 * ureg.megahertz

# %%
# Acquire a bead sample on each system
# ------------------------------------
# Use the same bead properties and random seed in both acquisitions. Each
# panel shows a separate simulated acquisition with its own voltage scale.

figure, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 5), layout="constrained")
for system, axis in zip((violet, blue), axes):
    beads = SpherePopulation(
        name="200 nm beads",
        diameter=200 * ureg.nanometer,
        refractive_index=1.59,
        medium_refractive_index=1.33,
        concentration=1e8 * ureg.particle / ureg.milliliter,
    )
    system.fluidics.scatterer_collection.add_population(beads)
    acquisition = system.acquire(run_time=100 * ureg.microsecond, random_state=42)

    optics = system.opto_electronics
    channel = optics.detectors[0].name
    wavelength = optics.source.wavelength.m_as("nanometer")
    sampling_rate = optics.digitizer.sampling_rate.m_as("megahertz")
    trace = acquisition.signal.analog
    axis.plot(trace["Time"].m_as("microsecond"), trace[channel].m_as("microvolt"))
    axis.set_title(f"{wavelength:.0f} nm {channel} sampled at {sampling_rate:g} MHz")
    axis.set_ylabel("Voltage (µV)")

axes[-1].set_xlabel("Time (µs)")
plt.show()
