import numpy as np
import pytest
from FlowCyPy import Detector
from FlowCyPy import units
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import NoiseSetting

NoiseSetting.include_noises = True

@pytest.fixture
def default_digitizer():
    """Fixture to create a default detector with thermal noise enabled."""
    return SignalDigitizer(
        bit_depth=1024,
        saturation_levels=[0 * units.volt, 1e30 * units.volt],
        sampling_rate=1e6 * units.hertz,  # High sampling frequency
    )

@pytest.fixture
def default_detector_shot_noise(default_digitizer):
    """Fixture to create a default detector with shot noise enabled."""
    detector = Detector(
        name='shot_noise_detector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,  # Responsivity in A/W
        resistance=50 * units.ohm,
        temperature=300 * units.kelvin,
    )

    detector.signal_digitizer = default_digitizer

    return detector



@pytest.fixture
def default_detector_thermal_noise(default_digitizer):
    """Fixture to create a default detector with thermal noise enabled."""
    detector = Detector(
        name='thermal_noise_detector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,  # Responsivity in A/W
        resistance=50 * units.ohm,  # Resistance for thermal noise
        temperature=300 * units.kelvin,  # Typical room temperature
    )
    detector.signal_digitizer = default_digitizer

    return detector


@pytest.fixture
def default_detector_dark_current(default_digitizer):
    """Fixture to create a default detector with dark current noise enabled."""
    detector = Detector(
        name='dark_current_noise_detector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsitivity=1 * units.ampere / units.watt,  # Responsivity in A/W
        dark_current=10e-2 * units.ampere,  # Dark current of 10 nA
        temperature=300 * units.kelvin,
    )
    detector.signal_digitizer = default_digitizer

    return detector


def test_shot_noise_generation(default_detector_shot_noise, default_digitizer):
    """Test that shot noise is generated and not zero for a detector."""
    # Generate photon shot noise
    NoiseSetting.include_shot_noise = True
    NoiseSetting.include_thermal_noise = False
    NoiseSetting.include_dark_current_noise = False
    NoiseSetting.include_RIN_noise = False

    detector = default_detector_shot_noise

    dataframe = detector.get_initialized_signal(run_time=100 * units.microsecond)

    optical_power = np.linspace(1e-3, 3e-3, len(dataframe)) * units.watt

    shot_noise = detector.capture_signal(
        signal=dataframe['Signal'],
        optical_power=optical_power,
        wavelength=1550 * units.nanometer
    )

    # # Assert that the shot noise is generated and is not zero
    assert np.std(shot_noise) > 0 * units.volt, "Shot noise variance is zero, indicating no noise generated."


def test_thermal_noise_generation(default_detector_thermal_noise):
    """Test that thermal noise is generated and not zero for a detector."""
    # Initialize the raw signal
    NoiseSetting.include_shot_noise = False
    NoiseSetting.include_thermal_noise = True
    NoiseSetting.include_dark_current_noise = False
    NoiseSetting.include_RIN_noise = False

    detector = default_detector_thermal_noise

    dataframe = detector.get_initialized_signal(run_time=100 * units.microsecond)
    sequence_length = len(dataframe['Signal'])

    thermal_noise = detector.get_noise_signal(sequence_length)
    # Generate thermal noise and capture signal
    detector.signal_digitizer.capture_signal(dataframe['Signal'])

    # Assert that thermal noise is added to the signal
    assert np.std(thermal_noise) > 0 * units.volt, "Thermal noise variance is zero, indicating no noise generated."


def test_dark_current_noise_generation(default_detector_dark_current):
    """Test that dark current noise is generated and not zero for a detector."""
    NoiseSetting.include_shot_noise = False
    NoiseSetting.include_thermal_noise = False
    NoiseSetting.include_dark_current_noise = True
    NoiseSetting.include_RIN_noise = False

    # Initialize the raw signal
    detector = default_detector_dark_current

    dataframe = detector.get_initialized_signal(run_time=100 * units.microsecond)
    sequence_length = len(dataframe['Signal'])

    dark_current_noise = detector.get_noise_signal(sequence_length)

    # Generate dark current noise and capture signal
    detector.signal_digitizer.capture_signal(dataframe['Signal'])

    # Assert that dark current noise is added to the signal
    assert np.std(dark_current_noise) > 0 * units.volt, "Dark current noise variance is zero, indicating no noise generated."


def test_combined_noise_generation(default_detector_shot_noise):
    """Test that combined noises are generated for the detector."""
    NoiseSetting.include_shot_noise = True
    NoiseSetting.include_thermal_noise = True
    NoiseSetting.include_dark_current_noise = True
    NoiseSetting.include_RIN_noise = True
    # Initialize the raw signal with shot noise enabled
    detector = default_detector_shot_noise

    dataframe = detector.get_initialized_signal(run_time=100 * units.microsecond)
    sequence_length = len(dataframe['Signal'])

    noises = detector.get_noise_signal(sequence_length)

    # Assert that the signal contains noise (not zero)
    assert np.std(noises) > 0 * units.volt, "Noise variance is zero, indicating no noise added to signal."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
