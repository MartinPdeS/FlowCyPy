"""
Compare intensity noise from two co-located lasers
==================================================

Can a fluctuation in a bead pulse be traced back to one laser?
Acquire the same beads twice, switching relative intensity noise (RIN)
on and off. Two PMTs collect 405 nm scatter at different angles and a
third collects 488 nm scatter at 90 degrees. Each narrow bandpass
isolates one excitation line.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.fluorescence import Bandpass
from FlowCyPy.opto_electronics import Amplifier, Laser
from FlowCyPy.samples.beads import microbeads
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

# %%
# Use illustrative RIN densities that make the effect visible. With a 10 MHz
# sampling rate and 5 MHz noise bandwidth, −90 and −100 dB/Hz give about
# 7.1% and 2.2% RMS fractional intensity noise, respectively.

violet = Laser(wavelength=405 * ureg.nm, optical_power=8 * ureg.mW, rin=-90 * ureg.dB_per_Hz)
blue = Laser(wavelength=488 * ureg.nm, optical_power=20 * ureg.mW, rin=-100 * ureg.dB_per_Hz)
instrument = facs_canto(lasers=[violet, blue], include_shot_noise=False)
optics = instrument.opto_electronics
optics.detectors = [
    pmt(name=name, phi_angle=angle * ureg.degree, numerical_aperture=0.3,
        optical_filter=Bandpass(center=laser.wavelength, width=10 * ureg.nm),
        dark_current=0 * ureg.ampere)
    for name, angle, laser in [
        ("Violet side", 90, violet), ("Violet forward", 0, violet), ("Blue side", 90, blue)
    ]
]
# An ideal transimpedance amplifier preserves the sample-by-sample fluctuations.
optics.amplifier = Amplifier(gain=10 * ureg.volt / ureg.ampere, bandwidth=None)
beads = microbeads(name="Beads", diameter=300 * ureg.nm, refractive_index=1.59,
                   concentration=2e7 * ureg.particle / ureg.mL)
instrument.fluidics.scatterer_collection.add_population(beads)

noisy_record = instrument.acquire(run_time=2 * ureg.ms, random_state=42)
noisy_record.plot_analog(include_scatterer=False)
plt.show()
optics.source.include_rin_noise = False
reference_record = instrument.acquire(run_time=2 * ureg.ms, random_state=42)
noisy = noisy_record.signal.analog
reference = reference_record.signal.analog

# %%
# Compare the two side-scatter channels around an isolated bead. The quiet
# acquisition uses identical particle arrivals. Each subplot uses its own
# voltage scale since the two lasers deliver different scatter powers.

time = reference["Time"].m_as("microsecond")
arrivals = np.sort(reference_record.event_collection[0].get_quantity("Time").m_as("microsecond"))
gaps = np.diff(arrivals, prepend=time[0], append=time[-1])
center = arrivals[np.argmax(np.minimum(gaps[:-1], gaps[1:]))]
window = np.abs(time - center) <= 3
figure, axes = plt.subplots(2, 1, sharex=True, layout="constrained")
for axis, channel in zip(axes, ("Violet side", "Blue side"), strict=True):
    axis.plot(time[window] - center, noisy[channel].m_as("microvolt")[window], label="RIN on")
    axis.plot(time[window] - center, reference[channel].m_as("microvolt")[window], label="RIN off")
    axis.set(title=channel, ylabel="Voltage (µV)")
axes[0].legend()
axes[-1].set_xlabel("Time from bead arrival (µs)")
plt.show()

# %%
# For all pulses, calculate the fractional change at each sample. Keep
# samples above 10% of the reference peak in every channel to avoid dividing
# by a near-zero signal. A shared laser gives the same fractional change at
# both detectors. The two separate lasers give an uncorrelated cloud.

channels = [detector.name for detector in optics.detectors]
quiet = np.column_stack([reference[channel].m_as("V") for channel in channels])
measured = np.column_stack([noisy[channel].m_as("V") for channel in channels])
inside = (quiet > 0.1 * quiet.max(axis=0)).all(axis=1)
violet_side, violet_forward, blue_side = (100 * (measured[inside] / quiet[inside] - 1)).T

figure, axes = plt.subplots(1, 2, sharex=True, sharey=True, layout="constrained")
for axis, other, label in zip(
    axes, (violet_forward, blue_side), ("405 nm forward scatter", "488 nm side scatter"), strict=True
):
    axis.scatter(violet_side, other, s=5)
    correlation = np.corrcoef(violet_side, other)[0, 1]
    axis.set(title=f"{label}\nr = {correlation:.2f}", xlabel="405 nm side scatter change (%)")
axes[0].set_ylabel("Other channel change (%)")
plt.show()
