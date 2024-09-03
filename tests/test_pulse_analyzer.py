import numpy as np
import pytest
from FlowCytometry import PulseAnalyzer
from FlowCytometry.utils import generate_gaussian_signal

def test_pulse_analyzer_peak_detection():
    """Test peak detection in the pulse analyzer."""
    # Create a synthetic signal with two Gaussian peaks
    time = np.linspace(0, 10, 1000)
    signal = generate_gaussian_signal(time, centers=[3, 7], heights=[1, 1], stds=[0.1, 0.1])

    # Initialize PulseAnalyzer with time and signal
    analyzer = PulseAnalyzer(time=time, signal=signal, height_threshold=0.5)
    analyzer.find_peaks()

    # Check that two peaks were detected
    assert len(analyzer.peaks) == 2, "Number of detected peaks is not correct."

    # Check that the peaks are located near the expected positions
    expected_peak_positions = [3, 7]  # Expected positions in the time array
    for i, peak in enumerate(analyzer.peaks):
        assert np.isclose(peak.time, expected_peak_positions[i], atol=0.1), f"Peak {i+1} location is incorrect."

def test_pulse_analyzer_width_and_area():
    """Test width and area calculation in the pulse analyzer."""
    # Create a synthetic signal with one Gaussian peak
    std = 0.1
    time = np.linspace(0, 20, 1000)
    signal = generate_gaussian_signal(time, centers=[5], heights=[1], stds=[std])

    # Initialize PulseAnalyzer with time and signal
    analyzer = PulseAnalyzer(time=time, signal=signal, height_threshold=0.5)
    analyzer.find_peaks()
    analyzer.calculate_widths()
    analyzer.calculate_areas()

    # Check that the width is close to the expected value (based on the standard deviation of the Gaussian)
    expected_width = 2 * np.sqrt(2 * np.log(2)) * std  # Full width at half maximum (FWHM)
    measured_width = analyzer.peaks[0].width
    assert np.isclose(measured_width, expected_width, atol=0.02), (
        f"Measured width: [{measured_width:.2e}] does not match expected value: [{expected_width:.2e}]."
    )

    # Check that the area is close to the expected value (integral of the Gaussian)
    expected_area = np.sqrt(2 * np.pi) * std  # Area under the Gaussian curve
    measured_area = analyzer.peaks[0].area
    assert np.isclose(measured_area, expected_area, atol=0.1), (
        f"Measured area: [{measured_area:.2e}] does not match expected value: [{expected_area:.2e}]."
    )

if __name__ == '__main__':
    pytest.main([__file__])
