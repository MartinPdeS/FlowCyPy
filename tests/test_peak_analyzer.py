import numpy as np
import pytest
from FlowCyPy import Analyzer, ureg
from FlowCyPy.utils import generate_gaussian_signal
from unittest.mock import patch
import matplotlib.pyplot as plt
from FlowCyPy.peak_detector import BasicPeakDetector


def test_pulse_analyzer_peak_detection():
    """Test peak detection in the pulse analyzer."""
    # Create a synthetic signal with two Gaussian peaks
    time = np.linspace(0, 10, 1000)

    detector_0 = generate_gaussian_signal(
        time=time,
        centers=[3, 7],
        heights=[1, 1],
        stds=[0.1, 0.1]
    )

    detector_1 = generate_gaussian_signal(
        time=time,
        centers=[3.05, 7],
        heights=[1, 2],
        stds=[0.1, 0.1]
    )

    # Initialize Analyzer with time and signal
    analyzer = Analyzer(detector_0, detector_1, algorithm=BasicPeakDetector())

    analyzer.run_analysis()

    analyzer.to_dataframe()

    datasets = analyzer.get_coincidence_dataset(coincidence_margin=0.1)

    # Check that two peaks were detected
    assert len(datasets) == 2, "Number of detected peaks is not correct."

    # # Check that the peaks are located near the expected positions
    expected_peak_positions = [3, 7] * ureg.second  # Expected positions in the time array

    assert np.all(np.isclose(datasets[0].time, expected_peak_positions, atol=0.1 * ureg.second)), f"Peak location [{datasets[0].time}] are incorrect. Supposed to be: [{expected_peak_positions}]"

@patch('matplotlib.pyplot.show')
def test_pulse_analyzer_width_and_area(mock_show):
    """Test width and area calculation in the pulse analyzer."""
    # Create a synthetic signal with one Gaussian peak
    stds = [0.1]
    centers = [5]
    heights = [1]

    time = np.linspace(0, 20, 1000)

    detector_0 = generate_gaussian_signal(
        time=time,
        centers=centers,
        heights=heights,
        stds=stds
    )

    detector_1 = generate_gaussian_signal(
        time=time,
        centers=centers,
        heights=heights,
        stds=stds
    )

    # Initialize Analyzer with time and signal
    analyzer = Analyzer(detector_0, detector_1, algorithm=BasicPeakDetector())

    analyzer.run_analysis(compute_peak_area=True)

    datasets = analyzer.get_coincidence_dataset(coincidence_margin=0.1)

    analyzer.display_features()

    analyzer.plot()

    plt.close()

    # Check that the width is close to the expected value (based on the standard deviation of the Gaussian)
    expected_width = 2 * np.sqrt(2 * np.log(2)) * 0.1 * ureg.second  # Full width at half maximum (FWHM)
    measured_width = datasets[0].width[0]

    assert np.isclose(measured_width, expected_width, atol=0.02), (
        f"Measured width: [{measured_width:.2e}] does not match expected value: [{expected_width:.2e}]."
    )

    # Check that the area is close to the expected value (integral of the Gaussian)
    expected_area = np.sqrt(2 * np.pi) * 0.1 * ureg.second * ureg.volt  # Area under the Gaussian curve
    measured_area = datasets[0].area[0]

    assert np.isclose(measured_area, expected_area, atol=0.1), (
        f"Measured area: [{measured_area:.2e}] does not match expected value: [{expected_area:.2e}]."
    )

if __name__ == '__main__':
    pytest.main([__file__])
