"""
How much fluorescence passes a 530/30 filter?
=============================================

A nominal 530/30 channel has a center wavelength of 530 nm and a full width of
30 nm. Use two illustrative dye spectra to calculate how much of each dye's
emission enters that channel, including spillover from an orange-emitting dye.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.fluorescence import Bandpass
from FlowCyPy.units import ureg

# %%
# Specify photon counts in wavelength bins
# ----------------------------------------
# Each entry counts photons across a whole bin. The filter acts on the bin's
# representative wavelength, exactly as it does during a FlowCyPy acquisition.
# Both endpoints, 515 and 545 nm, pass the filter.

wavelengths = np.array([505, 515, 525, 535, 545, 555, 565, 575, 585]) * ureg.nm
spectra = {
    "Green dye": np.array([8, 15, 35, 25, 10, 5, 2, 0, 0]),
    "Orange dye": np.array([0, 0, 2, 4, 7, 15, 28, 30, 14]),
}
bandpass = Bandpass(center=530 * ureg.nm, width=30 * ureg.nm)
transmitted = bandpass.transmits(wavelength=wavelengths)

# %%
# Calculate spillover into the green channel
# ------------------------------------------
# Normalize each dye to its own emitted photon count. The hard filter passes
# 85% of the green dye's photons and 13% of the orange dye's photons. These
# fractions describe spectral transmission before geometric collection and
# conversion to detector voltage.

figure, axes = plt.subplots(2, 1, sharex=True, sharey=True, figsize=(7, 5), layout="constrained")
for axis, (name, counts), color in zip(axes, spectra.items(), ["seagreen", "darkorange"], strict=True):
    fraction = counts / counts.sum()
    passed = fraction[transmitted].sum()
    axis.axvspan(515, 545, color="tab:blue", alpha=0.12, label="530/30 passband")
    axis.vlines(wavelengths.m_as("nm"), 0, 100 * fraction, color=color)
    axis.scatter(wavelengths.m_as("nm"), 100 * fraction, color=color)
    axis.set_title(f"{name} · {passed:.0%} of emitted photons transmitted")
    axis.set_ylabel("Photons per bin (%)")
axes[0].legend(loc="upper right")
axes[-1].set_xlabel("Emission wavelength (nm)")
plt.show()
