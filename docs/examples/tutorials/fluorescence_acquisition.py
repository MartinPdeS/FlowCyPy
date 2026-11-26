"""
Detect fluorescent beads alongside unlabeled beads
==================================================

Run two populations of 300 nm beads through a 488 nm laser. Both scatter
light. Only the labeled population emits fluorescence. Compare the two PMT
voltages against the simulated particle arrival times in the same acquisition.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.fluorescence import Bandpass, Fluorophore, Label
from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

# %%
# Label one bead population
# -------------------------
# These illustrative dye parameters specify the molecular absorption cross
# section at 488 nm and the relative number of photons in each emission bin.
# The 4 ns emission lifetime is short compared with the beam transit time.
# Keep the bead size, refractive index and concentration equal in both populations.

instrument = facs_canto(include_shot_noise=False, include_rin_noise=False)
dye = Fluorophore(
    name="green dye",
    absorption_cross_section=2e-20 * ureg.meter**2,
    quantum_yield=0.8,
    lifetime=4 * ureg.nanosecond,
    emission_wavelengths=np.array([510, 520, 530, 550]) * ureg.nm,
    photon_weights=(1, 4, 3, 2),
)
label = Label(fluorophore=dye, molecules_per_particle=20_000)
for name, labels in [("Labeled", [label]), ("Unlabeled", [])]:
    beads = microbeads(
        name=name,
        diameter=300 * ureg.nm,
        refractive_index=1.59,
        concentration=2e7 * ureg.particle / ureg.milliliter,
        labels=labels,
    )
    instrument.fluidics.scatterer_collection.add_population(beads)

# %%
# Add a green PMT and acquire both signals
# ----------------------------------------
# The instrument's side PMT uses the scatter-only default. The green PMT
# accepts fluorescence from 515 through 545 nm, including the 520 and 530 nm
# bins. Optical noise and green PMT dark current are disabled to make the
# relationship between individual events and pulses visible.

green = pmt(
    name="green",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.8,
    signals=("fluorescence",),
    optical_filter=Bandpass(center=530 * ureg.nm, width=30 * ureg.nm),
    dark_current=0 * ureg.ampere,
)
optics = instrument.opto_electronics
optics.detectors = [*optics.detectors, green]
record = instrument.acquire(run_time=200 * ureg.microsecond, random_state=42)

# %%
# Match pulses to their particles
# -------------------------------
# The top panel marks each bead's arrival. Read vertically to compare the
# side-scatter and green-channel responses. Closely spaced arrivals can
# contribute to the same pulse. Each voltage panel has its own scale.

figure, axes = plt.subplots(
    3, 1, sharex=True, figsize=(8, 5), height_ratios=(1, 2, 2), layout="constrained"
)
for row, events in enumerate(record.event_collection):
    arrivals = events.get_quantity("Time").m_as("microsecond")
    axes[0].vlines(arrivals, row - 0.28, row + 0.28, color="black")
axes[0].set_yticks([0, 1], ["Labeled", "Unlabeled"])
axes[0].set_ylim(-0.5, 1.5)
axes[0].set_title("Particle arrivals and detector responses")

analog = record.signal.analog
time = analog["Time"].m_as("microsecond")
axes[1].plot(time, analog["side"].m_as("microvolt"), color="tab:blue")
axes[1].set_ylabel("Side scatter (µV)")
axes[2].plot(time, analog["green"].m_as("nanovolt"), color="seagreen")
axes[2].set_ylabel("Fluorescence (nV)")
axes[2].set_xlabel("Time (µs)")
plt.show()
