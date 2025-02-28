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
    detector's responsitivity and resistance.
    """
    # Signal and Detector Properties
    optical_power = 0.001 * units.milliwatt  # Power in watts
    sampling_rate = 1e6 * units.hertz  # Sampling frequency
    run_time = 500e-6 * units.second  # Signal duration

    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=sampling_rate
    )

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * units.ampere / units.watt,  # Responsitivity (current per power)
        resistance=50 * units.ohm,              # Load resistance
        numerical_aperture=0.2 * units.AU,
        temperature=300 * units.kelvin,
        dark_current=1e-12 * units.ampere,
        phi_angle=0 * units.degree,
    )
    dataframe = detector.get_initialized_signal(run_time=run_time, signal_digitizer=signal_digitizer)

    noise = detector._add_optical_power_to_raw_signal(
        optical_power=optical_power,
        wavelength=1550 * units.nanometer,
        signal=dataframe['Signal']
    )  # Capture returned noise

    # Step 1: Compute Equivalent Shot Noise in Voltage
    photo_current = optical_power * detector.responsitivity

    expected_std = np.sqrt(2 * PhysicalConstant.e * detector.signal_digitizer.bandwidth * photo_current) * detector.resistance # Shot noise current std

    expected_voltage_std = expected_std.to(units.volt)

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
    resistance = 50 * units.ohm  # Load resistance in ohms
    temperature = 300 * units.kelvin  # Temperature in Kelvin
    sampling_rate = 1e6 * units.hertz  # Sampling frequency
    run_time = 500e-6 * units.second  # Signal duration

    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=sampling_rate,
    )

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * units.ampere / units.watt,  # Responsitivity (not used here but required)
        resistance=resistance,            # Load resistance
        numerical_aperture=0.2 * units.AU,
        temperature=temperature,
        dark_current=0 * units.ampere,
        phi_angle=0 * units.degree,
    )
    dataframe = detector.get_initialized_signal(run_time=run_time, signal_digitizer=signal_digitizer)

    # Generate thermal noise
    noise = detector._add_thermal_noise_to_raw_signal(signal=dataframe['Signal'])  # Capture returned noise

    # Step 1: Compute Theoretical Thermal Noise in Voltage
    bandwidth = detector.signal_digitizer.bandwidth  # Bandwidth in Hz
    k_B = PhysicalConstant.kb  # Boltzmann constant in J/K

    # Thermal noise voltage std (Nyquist formula)
    expected_std = np.sqrt(4 * k_B * temperature * resistance * bandwidth).to(units.volt)

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
    dark_current = 1e-12 * units.ampere  # Dark current in amps
    resistance = 50 * units.ohm  # Load resistance
    sampling_rate = 1e6 * units.hertz  # Sampling frequency
    run_time = 500e-6 * units.second  # Signal duration

    signal_digitizer = SignalDigitizer(
        bit_depth=1024,
        saturation_levels='auto',
        sampling_rate=sampling_rate,
    )

    # Initialize Detector
    detector = Detector(
        responsitivity=1 * units.ampere / units.watt,  # Responsitivity (not used here but required)
        resistance=resistance,            # Load resistance
        numerical_aperture=0.2 * units.AU,
        temperature=0 * units.kelvin,
        dark_current=dark_current,
        phi_angle=0 * units.degree,
    )
    dataframe = detector.get_initialized_signal(run_time=run_time, signal_digitizer=signal_digitizer)

    # Generate dark current noise
    noise = detector._add_dark_current_noise_to_raw_signal(dataframe['Signal'])  # Capture returned noise

    # Step 1: Compute Theoretical Dark Current Noise in Voltage
    bandwidth = detector.signal_digitizer.bandwidth  # Bandwidth in Hz
    e = PhysicalConstant.e  # Elementary charge in C

    # Dark current noise current std
    current_std = np.sqrt(2 * e * dark_current * bandwidth)

    # Convert to voltage using the detector resistance
    expected_std = (current_std * resistance).to(units.volt)

    # Step 2: Measure the actual noise standard deviation
    validate_noise(noise=noise, expected_std=expected_std, tolerance=0.1)


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
