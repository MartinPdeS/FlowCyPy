import numpy as np
import pytest
from TypedUnit import ureg

from FlowCyPy.opto_electronics import Detector
from FlowCyPy.signal_processing import Digitizer
from FlowCyPy import SimulationSettings
from FlowCyPy.signal_generator import SignalGenerator
import FlowCyPy

FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging
SimulationSettings.include_noises = True

# ----------------- CONSTANTS -----------------

N_ELEMENTS = 5000  # Number of elements in the signal
TIME_ARRAY = np.linspace(0.0, 1.0, N_ELEMENTS) * ureg.microsecond  # Time array for the signal generator

# ----------------- FIXTURES -----------------

@pytest.fixture
def signal_generator():
    """
    Returns a SignalGenerator instance with a predefined time array.
    This is used to avoid code duplication in tests.
    """
    signal_generator = SignalGenerator(N_ELEMENTS, time_units=ureg.second, signal_units=ureg.volt)
    signal_generator.add_time(TIME_ARRAY)
    signal_generator.create_zero_signal(signal_name="TestDetector")
    return signal_generator

digitizer = Digitizer(
    bit_depth=1024,
    saturation_levels=[0 * ureg.volt, 1e30 * ureg.volt],
    sampling_rate=1e6 * ureg.hertz,  # High sampling frequency
)

@pytest.fixture
def detector_shot_noise():
    """Fixture to create a default detector with shot noise enabled."""
    return Detector(
        name='TestDetector',
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,  # Responsivity in A/W
    )

@pytest.fixture
def detector_dark_current():
    """Fixture to create a default detector with dark current noise enabled."""
    detector = Detector(
        name='TestDetector',
        numerical_aperture=1 * ureg.AU,
        phi_angle=90 * ureg.degree,
        responsivity=1 * ureg.ampere / ureg.watt,  # Responsivity in A/W
        dark_current=10e-2 * ureg.ampere,  # Dark current of 10 nA
    )

    return detector


# ----------------- TESTS -----------------

def test_shot_noise_generation(detector_shot_noise, signal_generator):
    """Test that shot noise is generated and not zero for a detector."""
    # Generate photon shot noise
    SimulationSettings.include_shot_noise = True
    SimulationSettings.include_dark_current_noise = False
    SimulationSettings.include_source_noise = False

    signal_generator.signal_units = ureg.watt  # Set signal units to watts for shot noise calculation
    signal_generator.add_constant(1e-3 * ureg.watt)  # Add constant optical power to the signal units in ureg.watt

    detector_shot_noise.apply_shot_noise(
        signal_generator=signal_generator,
        wavelength=1550 * ureg.nanometer,
        bandwidth=digitizer.bandwidth
    )

    shot_noise = signal_generator.get_signal("TestDetector")

    # # Assert that the shot noise is generated and is not zero
    assert np.std(shot_noise) > 0 * ureg.watt, "Shot noise variance is zero, indicating no noise generated."


def test_dark_current_noise_generation(detector_dark_current, signal_generator):
    """Test that dark current noise is generated and not zero for a detector."""
    SimulationSettings.include_shot_noise = False
    SimulationSettings.include_dark_current_noise = True
    SimulationSettings.include_source_noise = False

    signal_generator.signal_units = ureg.ampere  # Set signal units to amperes for dark current noise calculation

    detector_dark_current.apply_dark_current_noise(
        signal_generator=signal_generator,
        bandwidth=digitizer.bandwidth
    )

    dark_current_noise = signal_generator.get_signal("TestDetector")

    # Assert that dark current noise is added to the signal
    assert np.std(dark_current_noise) > 0 * ureg.ampere, "Dark current noise variance is zero, indicating no noise generated."


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
