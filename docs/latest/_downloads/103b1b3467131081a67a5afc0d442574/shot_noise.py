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
from FlowCyPy.signal_digitizer import SignalDigitizer

from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

# Define optical power levels
optical_powers = [1e-9 * units.watt, 5e-9 * units.watt, 1e-8 * units.watt]  # Powers in watts

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_freq=1e6 * units.hertz,        # Sampling frequency
)

# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the optical power levels
for optical_power in optical_powers:
    # Initialize the detector
    detector = Detector(
        name=f"{optical_power.magnitude:.1e} W",
        responsitivity=1 * units.ampere / units.watt,  # Responsitivity (current per power)
        resistance=50 * units.ohm,              # Load resistance
        numerical_aperture=0.2 * units.AU,      # Numerical aperture
        phi_angle=0 * units.degree              # Detector orientation angle
    )

    # Initialize the raw signal
    dataframe = detector.get_initialized_signal(run_time=200e-6 * units.second, signal_digitizer=signal_digitizer)

    # Add optical power to the raw signal
    detector._add_optical_power_to_raw_signal(
        signal=dataframe['Signal'],
        optical_power=optical_power,
        wavelength=1550 * units.nanometer
    )

    detector.capture_signal(dataframe['Signal'])

    # Plot the raw signal on the first axis
    ax_signal.step(
        dataframe.index,
        dataframe.Signal.pint.quantity.magnitude
    )

    # Plot the histogram of the raw signal
    ax_hist.hist(dataframe['Signal'], bins=50, alpha=0.6, label=detector.name)

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