import numpy as np
import pytest
from FlowCyPy import Detector
from FlowCyPy.units import (
    ampere, watt, hertz, ohm, kelvin, volt, microsecond, degree, AU
)


@pytest.fixture
def default_detector_shot_noise():
    """Fixture to create a default detector with shot noise enabled."""
    detector = Detector(
        name='shot_noise_detector',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,  # Responsivity in A/W
        sampling_freq=1e6 * hertz,  # High sampling frequency to test shot noise
        resistance=50 * ohm,
        temperature=300 * kelvin,
    )
    detector.init_raw_signal(run_time=1 * microsecond)

    return detector


@pytest.fixture
def default_detector_thermal_noise():
    """Fixture to create a default detector with thermal noise enabled."""
    detector = Detector(
        name='thermal_noise_detector',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,  # Responsivity in A/W
        sampling_freq=1e6 * hertz,  # High sampling frequency
        resistance=50 * ohm,  # Resistance for thermal noise
        temperature=300 * kelvin,  # Typical room temperature
    )

    detector.init_raw_signal(run_time=1 * microsecond)

    return detector


@pytest.fixture
def default_detector_dark_current():
    """Fixture to create a default detector with dark current noise enabled."""
    detector = Detector(
        name='dark_current_noise_detector',
        numerical_aperture=1 * AU,
        phi_angle=90 * degree,
        responsitivity=1 * ampere / watt,  # Responsivity in A/W
        sampling_freq=1e6 * hertz,  # High sampling frequency
        dark_current=10e-2 * ampere,  # Dark current of 10 nA
        temperature=300 * kelvin,
    )

    detector.init_raw_signal(run_time=1 * microsecond)

    return detector


def test_shot_noise_generation(default_detector_shot_noise):
    """Test that shot noise is generated and not zero for a detector."""
    # Generate photon shot noise
    default_detector_shot_noise.init_raw_signal(run_time=100 * microsecond)

    test_optical_power = np.linspace(1e-3, 3e-3, len(default_detector_shot_noise.dataframe)) * watt

    shot_noise = default_detector_shot_noise._add_optical_power_to_raw_signal(optical_power=test_optical_power)

    # # Assert that the shot noise is generated and is not zero
    assert np.std(shot_noise) > 0 * volt, "Shot noise variance is zero, indicating no noise generated."


def test_thermal_noise_generation(default_detector_thermal_noise):
    """Test that thermal noise is generated and not zero for a detector."""
    # Initialize the raw signal
    default_detector_thermal_noise.init_raw_signal(run_time=100 * microsecond)

    thermal_noise = default_detector_thermal_noise._add_thermal_noise_to_raw_signal()
    # Generate thermal noise and capture signal
    default_detector_thermal_noise.capture_signal()

    # Assert that thermal noise is added to the signal
    assert np.std(thermal_noise) > 0 * volt, "Thermal noise variance is zero, indicating no noise generated."


def test_dark_current_noise_generation(default_detector_dark_current):
    """Test that dark current noise is generated and not zero for a detector."""
    # Initialize the raw signal
    default_detector_dark_current.init_raw_signal(run_time=100 * microsecond)

    dark_current_noise = default_detector_dark_current._add_dark_current_noise_to_raw_signal()

    # Generate dark current noise and capture signal
    default_detector_dark_current.capture_signal()

    # Assert that dark current noise is added to the signal
    assert np.std(dark_current_noise) > 0 * volt, "Dark current noise variance is zero, indicating no noise generated."


def test_combined_noise_generation(default_detector_shot_noise):
    """Test that combined noises are generated for the detector."""
    # Initialize the raw signal with shot noise enabled
    default_detector_shot_noise.init_raw_signal(run_time=100 * microsecond)

    default_detector_shot_noise._add_thermal_noise_to_raw_signal()

    default_detector_shot_noise._add_dark_current_noise_to_raw_signal()

    # Capture the signal and add noise
    default_detector_shot_noise.capture_signal()

    # Assert that the signal contains noise (not zero)
    assert np.std(default_detector_shot_noise.dataframe.RawSignal) > 0 * volt, "Noise variance is zero, indicating no noise added to signal."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
