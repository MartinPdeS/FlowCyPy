import numpy as np
import pytest
from FlowCyPy import Detector
from FlowCyPy import units
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True

default_digitizer = SignalDigitizer(
    bit_depth=1024,
    saturation_levels=[0 * units.volt, 1e30 * units.volt],
    sampling_rate=1e6 * units.hertz,  # High sampling frequency
)

@pytest.fixture
def default_detector_shot_noise():
    """Fixture to create a default detector with shot noise enabled."""
    return Detector(
        name='shot_noise_detector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,  # Responsivity in A/W
    )

@pytest.fixture
def default_detector_dark_current():
    """Fixture to create a default detector with dark current noise enabled."""
    detector = Detector(
        name='dark_current_noise_detector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,  # Responsivity in A/W
        dark_current=10e-2 * units.ampere,  # Dark current of 10 nA
    )

    return detector


def test_shot_noise_generation(default_detector_shot_noise):
    """Test that shot noise is generated and not zero for a detector."""
    # Generate photon shot noise
    NoiseSetting.include_shot_noise = True
    NoiseSetting.include_dark_current_noise = False
    NoiseSetting.include_source_noise = False

    detector = default_detector_shot_noise

    time_series = default_digitizer.get_time_series(
        run_time=100 * units.microsecond
    )

    optical_power = np.linspace(1e-3, 3e-3, len(time_series)) * units.watt

    shot_noise = detector.get_shot_noise(optical_power=optical_power, wavelength=1550 * units.nanometer, bandwidth=default_digitizer.bandwidth)

    # # Assert that the shot noise is generated and is not zero
    assert np.std(shot_noise) > 0 * units.ampere, "Shot noise variance is zero, indicating no noise generated."


def test_dark_current_noise_generation(default_detector_dark_current):
    """Test that dark current noise is generated and not zero for a detector."""
    NoiseSetting.include_shot_noise = False
    NoiseSetting.include_dark_current_noise = True
    NoiseSetting.include_source_noise = False

    # Initialize the raw signal
    detector = default_detector_dark_current

    # dataframe = detector.get_initialized_signal(run_time=100 * units.microsecond, sampling_rate=default_digitizer.sampling_rate)

    time_series = default_digitizer.get_time_series(
        run_time=100 * units.microsecond
    )

    sequence_length = len(time_series)

    dark_current_noise = detector.get_dark_current_noise(sequence_length, bandwidth=default_digitizer.bandwidth)

    # Assert that dark current noise is added to the signal
    assert np.std(dark_current_noise) > 0 * units.ampere, "Dark current noise variance is zero, indicating no noise generated."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
