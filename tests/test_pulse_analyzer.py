import numpy as np
import pytest
from FlowCytometry import PulseAnalyzer

def test_pulse_analyzer_peak_detection():
    """Test peak detection in the pulse analyzer."""
    # Create a synthetic signal with two peaks
    time = np.linspace(0, 10, 1000)
    signal = np.exp(-((time - 3) ** 2) / (2 * 0.1 ** 2)) + np.exp(-((time - 7) ** 2) / (2 * 0.1 ** 2))

    analyzer = PulseAnalyzer(signal, height_threshold=0.5)
    analyzer.find_peaks()

    # Check that two peaks were detected
    assert len(analyzer.peaks) == 2, "Number of detected peaks is not correct."

    # Check that the peaks are located near the expected positions
    assert np.isclose(analyzer.peaks[0], 300, atol=10), "First peak location is incorrect."
    assert np.isclose(analyzer.peaks[1], 700, atol=10), "Second peak location is incorrect."

def test_pulse_analyzer_width_and_area():
    """Test width and area calculation in the pulse analyzer."""
    time = np.linspace(0, 10, 1000)
    signal = np.exp(-((time - 5) ** 2) / (2 * 0.1 ** 2))

    analyzer = PulseAnalyzer(signal, height_threshold=0.5)
    analyzer.find_peaks()
    analyzer.calculate_widths()
    analyzer.calculate_areas()

    # Check that the width is close to the expected value (based on the standard deviation of the Gaussian)
    expected_width = 2 * 0.1 * np.sqrt(2 * np.log(2))  # Full width at half maximum (FWHM)
    assert np.isclose(analyzer.widths[0], expected_width, atol=0.02), "Width is incorrect."

    # Check that the area is close to the expected value (integral of the Gaussian)
    expected_area = np.sqrt(2 * np.pi) * 0.1  # Area under the Gaussian curve
    assert np.isclose(analyzer.areas[0], expected_area, atol=0.1), "Area is incorrect."

if __name__ == '__main__':
    pytest.main([__file__])