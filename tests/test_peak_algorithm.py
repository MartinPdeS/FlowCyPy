import numpy as np
import pytest
from FlowCyPy.peak_detector import ThresholdPeakDetector, BasicPeakDetector, MovingAveragePeakDetector
from FlowCyPy import ureg
from FlowCyPy.utils import generate_gaussian_signal


algorithms = [
    BasicPeakDetector(height_threshold=0),
    MovingAveragePeakDetector(threshold=0.5, window_size=3)
]

EXPECTED_PEAKS = np.asarray([1, 3]) * ureg.second
EXPECTED_HEIGHTS = np.asarray([3, 8]) * ureg.volt
EXPECTED_STDS = np.asarray([0.01, 0.01]) * ureg.second

# Parametrize the test with both detector fixtures
@pytest.mark.parametrize("algorithm", algorithms, ids= lambda x: x.__repr__())
def test_peak_detectors(algorithm):

    time_stamp = np.linspace(0, 4, 200)

    detector = generate_gaussian_signal(
        time=time_stamp,
        centers=EXPECTED_PEAKS.magnitude,
        heights=EXPECTED_HEIGHTS.magnitude,
        stds=EXPECTED_STDS.magnitude
    )

    dt = detector.time[1] - detector.time[0]

    # Run the peak detection
    peak_times, heights, widths, areas = algorithm.detect_peaks(
        signal=detector.signal,
        time=detector.time,
        dt=dt,
    )

    # Assert results with helpful error messages
    assert len(peak_times) == len(EXPECTED_PEAKS), f"Expected {len(EXPECTED_PEAKS)} peaks, but got {len(peak_times)}."

    assert np.isclose(heights, EXPECTED_HEIGHTS, atol=1).all(), f"Expected peak heights {EXPECTED_HEIGHTS}, but got {heights}."

if __name__ == '__main__':
    pytest.main([__file__])
