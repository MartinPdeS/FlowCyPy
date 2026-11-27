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
from FlowCyPy.digital_processing import DigitalProcessing, discriminator, peak_locator
from FlowCyPy.dyes import alexa_fluor_488
from FlowCyPy.fluorescence import Bandpass, Label
from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

# %%
# Label one bead population
# -------------------------
# Use the Alexa Fluor 488 reference lifetime of 4.1 ns and quantum yield of
# 0.92. For this timing demonstration we approximate absorption at 488 nm
# by its peak value at 495 nm and place all emission at 519 nm.
# Keep the bead size, refractive index and concentration equal in both populations.

instrument = facs_canto(include_shot_noise=False, include_rin_noise=False)
dye = alexa_fluor_488()
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
# accepts fluorescence from 515 through 545 nm, including the 519 nm
# emission bin. Optical noise and green PMT dark current are disabled to make the
# relationship between individual events and pulses visible.

optical_filter = Bandpass(center=530 * ureg.nm, width=30 * ureg.nm)
green = pmt(
    name="green",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.8,
    signals=("fluorescence",),
    optical_filter=optical_filter,
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
    nrows=3,
    ncols=1,
    sharex=True,
    figsize=(8, 5),
    height_ratios=(1, 2, 2),
    layout="constrained",
)
for row, events in enumerate(record.event_collection):
    arrivals = events.get_quantity("Time").m_as("microsecond")
    axes[0].vlines(arrivals, row - 0.28, row + 0.28)
axes[0].set_yticks([0, 1], ["Labeled", "Unlabeled"])
axes[0].set_ylim(-0.5, 1.5)
axes[0].set_title("Particle arrivals and detector responses")

analog = record.signal.analog
time = analog["Time"].m_as("microsecond")
axes[1].plot(time, analog["side"].m_as("microvolt"))
axes[1].set_ylabel("Side scatter (µV)")
axes[2].plot(time, analog["green"].m_as("nanovolt"))
axes[2].set_ylabel("Fluorescence (nV)")
axes[2].set_xlabel("Time (µs)")
plt.show()

# %%
# Read simulated labels and trigger on fluorescence
# -------------------------------------------------
# The event collection stores the sampled molecule count for each labeled bead.
# The analog green channel contains the voltage from all particles together.
# Triggering on green selects bright pulses and extracts the corresponding
# time window from every detector. The threshold below is illustrative and
# depends on the peak voltage of this noise-free record.

labeled_events = record.event_collection[0]
counts = labeled_events.get_quantity(label.column_name)
print(f"{len(counts)} labeled beads with {counts.magnitude[0]:.0f} molecules per bead")
threshold = analog["green"].max() / 2
trigger_window = discriminator.DynamicWindow(
    trigger_channel="green",
    threshold=threshold,
    pre_buffer=8,
    post_buffer=8,
)
peak_algorithm = peak_locator.GlobalPeakLocator()
processing = DigitalProcessing(
    discriminator=trigger_window,
    peak_locator=peak_algorithm,
)
processed = record.process(digital_processing=processing)
print(f"Green-triggered segments: {processed.number_of_triggers}")
print(
    "Channels with digitized peaks:", processed.peaks.index.unique("Detector").tolist()
)

# %%
# Compare the same bead with photon shot noise enabled
# ----------------------------------------------------
# Keep the random seed to reproduce the particle arrivals and their positions.
# Turn on photon shot noise and zoom in on the labeled bead nearest the middle
# of the record. The green channel now fluctuates around the deterministic
# pulse. In this example the background and dark current are both zero.

optics.source.include_shot_noise = True
noisy = instrument.acquire(run_time=200 * ureg.microsecond, random_state=42)
arrival_times = labeled_events.get_quantity("Time").m_as("microsecond")
np.testing.assert_array_equal(
    noisy.event_collection[0].get_quantity("Time").m_as("microsecond"), arrival_times
)
center = arrival_times[np.argmin(np.abs(arrival_times - np.median(time)))]
near_bead = np.abs(time - center) <= 4
figure, axis = plt.subplots(figsize=(7, 3.2), layout="constrained")
axis.plot(
    time[near_bead] - center,
    noisy.signal.analog["green"].m_as("nanovolt")[near_bead],
    label="With photon shot noise",
)
axis.plot(
    time[near_bead] - center,
    analog["green"].m_as("nanovolt")[near_bead],
    label="Mean response",
)
axis.set(xlabel="Time from bead arrival (µs)", ylabel="Green voltage (nV)")
axis.legend()
plt.show()
