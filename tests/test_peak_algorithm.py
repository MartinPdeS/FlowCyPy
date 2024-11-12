import numpy as np
import pytest
from FlowCyPy import peak_finder
from FlowCyPy.units import Quantity, second, volt
from FlowCyPy.utils import generate_dummy_detector

# Update the algorithm class name to match the new implementation
algorithms = [
    peak_finder.Basic(height_threshold=0.1 * volt, rel_height=0.3),
    peak_finder.MovingAverage(threshold=0.1 * volt, window_size=0.1 * second, min_peak_distance=1e-4 * second),
]

EXPECTED_PEAKS = Quantity(np.array([1, 3]), second)
EXPECTED_HEIGHTS = Quantity(np.array([3, 8]), volt)
EXPECTED_STDS = Quantity(np.array([0.01, 0.01]), second)

# Parametrize the test with the detector
@pytest.mark.parametrize("algorithm", algorithms, ids=lambda x: x.__class__.__name__)
def test_peak_finders(algorithm):

    # Create time_stamp as a Quantity with units
    time_stamp = Quantity(np.linspace(0, 4, 400), second)

    # Generate the Gaussian signal with units
    detector = generate_dummy_detector(
        time=time_stamp,
        centers=EXPECTED_PEAKS,
        heights=EXPECTED_HEIGHTS,
        stds=EXPECTED_STDS
    )

    # Run the peak detection
    algorithm.detect_peaks(detector=detector, compute_area=True)

    # Assert results with helpful error messages
    assert len(detector.peak_properties.index) == len(EXPECTED_PEAKS), (
        f"Expected {len(EXPECTED_PEAKS)} peaks, but got {len(detector.peak_properties.index)}."
    )

    # Allow a tolerance in height comparison due to numerical differences
    assert np.allclose(detector.peak_properties['Heights'].values.numpy_data, EXPECTED_HEIGHTS.magnitude, atol=0.5),\
        f"Expected peak heights {EXPECTED_HEIGHTS}, but got {detector.peak_properties['Heights'].values}."


if __name__ == '__main__':
    pytest.main([__file__])
