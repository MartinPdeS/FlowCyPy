"""
Dark Current
============

This example illustrates the impact of varying dark current levels on a flow cytometer detector signal.
The detector is initialized, dark current noise is applied, and the resulting signals are visualized
along with their distributions.

"""

import matplotlib.pyplot as plt
import numpy
from TypedUnit import ureg

from FlowCyPy import SimulationSettings
from FlowCyPy.detector import Detector
from FlowCyPy.signal_generator import SignalGenerator

SimulationSettings.include_noises = True
SimulationSettings.include_shot_noise = False
SimulationSettings.include_dark_current_noise = True
SimulationSettings.include_source_noise = False

# Define dark current levels
dark_currents = [1, 5, 10] * ureg.nanoampere  # Dark current levels in amperes

# %%
# Create a figure for signal visualization
fig, (ax_signal, ax_hist) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

# Loop over the dark current levels
for dark_current in dark_currents:
    detector_name = f"{dark_current.magnitude:.1e} A"

    signal_generator = SignalGenerator(
        n_elements=200, time_units=ureg.second, signal_units=ureg.ampere
    )

    signal_generator.create_zero_signal(detector_name)

    # Initialize the detector
    detector = Detector(
        name=detector_name,
        responsivity=1 * ureg.ampere / ureg.watt,  # Responsitivity (current per power)
        numerical_aperture=0.2 * ureg.AU,  # Numerical aperture
        phi_angle=0 * ureg.degree,  # Detector orientation angle
        dark_current=dark_current,  # Dark current level
    )

    # Add dark current noise to the raw signal
    detector.apply_dark_current_noise(
        signal_generator=signal_generator, bandwidth=10 * ureg.megahertz
    )

    noise_current = signal_generator.get_signal(detector_name)

    # Plot the raw signal on the first axis
    ax_signal.step(x=numpy.arange(200), y=noise_current)

    # Plot the histogram of the raw signal
    ax_hist.hist(noise_current, bins=50, alpha=0.6, label=detector.name)

# Customize the axes
ax_signal.set_title("Raw Signals with Different Dark Current Levels")
ax_signal.set_ylabel("Signal Voltage (A)")
ax_signal.legend()

ax_hist.set_title("Histogram of Raw Signals")
ax_hist.set_xlabel("Signal Voltage (A)")
ax_hist.set_ylabel("Frequency")
ax_hist.legend()


# Show the plots
plt.tight_layout()
_ = plt.show()
