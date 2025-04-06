import numpy as np
import pytest

from FlowCyPy.binary.interface_peak_locator import SlidingWindowPeakLocator, GlobalPeakLocator

# === Peak signal generation ===

def generate_peak_signal(length=100, peaks=None, mode="square"):
    """
    Generate a 1D signal with square or Gaussian peaks.

    Parameters:
    - length: int
        Length of the signal array.
    - peaks: list of dicts
        Each dict should have:
            - 'center' (float or int): center of the peak
            - 'height' (float): amplitude of the peak
            - 'width' (float): width of the peak (FWHM for Gaussian)
    - mode: str
        One of "square" or "gaussian"

    Returns:
    - np.ndarray: signal array
    """
    signal = np.zeros(length)
    if not peaks:
        return signal

    x = np.arange(length)

    for peak in peaks:
        center = peak.get("center")
        height = peak.get("height", 1.0)
        width = peak.get("width", 10.0)

        if center is None:
            raise ValueError("Each peak must have a 'center' key")

        if mode == "square":
            start = max(0, int(center - width // 2))
            end = min(length, int(center + width // 2))
            signal[start:end] = height

        elif mode == "gaussian":
            sigma = width / 6
            gaussian = height * np.exp(-0.5 * ((x - center) / sigma) ** 2)
            signal += gaussian

        else:
            raise ValueError("mode must be 'square' or 'gaussian'")

    return signal


# === SlidingWindowPeakLocator tests ===

def test_sliding_window_basic_peak_detection():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 20, "height": 5, "width": 10},
            {"center": 50, "height": 10, "width": 10},
            {"center": 80, "height": 7, "width": 8}
        ]
    )
    locator = SlidingWindowPeakLocator(window_size=20, window_step=10, max_number_of_peaks=3)
    locator(signal)

    indices = locator.get_indices()
    heights = locator.get_heights()

    assert isinstance(indices, np.ndarray)
    assert isinstance(heights, np.ndarray)
    assert heights.shape[0] == 3


def test_sliding_window_with_width_and_area():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 25, "height": 6, "width": 12},
            {"center": 60, "height": 9, "width": 8}
        ],
        mode="gaussian"
    )
    locator = SlidingWindowPeakLocator(
        window_size=25,
        window_step=10,
        max_number_of_peaks=5,
        compute_width=True,
        compute_area=True,
        threshold=0.5
    )
    locator(signal)

    widths = locator.get_widths()
    indices = locator.get_indices()

    assert widths.shape == indices.shape


def test_sliding_window_empty_signal():
    signal = np.zeros(100)
    locator = SlidingWindowPeakLocator(window_size=20)
    locator(signal)
    heights = locator.get_heights()
    assert np.all(heights == 0) or np.all(np.isnan(heights))


def test_sliding_window_rejects_non_1d_input():
    locator = SlidingWindowPeakLocator(window_size=10)
    bad_input = np.zeros((10, 10))
    with pytest.raises(RuntimeError, match="1D"):
        locator(bad_input)


# === GlobalPeakLocator tests ===

def test_global_peak_basic():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 10, "height": 3, "width": 5},
            {"center": 40, "height": 10, "width": 5},
            {"center": 70, "height": 6, "width": 5}
        ]
    )
    locator = GlobalPeakLocator()
    locator(signal)

    indices = locator.get_indices()

    assert isinstance(indices, np.ndarray)
    assert indices.shape[0] == 1
    assert indices[0] == 38


def test_global_peak_with_width_and_area():
    signal = generate_peak_signal(
        length=100,
        peaks=[{"center": 50, "height": 10, "width": 10}],
        mode="gaussian"
    )
    locator = GlobalPeakLocator(compute_width=True, compute_area=True)
    result = locator(signal)

    widths = locator.get_widths()
    areas = locator.get_areas()

    assert not np.isnan(widths[0])
    assert not np.isnan(areas[0])


def test_global_peak_handles_flat_signal():
    signal = np.ones(100)
    locator = GlobalPeakLocator()
    result = locator(signal)

    heights = locator.get_heights()
    indices = locator.get_indices()

    assert indices.shape == (1,)
    assert heights[0] == 1.0


def test_global_peak_rejects_non_1d_input():
    locator = GlobalPeakLocator()
    bad_input = np.ones((10, 10))
    with pytest.raises(RuntimeError, match="1D"):
        locator(bad_input)


if __name__ == "__main__":
    pytest.main(["-s", "-W", "error", __file__])
