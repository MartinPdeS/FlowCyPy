import numpy as np
import pytest

from FlowCyPy.binary.peak_locator import GLOBALPEAKLOCATOR, SLIDINGWINDOWPEAKLOCATOR

# ----------------- HELPER FUNCTIONS -----------------


def generate_peak_signal(length=100, peaks=None, mode="square") -> np.ndarray:
    """
    Generate a 1D signal with square or Gaussian peaks.

    Parameters
    ----------
    length : int
        Length of the signal.
    peaks : list of dicts
        Each dict should have:
            - 'center' (float or int): center of the peak
            - 'height' (float): amplitude of the peak
            - 'width' (float): width of the peak (FWHM for Gaussian)
    mode : str
        One of "square" or "gaussian"

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


# ----------------- TESTS -----------------


def test_sliding_window_basic_peak_detection():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 20, "height": 5, "width": 10},
            {"center": 50, "height": 10, "width": 10},
            {"center": 80, "height": 7, "width": 8},
        ],
    )
    locator = SLIDINGWINDOWPEAKLOCATOR(
        window_size=20, window_step=10, max_number_of_peaks=3
    )
    locator.compute(signal)

    indices = locator.get_metric("Index")
    heights = locator.get_metric("Height")

    assert isinstance(indices, list)
    assert isinstance(heights, list)
    assert len(heights) == 3


def test_sliding_window_with_width_and_area():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 25, "height": 6, "width": 12},
            {"center": 60, "height": 9, "width": 8},
        ],
        mode="gaussian",
    )
    locator = SLIDINGWINDOWPEAKLOCATOR(
        window_size=25,
        window_step=10,
        max_number_of_peaks=5,
        compute_width=True,
        compute_area=True,
        threshold=0.5,
    )
    locator.compute(signal)

    widths = locator.get_metric("Width")
    indices = locator.get_metric("Index")

    assert len(widths) == len(indices)


def test_sliding_window_empty_signal():
    signal = np.zeros(100)
    locator = SLIDINGWINDOWPEAKLOCATOR(window_size=20)
    locator.compute(signal)
    heights = locator.get_metric("Height")
    heights = np.asarray(heights)
    assert np.all(heights == 0.0) or np.all(np.isnan(heights))


def test_sliding_window_rejects_non_1d_input():
    locator = SLIDINGWINDOWPEAKLOCATOR(window_size=10)
    bad_input = np.zeros((10, 10))
    with pytest.raises(TypeError):
        locator.compute(bad_input)


# === GLOBALPEAKLOCATOR tests ===


def test_global_peak_basic():
    signal = generate_peak_signal(
        length=100,
        peaks=[
            {"center": 10, "height": 3, "width": 5},
            {"center": 40, "height": 10, "width": 5},
            {"center": 70, "height": 6, "width": 5},
        ],
    )
    locator = GLOBALPEAKLOCATOR()
    locator.compute(signal)

    indices = locator.get_metric("Index")

    assert isinstance(indices, list)
    assert len(indices) == 1
    assert indices[0] == 38


def test_global_peak_with_width_and_area():
    signal = generate_peak_signal(
        length=100, peaks=[{"center": 50, "height": 10, "width": 10}], mode="gaussian"
    )
    locator = GLOBALPEAKLOCATOR(compute_width=True, compute_area=True)
    locator.compute(signal)

    widths = locator.get_metric("Width")
    areas = locator.get_metric("Area")

    assert not np.isnan(widths[0])
    assert not np.isnan(areas[0])


def test_global_peak_handles_flat_signal():
    signal = np.ones(100)
    locator = GLOBALPEAKLOCATOR()
    locator.compute(signal)

    heights = locator.get_metric("Height")
    indices = locator.get_metric("Index")

    assert len(indices) == 1
    assert heights[0] == 1.0


def test_global_peak_rejects_non_1d_input():
    locator = GLOBALPEAKLOCATOR()
    bad_input = np.ones((10, 10))
    with pytest.raises(TypeError):
        locator.compute(bad_input)


if __name__ == "__main__":
    pytest.main(["-s", "-W", "error", __file__])
