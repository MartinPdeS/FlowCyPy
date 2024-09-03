"""
Plotting a Gaussian Pulse
==========================

This example demonstrates how to create and visualize a Gaussian pulse using the
`GaussianPulse` class.

The Gaussian pulse is useful for modeling signals in various scientific applications,
such as simulating the response of a detector to a particle passing through a laser beam.
"""

# Import the necessary libraries
import numpy as np
from FlowCytometry import GaussianPulse

# Define the time axis in microseconds (μs)
time = np.linspace(-10, 10, 1000)

# Create a GaussianPulse instance
pulse = GaussianPulse(center=0, height=1.0, width=1.0)

# Generate and plot the pulse
pulse.plot(time)

##############################################################################
# The above plot shows a Gaussian pulse centered at 0 μs with a peak amplitude
# of 1.0 volts and a standard deviation (width) of 1.0 μs. The time axis is
# given in microseconds.
#
# You can adjust the parameters (center, height, width) to see how they affect
# the shape and position of the pulse.
