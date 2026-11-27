"""
Measure false triggers with particle-free blanks
================================================

A threshold crossing can come from the optical background alone. Estimate
thresholds on one blank, then count triggered segments in four independent
blanks. Reuse each acquired waveform across thresholds so every setting
sees the same noise realization.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.digital_processing import DigitalProcessing, discriminator
from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

# %%
# Calibrate on a particle-free acquisition
# ----------------------------------------
# Set the bead concentration to zero while retaining the optical background
# and its shot noise. Disable optional analog processing circuits so that
# calibration and triggering both use the amplifier output directly.

instrument = facs_canto(background_power=1 * ureg.nanowatt, include_rin_noise=False)
instrument.opto_electronics.analog_processing = []
blank = microbeads(
    name="blank",
    diameter=300 * ureg.nm,
    refractive_index=1.59,
    concentration=0 * ureg.particle / ureg.milliliter,
)
instrument.fluidics.scatterer_collection.add_population(blank)
duration = 1 * ureg.millisecond
calibration = instrument.acquire(run_time=duration, random_state=11)
voltage = calibration.signal.analog["side"].m_as("nV")
baseline = np.median(voltage)
noise_scale = 1.4826 * np.median(np.abs(voltage - baseline))
multipliers = np.array([2.5, 3.5, 4.5])
thresholds = (baseline + multipliers * noise_scale) * ureg.nanovolt

# %%
# Measure the false-trigger rate on independent blanks
# ----------------------------------------------------
# Keep the calibrated voltage thresholds fixed. Sum segment counts and divide
# by the total recorded time. The segment length and sampling rate affect this
# rate because neighboring high samples can belong to one trigger.

seeds = [21, 22, 23, 24]
counts = np.zeros((len(seeds), len(thresholds)), dtype=int)
for run_index, seed in enumerate(seeds):
    record = instrument.acquire(run_time=duration, random_state=seed)
    assert len(record.event_collection[0]) == 0
    for threshold_index, threshold in enumerate(thresholds):
        trigger_window = discriminator.FixedWindow(
            trigger_channel="side",
            threshold=threshold,
            pre_buffer=4,
            post_buffer=8,
            max_triggers=-1,
        )
        settings = DigitalProcessing(discriminator=trigger_window)
        processed = record.process(digital_processing=settings)
        counts[run_index, threshold_index] = processed.number_of_triggers or 0

total_seconds = len(seeds) * duration.m_as("second")
for multiplier, threshold, total in zip(
    multipliers, thresholds, counts.sum(axis=0), strict=True
):
    print(
        f"{multiplier:g} noise scales: threshold {threshold.m_as('nV'):.3f} nV, "
        f"{total} triggers in {total_seconds * 1000:g} ms, {total / total_seconds:.0f} triggers/s"
    )

figure, axis = plt.subplots(figsize=(6, 3.5), layout="constrained")
axis.bar(multipliers, counts.sum(axis=0) / total_seconds, width=0.5)
axis.set(
    xticks=multipliers,
    xlabel="Threshold above baseline (noise scales)",
    ylabel="Blank triggers per second",
    title="False triggers over four blank acquisitions",
)
plt.show()

# %%
# A zero count means that no crossing was observed during these four
# milliseconds. Longer blanks can resolve rarer false triggers. To measure
# the sensitivity cost of raising a threshold, apply the same voltage levels
# to a sample with known particles.
