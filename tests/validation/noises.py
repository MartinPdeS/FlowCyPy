import numpy as np
import pytest
from TypedUnit import ureg

import FlowCyPy
from FlowCyPy.opto_electronics import Detector
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.binary.signal_generator import SignalGenerator
from FlowCyPy.signal_processing import Digitizer

FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging

# ----------------- CONSTANTS -----------------

TOLERANCE = 0.05  # Allowable error margin (5%)
N_ELEMENTS = 5000  # Number of elements in the signal
TIME_ARRAY = (
    np.linspace(0.0, 1.0, N_ELEMENTS) * ureg.microsecond
)  # Time array for the signal generator

# ----------------- FIXTURES -----------------


@pytest.fixture
def signal_generator():
    """
    Returns a SignalGenerator instance with a predefined time array.
    This is used to avoid code duplication in tests.
    """
    signal_generator = SignalGenerator(N_ELEMENTS)
    signal_generator.add_time(TIME_ARRAY)
    signal_generator.create_zero_signal(channel="TestDetector")
    return signal_generator


@pytest.fixture
def signal_digitizer():
    """
    Returns a Digitizer instance with default parameters.
    This is used to avoid code duplication in tests.
    """
    return Digitizer(
        bit_depth=1024,
        saturation_levels="auto",
        sampling_rate=1e6 * ureg.hertz,  # Default sampling rate
    )


# Helper function to validate noise
def validate_noise(noise, expected_std, tolerance=TOLERANCE):
    measured_std = np.std(noise)

    assert np.isclose(
        measured_std, expected_std, rtol=tolerance, atol=1e-10
    ), f"Measured noise std {measured_std} does not match expected {expected_std}."


# Test Shot Noise
def test_shot_noise(signal_generator, signal_digitizer):
    """
    Test that shot noise added to the signal matches the theoretical standard deviation.

    Shot noise is computed as the square root of the signal power in the context of the
    detector's responsivity and resistance.
    """
    # Signal and Detector Properties
    optical_power = 0.001 * ureg.milliwatt  # Power in watts

    signal_generator.add_constant(
        optical_power.to("watt").magnitude
    )  # Add constant optical power to the signal

    # Initialize Detector
    detector = Detector(
        name="TestDetector",
        responsivity=1 * ureg.ampere / ureg.watt,  # Responsitivity (current per power)
        numerical_aperture=0.2 * ureg.AU,
        dark_current=1e-12 * ureg.ampere,
        phi_angle=0 * ureg.degree,
    )

    detector.apply_shot_noise(
        signal_generator=signal_generator,
        wavelength=1550 * ureg.nanometer,
        bandwidth=signal_digitizer.bandwidth,
    )

    shot_noised_optical_power = signal_generator.get_signal("TestDetector") * ureg.watt

    # # Step 1: Compute Equivalent Shot Noise in Voltage
    shot_noised_current = shot_noised_optical_power * detector.responsivity

    expected_std = np.sqrt(
        2
        * PhysicalConstant.e
        * signal_digitizer.bandwidth
        * optical_power
        * detector.responsivity
    )  # Shot noise current std

    # Step 2: Measure the actual noise standard deviation
    validate_noise(
        noise=shot_noised_current,
        expected_std=expected_std.to(ureg.ampere),
    )


# Test Dark Current Noise
def test_dark_current_noise(signal_generator, signal_digitizer):
    """
    Test that dark current noise added to the signal matches the theoretical standard deviation.

    Dark current noise arises due to the statistical fluctuations of thermally generated electrons
    in the detector when no light is incident. The noise behaves like shot noise and is proportional
    to the square root of the dark current.
    """
    # Detector Properties
    dark_current = 1e-12 * ureg.ampere  # Dark current in amps

    signal_generator.add_constant(
        dark_current.to("ampere").magnitude
    )  # Add constant optical power to the signal

    # Initialize Detector
    detector = Detector(
        name="TestDetector",
        responsivity=1
        * ureg.ampere
        / ureg.watt,  # Responsitivity (not used here but required)
        numerical_aperture=0.2 * ureg.AU,
        dark_current=dark_current,
        phi_angle=0 * ureg.degree,
    )

    # Generate dark current noise
    detector.apply_dark_current_noise(
        signal_generator=signal_generator, bandwidth=signal_digitizer.bandwidth
    )  # Capture returned noise

    dark_current_noise = signal_generator.get_signal("TestDetector") * ureg.ampere

    # Step 1: Compute Theoretical Dark Current Noise in Voltage
    expected_current_std = np.sqrt(
        2 * PhysicalConstant.e * dark_current * signal_digitizer.bandwidth
    )

    # Step 2: Measure the actual noise standard deviation
    validate_noise(
        noise=dark_current_noise,
        expected_std=expected_current_std,
    )


if __name__ == "__main__":
    pytest.main(["-W error", __file__, "-s"])
