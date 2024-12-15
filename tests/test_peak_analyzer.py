import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch

# Importing from FlowCyPy
from FlowCyPy import EventCorrelator, FlowCytometer, Detector, Scatterer, GaussianBeam, peak_locator, distribution
from FlowCyPy.units import second, volt, hertz, watt, degree, micrometer, meter, particle, milliliter, ampere, AU, RIU
from FlowCyPy.population import Population
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.utils import generate_dummy_detector

# Seed for reproducibility
np.random.seed(10)


# Fixtures
@pytest.fixture
def flow_cell():
    return FlowCell(
        flow_speed=0.2 * meter / second,
        flow_area=1e-6 * meter * meter,
        run_time=1e-3 * second,
    )


@pytest.fixture
def default_size_distribution():
    return distribution.Normal(
        mean=1.0 * micrometer,
        std_dev=0.1 * micrometer
    )


@pytest.fixture
def default_ri_distribution():
    return distribution.Normal(
        mean=1.0 * RIU,
        std_dev=0.1 * RIU
    )


@pytest.fixture
def default_population(default_size_distribution, default_ri_distribution):
    return Population(
        size=default_size_distribution,
        refractive_index=default_ri_distribution,
        name="Default population"
    )


@pytest.fixture
def default_scatterer(flow_cell, default_population):
    scatterer = Scatterer()

    scatterer.add_population(default_population, particle_count=3e+5 * particle / milliliter)

    scatterer.initialize(flow_cell=flow_cell)

    return scatterer


@pytest.fixture
def default_source():
    return GaussianBeam(
        numerical_aperture=1 * AU,
        wavelength=1550e-9 * meter,
        optical_power=1e-3 * watt,
    )


@pytest.fixture
def default_detector():
    """Creates a default detector with common properties."""
    def create_detector(name):
        return Detector(
            name=name,
            numerical_aperture=1 * AU,
            phi_angle=0 * degree,
            responsitivity=1 * ampere / watt,
            sampling_freq=1e5 * hertz,
            noise_level=0 * volt,
            saturation_level=1 * volt,
            baseline_shift=0.0 * volt,
            n_bins='12bit',
        )
    return create_detector


@pytest.fixture
def default_cytometer(default_source, default_scatterer, default_detector):
    """Fixture for a default cytometer with two detectors."""
    detectors = [default_detector('0'), default_detector('1')]

    cytometer = FlowCytometer(
        source=default_source,
        detectors=detectors,
        scatterer=default_scatterer,
        coupling_mechanism='mie'
    )
    cytometer.simulate_pulse()
    return cytometer


# Algorithm setup
algorithm = peak_locator.MovingAverage(
    threshold=0.001 * volt,
    window_size=0.8 * second,
)


# API Test: Ensure peak detection API works correctly
def test_analyzer_peak_detection_api(default_cytometer):
    """Test peak detection API of the EventCorrelator."""
    time = np.linspace(0, 10, 1000) * second
    detector_0 = generate_dummy_detector(
        time=time, centers=[3, 7, 8], heights=[1, 1, 4], stds=[0.1, 0.1, 1]
    )
    detector_1 = generate_dummy_detector(
        time=time, centers=[3.05, 7, 5], heights=[1, 2, 4], stds=[0.1, 0.1, 1]
    )

    algorithm = peak_locator.MovingAverage(
        threshold=0.001 * volt,
        window_size=0.8 * second,
    )

    default_cytometer.detectors = [detector_0, detector_1]
    detector_0.set_peak_locator(algorithm)
    detector_1.set_peak_locator(algorithm)

    analyzer = EventCorrelator(default_cytometer)
    analyzer.run_analysis()
    analyzer.get_coincidence(margin=0.1 * second)

    assert len(analyzer.coincidence[detector_0.name]) == 2, "Number of detected peaks is incorrect."
    expected_peak_positions = [3, 7] * second
    assert np.all(np.isclose(analyzer.coincidence[detector_0.name]['PeakTimes'], expected_peak_positions, atol=0.1 * second)), \
        f"Peak locations are incorrect: {analyzer.coincidence[detector_0.name]['PeakTimes']}"


