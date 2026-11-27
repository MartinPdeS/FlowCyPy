"""
Choose a digitizer range for dim and bright pulses
==================================================

A narrow voltage range resolves small changes but can clip bright peaks.
Digitize the same two pulses with three settings to see which peak information
survives. Known input voltages let us measure the errors directly.
"""

import matplotlib.pyplot as plt
import numpy as np
from FlowCyPy.opto_electronics import Digitizer
from FlowCyPy.units import ureg

# %%
# Construct two calibration pulses
# --------------------------------
# Sample at 10 MHz, with both peaks centered on sample times. The pulses are
# well separated and the baseline is zero. These voltages represent the signal
# reaching the ADC after analog amplification.

sampling_rate = 10 * ureg.megahertz
time = np.arange(400) / sampling_rate
time_us = time.m_as("microsecond")
dim = 3 * np.exp(-0.5 * ((time_us - 10) / 0.8) ** 2)
bright = 160 * np.exp(-0.5 * ((time_us - 30) / 1.2) ** 2)
voltage = (dim + bright) * ureg.millivolt

# %%
# Compare fixed ranges and bit depths
# -----------------------------------
# For unsigned output, FlowCyPy maps the two range endpoints to codes zero
# and 2**bits - 1. Convert the codes back to millivolts to compare settings
# on the same physical scale. Count inputs above the upper limit directly.
# A sample at the maximum code alone cannot distinguish clipping from a
# voltage which rounded up to that code.

settings = [(8, 100), (8, 500), (12, 500)]
figure, axes = plt.subplots(1, 2, figsize=(9, 3.6), layout="constrained")
for axis in axes:
    axis.plot(time_us, voltage.m_as("mV"), label="Analog input")

for bits, upper_mv in settings:
    digitizer = Digitizer(
        sampling_rate=sampling_rate,
        bit_depth=bits,
        min_voltage=0 * ureg.mV,
        max_voltage=upper_mv * ureg.mV,
        use_auto_range=False,
        output_signed_codes=False,
    )
    codes = digitizer.digitize_signal(voltage)
    step_mv = upper_mv / (2**bits - 1)
    reconstructed = codes * step_mv
    dim_peak = reconstructed[time_us < 20].max()
    bright_peak = reconstructed[time_us >= 20].max()
    clipped = np.count_nonzero(voltage.m_as("mV") > upper_mv)
    print(
        f"{bits} bits, 0–{upper_mv} mV: {step_mv:.3f} mV/code; "
        f"peaks {dim_peak:.2f} and {bright_peak:.2f} mV; {clipped} samples clipped"
    )
    for axis in axes:
        axis.step(
            time_us, reconstructed, where="mid", label=f"{bits} bits, 0–{upper_mv} mV"
        )

for axis, center, title in zip(
    axes, (10, 30), ("3 mV pulse", "160 mV pulse"), strict=True
):
    axis.set(
        xlim=(center - 4, center + 4),
        xlabel="Time (µs)",
        ylabel="Voltage (mV)",
        title=title,
    )
axes[0].set_ylim(-0.2, 4.5)
axes[0].legend()
plt.show()

# %%
# Read the trade-off
# ------------------
# The 100 mV range flattens the bright peak at full scale. Widening the range
# to 500 mV captures that peak, but at 8 bits the 3 mV peak spans only about
# two codes. At 12 bits the same range gives about 0.122 mV per code.
# The reconstructed heights here isolate ADC error. Detector and amplifier
# noise would also contribute to the uncertainty in a measured peak.
