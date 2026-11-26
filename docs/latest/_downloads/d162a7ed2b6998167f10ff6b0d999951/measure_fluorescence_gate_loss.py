"""
How much fluorescence arrives after the gate closes?
====================================================

Illuminate a dye for 4 ns and close the gate when the light switches off.
Compare prompt emission with the FITC and ATTO 647N preset lifetimes. This controlled
input isolates the detector chain from particle arrivals and beam geometry.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.dyes import atto_647n, fitc
from FlowCyPy.opto_electronics import Amplifier
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg

# %%
# Isolate emission timing
# -----------------------
# Supply the same prompt-equivalent optical power at each dye’s emission
# maximum. This models separate excitations with equal collected power so
# the gate fractions depend only on lifetime. Disable noise and use a constant
# amplifier gain to isolate the dye response. The 128 ns window leaves ample
# time for the tail to decay before the periodic trace repeats.

optics = facs_canto(include_shot_noise=False, include_rin_noise=False).opto_electronics
detector = pmt(
    name="fluorescence",
    phi_angle=90 * ureg.degree,
    numerical_aperture=0.8,
    signals=("fluorescence",),
    dark_current=0 * ureg.ampere,
)
optics.detectors = [detector]
optics.amplifier = Amplifier(gain=1 * ureg.volt / ureg.ampere)

# %%
# Compare two sampling intervals
# ------------------------------
# Each trace has a square input from 16 through 20 ns (right edge excluded).
# The low-level emission key holds the channel name, wavelength in nm, and
# lifetime in seconds. Each plotted step is the mean over one sampling bin.
# Multiplying the summed voltage by the bin width gives the voltage-time area.

# Use an instantaneous response at the FITC wavelength as the reference.
responses = [("Prompt", fitc.emission_maximum, 0 * ureg.ns)]
for preset in (fitc, atto_647n):
    responses.append((preset.name, preset.emission_maximum, preset.lifetime))

figure, axes = plt.subplots(1, 2, figsize=(9, 3.5), sharey=True, layout="constrained")
for axis, bin_ns in zip(axes, (1, 4), strict=True):
    time_ns = np.arange(0, 128, bin_ns)
    edges_ns = np.append(time_ns, 128)
    in_gate = (time_ns >= 16) & (time_ns < 20)
    excitation = in_gate.astype(float) * ureg.nanowatt
    optics.digitizer.sampling_rate = 1 / (bin_ns * ureg.ns)
    for name, wavelength, lifetime in responses:
        lifetime_ns = lifetime.m_as("ns")
        power = {"Time": time_ns * ureg.ns, "fluorescence": np.zeros(time_ns.size) * ureg.watt}
        voltage = optics.convert_optical_power_to_voltage(
            power, emission={("fluorescence", wavelength.m_as("nm"), lifetime.m_as("s")): excitation}
        )["fluorescence"].m_as("nV")
        full_area = voltage.sum() * bin_ns
        gate_fraction = voltage[in_gate].sum() * bin_ns / full_area
        axis.stairs(voltage, edges_ns, label=f"{name} ({lifetime_ns:g} ns)")
        expected = 1 + lifetime_ns / 4 * np.expm1(-4 / lifetime_ns) if lifetime_ns else 1.0
        np.testing.assert_allclose(gate_fraction, expected)
        print(
            f"{name}, {bin_ns} ns bins: {gate_fraction:.1%} in gate, {full_area:.2f} nV ns total"
        )
    axis.axvspan(16, 20, alpha=0.15, label="Open gate")
    axis.set(xlim=(8, 44), xlabel="Time (ns)", title=f"{bin_ns} ns sampling interval")
axes[0].set_ylabel("Mean voltage per bin (nV)")
axes[1].legend()
plt.show()

# %%
# Interpret the gate fraction
# ---------------------------
# During the square excitation, the emission rises as one minus an exponential.
# The shorter ATTO 647N lifetime puts more of its emission inside the gate.
# Both bin widths recover the same fraction because the gate edges align with
# sampling boundaries. The finer grid resolves more of the rise and decay.
