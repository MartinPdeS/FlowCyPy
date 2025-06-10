import numpy as np
import pytest
from FlowCyPy import Detector
from FlowCyPy import units
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import NoiseSetting
from FlowCyPy.signal_generator import SignalGenerator

NoiseSetting.include_noises = True

N_ELEMENTS = 5000  # Number of elements in the signal
TIME_ARRAY = np.linspace(0.0, 1.0, N_ELEMENTS) * units.microsecond  # Time array for the signal generator


@pytest.fixture
def signal_generator():
    """
    Returns a SignalGenerator instance with a predefined time array.
    This is used to avoid code duplication in tests.
    """
    signal_generator = SignalGenerator(N_ELEMENTS, time_units=units.second, signal_units=units.volt)
    signal_generator.add_time(TIME_ARRAY)
    signal_generator.create_zero_signal(signal_name="TestDetector")
    return signal_generator

digitizer = SignalDigitizer(
    bit_depth=1024,
    saturation_levels=[0 * units.volt, 1e30 * units.volt],
    sampling_rate=1e6 * units.hertz,  # High sampling frequency
)

@pytest.fixture
def detector_shot_noise():
    """Fixture to create a default detector with shot noise enabled."""
    return Detector(
        name='TestDetector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,  # Responsivity in A/W
    )

@pytest.fixture
def detector_dark_current():
    """Fixture to create a default detector with dark current noise enabled."""
    detector = Detector(
        name='TestDetector',
        numerical_aperture=1 * units.AU,
        phi_angle=90 * units.degree,
        responsivity=1 * units.ampere / units.watt,  # Responsivity in A/W
        dark_current=10e-2 * units.ampere,  # Dark current of 10 nA
    )

    return detector


def test_shot_noise_generation(detector_shot_noise, signal_generator):
    """Test that shot noise is generated and not zero for a detector."""
    # Generate photon shot noise
    NoiseSetting.include_shot_noise = True
    NoiseSetting.include_dark_current_noise = False
    NoiseSetting.include_source_noise = False

    signal_generator.signal_units = units.watt  # Set signal units to watts for shot noise calculation
    signal_generator.add_constant(1e-3 * units.watt)  # Add constant optical power to the signal units in units.watt

    detector_shot_noise.apply_shot_noise(
        signal_generator=signal_generator,
        wavelength=1550 * units.nanometer,
        bandwidth=digitizer.bandwidth
    )

    shot_noise = signal_generator.get_signal("TestDetector")

    # # Assert that the shot noise is generated and is not zero
    assert np.std(shot_noise) > 0 * units.watt, "Shot noise variance is zero, indicating no noise generated."


def test_dark_current_noise_generation(detector_dark_current, signal_generator):
    """Test that dark current noise is generated and not zero for a detector."""
    NoiseSetting.include_shot_noise = False
    NoiseSetting.include_dark_current_noise = True
    NoiseSetting.include_source_noise = False

    signal_generator.signal_units = units.ampere  # Set signal units to amperes for dark current noise calculation

    detector_dark_current.apply_dark_current_noise(
        signal_generator=signal_generator,
        bandwidth=digitizer.bandwidth
    )

    dark_current_noise = signal_generator.get_signal("TestDetector")

    # Assert that dark current noise is added to the signal
    assert np.std(dark_current_noise) > 0 * units.ampere, "Dark current noise variance is zero, indicating no noise generated."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
