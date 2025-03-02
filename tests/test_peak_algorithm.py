import numpy as np
import pytest
from FlowCyPy import units
from FlowCyPy.utils import generate_dummy_detector
from FlowCyPy import peak_locator

# Update the algorithm class name to match the new implementation
algorithms = [
    # peak_locator.DeepPeakLocator(model_name='ROI_128', uncertainty=0.5, n_samples=30, max_number_of_peaks=5),
    peak_locator.BasicPeakLocator(),
    peak_locator.ScipyPeakLocator(height=2 * units.bit_bins, padding_value=-1),
    peak_locator.DerivativePeakLocator(padding_value=-1),
]

EXPECTED_PEAKS = units.Quantity(np.array([1, 3]), units.second)
EXPECTED_HEIGHTS = units.Quantity(np.array([3, 8]), units.bit_bins)
EXPECTED_STDS = units.Quantity(np.array([0.03, 0.03]), units.second)


# Parametrize the test with the detector
@pytest.mark.parametrize("algorithm", algorithms, ids=lambda x: x.__class__.__name__)
def test_peak_finders(algorithm):

    # Create time_stamp as a Quantity with units
    time_stamp = units.Quantity(np.linspace(0, 4, 128), units.second)

    # Generate the Gaussian signal with units
    detector = generate_dummy_detector(
        time=time_stamp,
        centers=EXPECTED_PEAKS,
        heights=EXPECTED_HEIGHTS,
        stds=EXPECTED_STDS
    )

    dataframe = detector.dataframe.pint.dequantify()
    signal = dataframe.Signal.values.T

    # Run the peak detection
    peaks = algorithm(signal)

    peaks = peaks[peaks != -1]

    assert len(peaks) <= 2, "Wrong number of peaks detected."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
