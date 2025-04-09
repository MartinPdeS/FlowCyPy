import pytest
import numpy as np
from FlowCyPy.detector import Detector
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.signal_digitizer import SignalDigitizer
from FlowCyPy import units

TOLERANCE = 0.05  # Allowable error margin (5%)

# Helper function to validate noise
def validate_noise(noise, expected_std, tolerance=TOLERANCE):
    measured_std = np.std(noise)
    assert np.isclose(measured_std, expected_std, rtol=tolerance), \
        f"Measured noise std {measured_std} does not match expected {expected_std}."

# Test Shot Noise
def test_shot_noise():
    """
    Test that shot noise added to the signal matches the theoretical standard deviation.

    Shot noise is computed as the square root of the signal power in the context of the
    detector's responsivity and resistance.
    """
    # Signal and Detector Properties
    optical_power = 0.001 * units.milliwatt  # Power in watts
    sampling_rate = 1e6 * units.hertz  # Sampling frequency

    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=sampling_rate
    )

    # Initialize Detector
    detector = Detector(
        responsivity=1 * units.ampere / units.watt,  # Responsitivity (current per power)
        numerical_aperture=0.2 * units.AU,
        dark_current=1e-12 * units.ampere,
        phi_angle=0 * units.degree,
    )

    optical_power_array = optical_power * np.ones(100)
    shot_noise_current = detector.get_shot_noise(
        optical_power=optical_power_array,
        wavelength=1550 * units.nanometer,
        bandwidth=signal_digitizer.bandwidth
    )

    # Step 1: Compute Equivalent Shot Noise in Voltage
    photo_current_array = (optical_power_array  * detector.responsivity) + shot_noise_current

    expected_std = np.sqrt(2 * PhysicalConstant.e * signal_digitizer.bandwidth * optical_power * detector.responsivity) # Shot noise current std

    # Step 2: Measure the actual noise standard deviation
    validate_noise(
        noise=photo_current_array.to(units.ampere),
        expected_std=expected_std.to(units.ampere),
        tolerance=0.1
    )



# Test Dark Current Noise
def test_dark_current_noise():
    """
    Test that dark current noise added to the signal matches the theoretical standard deviation.

    Dark current noise arises due to the statistical fluctuations of thermally generated electrons
    in the detector when no light is incident. The noise behaves like shot noise and is proportional
    to the square root of the dark current.
    """
    # Detector Properties
    dark_current = 1e-12 * units.ampere  # Dark current in amps
    sampling_rate = 1e6 * units.hertz  # Sampling frequency

    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=sampling_rate,
    )

    # Initialize Detector
    detector = Detector(
        responsivity=1 * units.ampere / units.watt,  # Responsitivity (not used here but required)
        numerical_aperture=0.2 * units.AU,
        dark_current=dark_current,
        phi_angle=0 * units.degree,
    )

    # Generate dark current noise
    dark_current_noise = detector.get_dark_current_noise(
        sequence_length=500,
        bandwidth=signal_digitizer.bandwidth
    )  # Capture returned noise

    # Step 1: Compute Theoretical Dark Current Noise in Voltage
    expected_current_std = np.sqrt(2 * PhysicalConstant.e * dark_current * signal_digitizer.bandwidth)

    # Step 2: Measure the actual noise standard deviation
    validate_noise(
        noise=dark_current_noise.to(units.ampere),
        expected_std=expected_current_std.to(units.ampere),
        tolerance=0.1
    )


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
