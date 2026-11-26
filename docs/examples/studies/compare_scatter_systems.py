"""
Compare side-scatter collection at 488 nm
=========================================

The BD FACSCanto II and nanoFCM NanoAnalyzer presets both illuminate the
sample at 488 nm. How does the same bead pulse appear on their modeled
side-scatter detectors? These presets share FlowCyPy reference fluidics and
electronics, so the comparison describes their modeled collection optics.
"""

import matplotlib.pyplot as plt
from FlowCyPy.fluidics.populations import SpherePopulation
from FlowCyPy.systems.bd import facs_canto_ii
from FlowCyPy.systems.nanofcm import nanoanalyzer
from FlowCyPy.units import ureg

# %%
# Hold the sample and illumination fixed
# --------------------------------------
# Give each instrument an independent sample with identical bead properties.
# Reusing the seed reproduces the particle arrivals. Disable optical noise to
# see the change in pulse amplitude at the two collection apertures.

figure, axis = plt.subplots(figsize=(8, 4), layout="constrained")
for label, factory in (("BD FACSCanto II", facs_canto_ii), ("nanoFCM NanoAnalyzer", nanoanalyzer)):
    system = factory(optical_power=20 * ureg.milliwatt)
    system.opto_electronics.source.include_shot_noise = False
    system.opto_electronics.source.include_rin_noise = False
    beads = SpherePopulation(
        name="200 nm beads",
        diameter=200 * ureg.nanometer,
        refractive_index=1.59,
        medium_refractive_index=1.33,
        concentration=1e8 * ureg.particle / ureg.milliliter,
    )
    system.fluidics.scatterer_collection.add_population(beads)
    acquisition = system.acquire(run_time=100 * ureg.microsecond, random_state=42)
    trace = acquisition.signal.analog
    side_detector = next(detector for detector in system.opto_electronics.detectors if detector.name == "SSC")
    axis.plot(
        trace["Time"].m_as("microsecond"),
        trace["SSC"].m_as("microvolt"),
        label=f"{label} (NA {side_detector.numerical_aperture:g})",
    )

axis.set(xlabel="Time (µs)", ylabel="Side-scatter voltage (µV)")
axis.legend()
plt.show()

# %%
# The peaks line up in time because both systems see the same bead arrivals.
# In this simulation the larger SSC aperture gives taller pulses.
