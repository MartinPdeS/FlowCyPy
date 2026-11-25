import numpy as np
import pytest
from FlowCyPy.digital_processing import peak_locator


@pytest.mark.parametrize(
    ("locator_type", "options", "expected_metrics"),
    [
        (
            peak_locator.GlobalPeakLocator,
            {},
            {"Index": [2], "Height": [8], "Width": [3], "Area": [19]},
        ),
        (
            peak_locator.SlidingWindowPeakLocator,
            {"window_size": 6, "window_step": 6, "max_number_of_peaks": 2},
            {"Index": [2, 8], "Height": [8, 5], "Width": [3, 2], "Area": [19, 8]},
        ),
    ],
)
def test_peak_locator_with_metrics(locator_type, options, expected_metrics):
    """Locate each maximum and integrate samples within its half-height support."""
    signal = np.array([0, 5, 8, 6, 1, 0, 0, 3, 5, 1, 0, 0], dtype=float)
    locator = locator_type(
        compute_width=True,
        compute_area=True,
        support=peak_locator.PulseSupport(threshold=0.5),
        **options,
    )

    result = locator.get_metrics(signal)

    for name, expected in expected_metrics.items():
        np.testing.assert_array_equal(result[name], expected, err_msg=name)


if __name__ == "__main__":
    pytest.main(["-W", "error", __file__])
