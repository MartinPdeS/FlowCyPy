"""
Effect of Optical Power on Detector Signal
==========================================

This example demonstrates the effect of different optical power levels on a flow cytometer detector.
We initialize the detector, apply varying optical power levels, and visualize the resulting signals
and their distributions.

"""

import matplotlib.pyplot as plt
from FlowCyPy.detector import Detector
from FlowCyPy.units import watt, ohm, ampere, second, hertz, degree, AU

from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

# Define optical power levels
optical_powers = [1e-9 * watt, 5e-9 * watt, 1e-8 * watt]  # Powers in watts

# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the optical power levels
for optical_power in optical_powers:
    # Initialize the detector
    detector = Detector(
        name=f"{optical_power.magnitude:.1e} W",
        responsitivity=1 * ampere / watt,  # Responsitivity (current per power)
        resistance=50 * ohm,              # Load resistance
        numerical_aperture=0.2 * AU,      # Numerical aperture
        sampling_freq=1e6 * hertz,        # Sampling frequency
        phi_angle=0 * degree              # Detector orientation angle
    )

    # Initialize the raw signal
    detector.init_raw_signal(run_time=200e-6 * second)

    # Add optical power to the raw signal
    detector._add_optical_power_to_raw_signal(optical_power=optical_power)

    # Plot the raw signal on the first axis
    detector.plot(ax=ax_signal, add_raw=True, add_captured=False, show=False)

    # Plot the histogram of the raw signal
    ax_hist.hist(detector.dataframe['RawSignal'], bins=50, alpha=0.6, label=detector.name)

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
