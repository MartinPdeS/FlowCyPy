from FlowCytometry import GaussianPulse

# Example usage of the GaussianPulse class with the new plot function

# Create a GaussianPulse instance
pulse = GaussianPulse(center=5, height=1.0, width=0.5)

# Plot the Gaussian pulse without providing a time axis (default time axis will be used)
pulse.plot()

# Plot the Gaussian pulse with a custom time axis
time_axis = np.linspace(0, 10, 1000)
pulse.plot(time_axis)