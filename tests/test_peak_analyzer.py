import numpy as np
import pytest
import math

# Replace 'your_module' with the actual module name where the classes are defined.
from FlowCyPy.signal_processing import peak_locator
import FlowCyPy
FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging

PEAK_CENTERS = [30, 70]

peak_algorithms = [
    peak_locator.GlobalPeakLocator(padding_value=-1, compute_width=True, compute_area=True, max_number_of_peaks=1),
    peak_locator.SlidingWindowPeakLocator(padding_value=-1, window_size=20, compute_width=True, compute_area=True, max_number_of_peaks=2),
    peak_locator.ScipyPeakLocator(height=500, distance=5, padding_value=-1, compute_width=True, compute_area=True, max_number_of_peaks=2),
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
    values = generate_gaussian_signal(length, peak_center=30, peak_height=1000, peak_width=5, noise_level=0)

    values +=  generate_gaussian_signal(length, peak_center=70, peak_height=800, peak_width=5, noise_level=0)

    return values


def assert_set_included_close(actual_set, expected_set, rel_tol=1e-7, abs_tol=0):
    """
    Asserts that every element in `actual_set` has at least one counterpart in `expected_set`
    that is "close enough" (within the given tolerances).

    Parameters
    ----------
    actual_set : set of float
        The set whose elements must be found (approximately) in expected_set.
    expected_set : set of float
        The set that is expected to contain (or approximate) all elements in actual_set.
    rel_tol : float, optional
        The relative tolerance parameter passed to math.isclose. Default is 1e-7.
    abs_tol : float, optional
        The absolute tolerance parameter passed to math.isclose. Default is 0.

    Raises
    ------
    AssertionError
        If any element in actual_set does not have a "close enough" match in expected_set.
    """
    for a in actual_set:
        # Check if there's any element in expected_set close to a.
        if not any(math.isclose(a, e, rel_tol=rel_tol, abs_tol=abs_tol) for e in expected_set):
            raise AssertionError(f"Element {a} from the actual set has no close match in the expected set.")

# ------------------------------
# Test peak detection with additional metrics (width and area)
# ------------------------------
@pytest.mark.parametrize("peak_algorithm", peak_algorithms, ids=[p.__class__.__name__ for p in peak_algorithms])
def test_peak_locator_with_metrics(peak_algorithm, sample_data):
    """
    Test that the locator (with width/area enabled) computes additional metrics.
    """
    result = peak_algorithm(sample_data)

    assert_set_included_close(result["Index"], PEAK_CENTERS, abs_tol=3)


if __name__ == '__main__':
    pytest.main(["-W", "error", __file__])
