import numpy as np
import pytest
from FlowCytometry import GaussianPulse
from unittest.mock import patch
import matplotlib.pyplot as plt

def test_gaussian_pulse_generation():
    """Test the generation of a Gaussian pulse."""
    pulse = GaussianPulse(center=0, height=1.0, width=1.0)
    time = np.linspace(-5, 5, 1000)
    generated_pulse = pulse.generate(time)

    # Check that the generated pulse has the correct maximum value
    assert np.isclose(np.max(generated_pulse), 1.0), "Pulse height does not match expected value."

    # Check that the pulse is symmetric around the center
    half = len(time) // 2
    assert np.isclose(generated_pulse[half], generated_pulse[-half]), "Pulse is not symmetric around the center."

    # Check that the pulse has the correct shape (bell curve)
    assert generated_pulse[0] < generated_pulse[half], "Pulse does not have the correct bell curve shape."


@patch('matplotlib.pyplot.show')
def test_gaussian_pulse_plot(mock_show):
    """Test the plotting of a Gaussian pulse."""
    pulse = GaussianPulse(center=0, height=1.0, width=1.0)
    time = np.linspace(-5, 5, 1000)

    # Since we can't directly test the plot, we ensure that the plot method runs without error
    pulse.plot(time)

    plt.close()


if __name__ == '__main__':
    pytest.main([__file__])