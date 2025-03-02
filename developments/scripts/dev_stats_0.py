"""
Effect of Optical Power on Detector Signal
==========================================

This example demonstrates the effect of different optical power levels on a flow cytometer detector.
We initialize the detector, apply varying optical power levels, and visualize the resulting signals
and their distributions.

"""
import numpy
import matplotlib.pyplot as plt
from FlowCyPy.detector import Detector
from FlowCyPy.units import watt, ohm, ampere, second, hertz, degree, AU, millivolt, kelvin, megahertz
import scipy.stats as stats
from FlowCyPy.signal_digitizer import SignalDigitizer


from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True
NoiseSetting.include_shot_noise = True
NoiseSetting.include_dark_current_noise = False
NoiseSetting.include_thermal_noise = False
NoiseSetting.include_RIN_noise = False

# Define optical power levels
# optical_powers = [1e-12 * watt, 1e-9 * watt, 5e-9 * watt, 1e-8 * watt]  # Powers in watts
optical_powers = [0.3e-11 * watt, 1e-8 * watt]  # Powers in watts

signal_digitizer = SignalDigitizer(
    bit_depth='14bit',
    saturation_levels='auto',
    sampling_freq=2 * megahertz,           # Sampling frequency: 60 MHz
)

# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the optical power levels
for optical_power in optical_powers:
    # Initialize the detector
    detector = Detector(
        name=f"{optical_power.magnitude:.1e} W",
        responsitivity=1 * ampere / watt,  # Responsitivity (current per power)
        resistance=500 * ohm,              # Load resistance
        numerical_aperture=0.2 * AU,      # Numerical aperture
        phi_angle=0 * degree,              # Detector orientation angle
        temperature=300 * kelvin,
        dark_current=0.00001 * ampere,
        signal_digitizer=signal_digitizer
    )

    # Initialize the raw signal
    detector.init_raw_signal(run_time=30000e-6 * second)

    # Add optical power to the raw signal
    detector._add_optical_power_to_raw_signal(optical_power=optical_power)
    # detector._add_thermal_noise_to_raw_signal()
    # detector._add_dark_current_noise_to_raw_signal()

    print()

    detector.capture_signal()

    # Plot the raw signal on the first axis
    detector.plot(ax=ax_signal, show=False)

    # Plot the histogram of the raw signal
    signal = detector.dataframe['DigitizedSignal']
    ax_hist.hist(signal, bins='auto', alpha=0.6, label=detector.name)

    mean = numpy.mean(signal)
    variance = numpy.var(signal)
    skewness = stats.skew(signal)
    kurotosis = stats.kurtosis(signal, fisher=True)

    print(mean, mean**2 / 2, variance, skewness, kurotosis)

# Customize the axes
ax_signal.set_title("Raw Signals at Different Optical Powers")
ax_signal.set_ylabel("Signal")
ax_signal.legend()

ax_hist.set_title("Histogram of Raw Signals")
ax_hist.set_xlabel("Signal")
ax_hist.set_ylabel("Frequency")
ax_hist.legend()

# Show the plots
plt.tight_layout()
plt.show()
