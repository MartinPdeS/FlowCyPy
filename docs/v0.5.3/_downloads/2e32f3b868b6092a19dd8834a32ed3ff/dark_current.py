"""
Effect of Dark Current Noise on Detector Signal
===============================================

This example illustrates the impact of varying dark current levels on a flow cytometer detector signal.
The detector is initialized, dark current noise is applied, and the resulting signals are visualized
along with their distributions.

"""

import matplotlib.pyplot as plt
from FlowCyPy.detector import Detector
from FlowCyPy.units import watt, ohm, ampere, second, hertz, degree, AU, kelvin

from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = False
NoiseSetting.include_dark_current_noise = True
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

# Define dark current levels
dark_currents = [1e-9 * ampere, 5e-9 * ampere, 1e-8 * ampere]  # Dark current levels in amperes

# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the dark current levels
for dark_current in dark_currents:
    # Initialize the detector
    detector = Detector(
        name=f"{dark_current.magnitude:.1e} A",
        responsitivity=1 * ampere / watt,  # Responsitivity (current per power)
        resistance=50 * ohm,              # Load resistance
        numerical_aperture=0.2 * AU,      # Numerical aperture
        sampling_freq=1e6 * hertz,        # Sampling frequency
        phi_angle=0 * degree,             # Detector orientation angle
        temperature=300 * kelvin,         # Detector temperature
        dark_current=dark_current         # Dark current level
    )

    # Initialize the raw signal
    detector.init_raw_signal(run_time=200e-6 * second)

    # Add dark current noise to the raw signal
    detector._add_dark_current_noise_to_raw_signal()

    # Plot the raw signal on the first axis
    detector.plot(ax=ax_signal, add_raw=True, add_captured=False, show=False)

    # Plot the histogram of the raw signal
    ax_hist.hist(detector.dataframe['RawSignal'], bins=50, alpha=0.6, label=detector.name)

# Customize the axes
ax_signal.set_title("Raw Signals with Different Dark Current Levels")
ax_signal.set_ylabel("Signal Voltage (V)")
ax_signal.legend()

ax_hist.set_title("Histogram of Raw Signals")
ax_hist.set_xlabel("Signal Voltage (V)")
ax_hist.set_ylabel("Frequency")
ax_hist.legend()

# Show the plots
plt.tight_layout()
plt.show()
