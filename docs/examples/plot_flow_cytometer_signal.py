"""
Simulating Flow Cytometer Signals
==================================

This example demonstrates how to simulate signals from a flow cytometer using
the `FlowCytometer` class.

Flow cytometers generate signals (e.g., forward scatter and side scatter) when
particles pass through a laser beam. These signals can be analyzed to obtain
information about the size, complexity, and other properties of the particles.
"""

# Import the necessary libraries
from FlowCytometry import FlowCytometer

# Create a FlowCytometer instance
cytometer = FlowCytometer(
    n_events=30,
    time_points=1000,
    noise_level=30,
    baseline_shift=0.01,
    saturation_level=10_000,
    n_bins=40,
)

# Simulate the flow cytometer signals
cytometer.simulate_pulse()

# Plot the generated signals
cytometer.plot()

##############################################################################
# The above plot shows simulated raw signals for both Forward Scatter (FSC) and
# Side Scatter (SSC) channels. The signals include realistic features such as
# noise, baseline shifts, and saturation effects.
#
# These signals can be used as a basis for developing and testing signal
# processing algorithms in flow cytometry.
