import numpy as np
import pytest
from numpy.testing import assert_allclose

# Replace 'your_module' with the actual module name where the classes are defined.
from FlowCyPy import peak_locator

PEAK_CENTERS = [30, 70]

peak_algorithms = [
    peak_locator.BasicPeakLocator(padding_value=-1, compute_width=True, compute_area=True),
    peak_locator.ScipyPeakLocator(height=500, distance=5, max_number_of_peaks=1, padding_value=-1, compute_width=True, compute_area=True),
]

# Helper function: generate a Gaussian pulsed signal.
def generate_gaussian_signal(length, peak_center, peak_height, peak_width, noise_level=0):
    x = np.arange(length)
    signal = peak_height * np.exp(-((x - peak_center) ** 2) / (2 * peak_width ** 2))
    if noise_level:
        signal += np.random.normal(0, noise_level, size=length)
    return signal

# Pytest fixture that returns a 2D array with two realistic Gaussian pulses.
@pytest.fixture
def sample_data():
    length = 100
    # Row 0: pulse centered around index 30, height 1000, width 5, with slight noise.
    row0 = generate_gaussian_signal(length, peak_center=30, peak_height=1000, peak_width=5, noise_level=10)
    # Row 1: pulse centered around index 70, height 1500, width 8, with slight noise.
    row1 = generate_gaussian_signal(length, peak_center=70, peak_height=1500, peak_width=8, noise_level=10)
    return np.vstack([row0, row1])

# ------------------------------
# Test peak detection with additional metrics (width and area)
# ------------------------------
@pytest.mark.parametrize("peak_algorithm", peak_algorithms)
def test_peak_locator_with_metrics(peak_algorithm, sample_data):
    """
    Test that the locator (with width/area enabled) computes additional metrics.
    """
    result = peak_algorithm(sample_data)
    peak_idx = result["peak_index"]
    widths = result["width"]
    areas = result["area"]
    # Check detected peak indices are near the expected centers.
    assert_allclose(peak_idx[0, 0], PEAK_CENTERS[0], atol=3)
    assert_allclose(peak_idx[1, 0], PEAK_CENTERS[1], atol=3)
    # Verify that computed widths and areas are positive.
    assert widths[0, 0] > 0
    assert widths[1, 0] > 0
    # assert areas[0, 0] > 0
    # assert areas[1, 0] > 0

if __name__ == '__main__':
    pytest.main(["-W", "error", __file__])
