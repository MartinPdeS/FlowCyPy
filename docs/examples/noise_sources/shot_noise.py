"""
Shot noise
==========

This example demonstrates the effect of different optical power levels on a flow cytometer detector.
We initialize the detector, apply varying optical power levels, and visualize the resulting signals
and their distributions.

"""

import matplotlib.pyplot as plt
from FlowCyPy.detector import Detector
from FlowCyPy import units
import numpy
from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_source_noise = False

# Define optical power levels
optical_powers = [1e-9 * units.watt, 2e-9 * units.watt, 4e-9 * units.watt]  # Powers in watts
sequence_length = 300

# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the optical power levels
for optical_power in optical_powers:
    optical_power_array = numpy.ones(sequence_length) * optical_power

    # Initialize the detector
    detector = Detector(
        name=f"{optical_power.magnitude:.1e} W",
        responsivity=1 * units.ampere / units.watt,
        numerical_aperture=0.2 * units.AU,
        phi_angle=0 * units.degree
    )

    noise_current = detector.get_shot_noise(
        optical_power=optical_power_array,
        wavelength=1550 * units.nanometer,
        bandwidth=10 * units.megahertz
    ).to(units.ampere)

    # Plot the raw signal on the first axis
    ax_signal.step(numpy.arange(sequence_length), noise_current, label=detector.name)

    # Plot the histogram of the raw signal
    ax_hist.hist(noise_current, bins=50, alpha=0.6, label=detector.name)

# Customize the axes
ax_signal.set_title("Raw Signals at Different Optical Powers")
ax_signal.set_ylabel("Signal Voltage (V)")
ax_signal.legend()

ax_hist.set_title("Histogram of Raw Signals")
ax_hist.set_xlabel("Signal Voltage (V)")
ax_hist.set_ylabel("Frequency")
ax_hist.legend()

# Show the plots
plt.tight_layout()
plt.show()