# Test Plottings: Ensure plotting functions work correctly
@patch('matplotlib.pyplot.show')
def test_analyzer_plotting(mock_show, default_cytometer):
    """Test plotting functionality of the EventCorrelator."""
    time = np.linspace(0, 10, 1000) * second
    detector_0 = generate_dummy_detector(time=time, centers=[3, 7, 8, 9], heights=[1, 1, 4, 3], stds=[0.1, 0.1, 1, 0.1])
    detector_1 = generate_dummy_detector(time=time, centers=[3.05, 7, 5, 9], heights=[1, 2, 4, 2], stds=[0.1, 0.1, 1, 0.1])
    default_cytometer.detectors = [detector_0, detector_1]

    detector_0.set_peak_locator(algorithm)
    detector_1.set_peak_locator(algorithm)

    default_cytometer.plot(add_peak_locator=True)

    correlator = EventCorrelator(default_cytometer)
    correlator.run_analysis()
    correlator.get_coincidence(margin=1e-6 * second)

    correlator.display_features()
    plt.close()

    detector_1.plot(add_peak_locator=True)
    plt.close()

    correlator.plot()
    plt.close()


# Test Pulse Width Analysis: Ensure width calculation is accurate
def test_pulse_width_analysis(default_cytometer):
    """Test pulse width calculation in the EventCorrelator."""
    n_peaks = 4
    centers = np.linspace(1, 8, n_peaks)
    stds = np.random.rand(n_peaks) * 0.1
    time = np.linspace(0, 10, 1000) * second
    detector_0 = generate_dummy_detector(time=time, centers=centers, heights=np.random.rand(n_peaks), stds=stds)
    detector_1 = generate_dummy_detector(time=time, centers=centers, heights=np.random.rand(n_peaks), stds=stds)

    default_cytometer.detectors = [detector_0, detector_1]

    detector_0.set_peak_locator(algorithm)
    detector_1.set_peak_locator(algorithm)

    analyzer = EventCorrelator(default_cytometer)
    analyzer.run_analysis()
    analyzer.get_coincidence(margin=1e-6 * second)

    expected_widths = 2 * np.sqrt(2 * np.log(2)) * stds * second
    measured_widths = analyzer.coincidence[detector_0.name].Widths.values

    assert np.allclose(measured_widths.numpy_data, expected_widths.magnitude, atol=0.5 * 10), \
        f"Measured widths: {measured_widths.numpy_data} do not match expected: {expected_widths}."


# Test Pulse Heights: Ensure height calculation is accurate
def test_pulse_height_analysis(default_cytometer):
    """Test pulse height calculation in the EventCorrelator."""
    n_peaks = 2
    centers = np.linspace(1, 8, n_peaks)
    heights = np.random.rand(n_peaks)
    time = np.linspace(0, 10, 1000) * second
    detector_0 = generate_dummy_detector(time=time, centers=centers, heights=heights, stds=np.random.rand(n_peaks) * 0.1)
    detector_1 = generate_dummy_detector(time=time, centers=centers, heights=heights, stds=np.random.rand(n_peaks))

    default_cytometer.detectors = [detector_0, detector_1]

    detector_0.set_peak_locator(algorithm)
    detector_1.set_peak_locator(algorithm)

    analyzer = EventCorrelator(default_cytometer)
    analyzer.run_analysis()
    analyzer.get_coincidence(margin=1e-1 * second)

    measured_heights = analyzer.coincidence[detector_0.name].Heights.values

    assert np.allclose(measured_heights.numpy_data, heights, atol=0.1), \
        f"Measured heights: {measured_heights.numpy_data} do not match expected: {heights}."


# Test Pulse Area: Ensure area calculation is accurate
def test_pulse_area_analysis(default_cytometer):
    """Test pulse area calculation in the EventCorrelator."""
    n_peaks = 4
    centers = np.linspace(1, 8, n_peaks)
    stds = np.random.rand(n_peaks) * 0.1
    heights = 1 + np.random.rand(n_peaks)
    time = np.linspace(0, 10, 1000) * second
    detector_0 = generate_dummy_detector(time=time, centers=centers, heights=heights, stds=stds)
    detector_1 = generate_dummy_detector(time=time, centers=centers, heights=heights, stds=stds)

    default_cytometer.detectors = [detector_0, detector_1]

    detector_0.set_peak_locator(algorithm, compute_peak_area=True)
    detector_1.set_peak_locator(algorithm, compute_peak_area=True)

    analyzer = EventCorrelator(default_cytometer)
    analyzer.run_analysis(compute_peak_area=True)

    analyzer.get_coincidence(margin=1e-6 * second)

    expected_area = np.sqrt(2 * np.pi) * stds * second * volt
    measured_area = analyzer.coincidence[detector_0.name].Areas.values

    assert np.allclose(measured_area.numpy_data, expected_area.magnitude, atol=0.5 * 100), f"Measured areas: {measured_area.numpy_data} do not match expected: {expected_area.magnitude}."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
