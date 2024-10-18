"""
Plotting a Gaussian Pulse
==========================

This script demonstrates how to create and visualize a Gaussian pulse using the
`GaussianPulse` class from the `FlowCyPy` library.

A Gaussian pulse is widely used in various scientific fields to model signals such as the
response of a detector to a particle passing through a laser beam or electromagnetic pulses.

Steps:
------
1. Define the time axis.
2. Create a Gaussian pulse using the `GaussianPulse` class.
3. Generate and plot the pulse.
"""

# Step 1: Import necessary libraries
import numpy as np
from FlowCyPy import GaussianPulse

# Step 2: Define the time axis
# ----------------------------
# Define a time axis ranging from -10 to 10 microseconds, with 1000 points.
time = np.linspace(-10, 10, 1000)

# Step 3: Create a Gaussian pulse
# -------------------------------
# Create a GaussianPulse instance with the following parameters:
# - center: The time at which the pulse is centered (0 μs).
# - height: The peak amplitude of the pulse (1.0 volts).
# - width: The standard deviation of the pulse (1.0 μs).
pulse = GaussianPulse(center=0, height=1.0, width=1.0)

# Step 4: Generate and plot the Gaussian pulse
# --------------------------------------------
# Generate the pulse and visualize it using the built-in plot function.
pulse.plot()

"""
Summary:
--------
This script generates a Gaussian pulse centered at 0 μs with a peak amplitude of 1.0 volts
and a standard deviation of 1.0 μs. The pulse is plotted over a time axis ranging from
-10 to 10 μs. Adjust the parameters (center, height, width) to explore how they affect
the shape and position of the pulse.
"""
