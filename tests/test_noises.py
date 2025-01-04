import pytest
import numpy as np
from FlowCyPy.detector import Detector
from FlowCyPy.units import watt, ohm, kelvin, ampere, second, hertz, degree, AU, volt
from FlowCyPy.physical_constant import PhysicalConstant

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
    detector's responsitivity and resistance.
    """
    # Signal and Detector Properties
    optical_power = 1 * watt  # Power in watts
    sampling_freq = 1e6 * hertz  # Sampling frequency
    run_time = 500e-6 * second  # Signal duration

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * ampere / watt,  # Responsitivity (current per power)
        resistance=50 * ohm,              # Load resistance
        numerical_aperture=0.2 * AU,
        temperature=300 * kelvin,
        dark_current=1e-12 * ampere,
        sampling_freq=sampling_freq,
        phi_angle=0 * degree,
    )
    detector.init_raw_signal(run_time=run_time)

    noise = detector._add_optical_power_to_raw_signal(optical_power)  # Capture returned noise

    # Step 1: Compute Equivalent Shot Noise in Voltage
    photo_current = optical_power * detector.responsitivity

    expected_std = np.sqrt(2 * PhysicalConstant.e * detector.bandwidth * photo_current) * detector.resistance # Shot noise current std

    expected_voltage_std = expected_std.to(volt)

    # Step 2: Measure the actual noise standard deviation
    validate_noise(noise=noise, expected_std=expected_voltage_std, tolerance=0.1)



# Test Thermal Noise
def test_thermal_noise():
    """
    Test that thermal noise added to the signal matches the theoretical standard deviation.

    Thermal noise (Johnson-Nyquist noise) arises due to the thermal agitation of electrons
    in a resistor. The theoretical standard deviation is computed using the Nyquist formula.
    """
    # Detector Properties
    resistance = 50 * ohm  # Load resistance in ohms
    temperature = 300 * kelvin  # Temperature in Kelvin
    sampling_freq = 1e6 * hertz  # Sampling frequency
    run_time = 500e-6 * second  # Signal duration

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * ampere / watt,  # Responsitivity (not used here but required)
        resistance=resistance,            # Load resistance
        numerical_aperture=0.2 * AU,
        temperature=temperature,
        dark_current=0 * ampere,
        sampling_freq=sampling_freq,
        phi_angle=0 * degree,
    )
    detector.init_raw_signal(run_time=run_time)

    # Generate thermal noise
    noise = detector._add_thermal_noise_to_raw_signal()  # Capture returned noise

    # Step 1: Compute Theoretical Thermal Noise in Voltage
    bandwidth = detector.bandwidth  # Bandwidth in Hz
    k_B = PhysicalConstant.kb  # Boltzmann constant in J/K

    # Thermal noise voltage std (Nyquist formula)
    expected_std = np.sqrt(4 * k_B * temperature * resistance * bandwidth).to(volt)

    # Step 2: Measure the actual noise standard deviation
    validate_noise(noise=noise, expected_std=expected_std, tolerance=0.1)


# Test Dark Current Noise
def test_dark_current_noise():
    """
    Test that dark current noise added to the signal matches the theoretical standard deviation.

    Dark current noise arises due to the statistical fluctuations of thermally generated electrons
    in the detector when no light is incident. The noise behaves like shot noise and is proportional
    to the square root of the dark current.
    """
    # Detector Properties
    dark_current = 1e-12 * ampere  # Dark current in amps
    resistance = 50 * ohm  # Load resistance
    sampling_freq = 1e6 * hertz  # Sampling frequency
    run_time = 500e-6 * second  # Signal duration

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * ampere / watt,  # Responsitivity (not used here but required)
        resistance=resistance,            # Load resistance
        numerical_aperture=0.2 * AU,
        temperature=0 * kelvin,
        dark_current=dark_current,
        sampling_freq=sampling_freq,
        phi_angle=0 * degree,
    )
    detector.init_raw_signal(run_time=run_time)

    # Generate dark current noise
    noise = detector._add_dark_current_noise_to_raw_signal()  # Capture returned noise

    # Step 1: Compute Theoretical Dark Current Noise in Voltage
    bandwidth = detector.bandwidth  # Bandwidth in Hz
    e = PhysicalConstant.e  # Elementary charge in C

    # Dark current noise current std
    current_std = np.sqrt(2 * e * dark_current * bandwidth)

    # Convert to voltage using the detector resistance
    expected_std = (current_std * resistance).to(volt)

    # Step 2: Measure the actual noise standard deviation
    validate_noise(noise=noise, expected_std=expected_std, tolerance=0.1)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
