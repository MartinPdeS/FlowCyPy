import numpy as np
import pytest
from FlowCytometry import FlowCytometer
import matplotlib.pyplot as plt
from unittest.mock import patch

def test_flow_cytometer_simulation():
    """Test the simulation of flow cytometer signals."""
    cytometer = FlowCytometer(n_events=10, time_points=1000, n_bins=100, noise_level=20)
    cytometer.simulate_pulse()

    cytometer.plot()

    # Check that the signals are not all zeros (pulses should add non-zero values)
    assert np.any(cytometer.fsc_raw_signal > 0), "FSC signal is all zeros."
    assert np.any(cytometer.ssc_raw_signal > 0), "SSC signal is all zeros."

    # Check that the noise has been added to the signal
    assert np.var(cytometer.fsc_raw_signal) > 0, "FSC signal variance is zero, indicating no noise added."
    assert np.var(cytometer.ssc_raw_signal) > 0, "SSC signal variance is zero, indicating no noise added."

@patch('matplotlib.pyplot.show')
def test_flow_cytometer_plot(mock_show):
    """Test the plotting of flow cytometer signals."""
    cytometer = FlowCytometer(n_events=10, time_points=1000)
    cytometer.simulate_pulse()

    # Since we can't directly test the plot, we ensure that the plot method runs without error
    cytometer.plot_signals()

    plt.close()

if __name__ == '__main__':
    pytest.main([__file__])