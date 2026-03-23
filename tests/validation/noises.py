import numpy as np
import pytest
from TypedUnit import ureg

import FlowCyPy
from FlowCyPy.opto_electronics import Detector
from FlowCyPy.opto_electronics.source import Gaussian
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.signal_processing import Digitizer

FlowCyPy.debug_mode = True

# ----------------- CONSTANTS -----------------

TOLERANCE = 0.05
N_ELEMENTS = 5000


# ----------------- FIXTURES -----------------


@pytest.fixture
def digitizer():
    return Digitizer(
        bit_depth=10,
        use_auto_range=True,
        sampling_rate=1e6 * ureg.hertz,
        bandwidth=1e6 * ureg.hertz,
    )


# ----------------- HELPERS -----------------


def validate_noise(
    noise: np.ndarray, expected_std: float, tolerance: float = TOLERANCE
):
    measured_std = np.std(noise)
    assert np.isclose(
        measured_std, expected_std, rtol=tolerance, atol=1e-10
    ), f"Measured noise std {measured_std} does not match expected {expected_std}."


# ----------------- TESTS -----------------


def test_shot_noise(digitizer):
    """
    Shot noise is applied by the source on an optical power signal.
    """

    # Constant optical power (P)
    optical_power = 0.001 * ureg.milliwatt
    power_watt = optical_power.to("watt").magnitude
    power_signal = np.full(N_ELEMENTS, power_watt, dtype=float)

    # Source with shot noise enabled
    source = Gaussian(
        wavelength=1550 * ureg.nanometer,
        optical_power=optical_power,
        waist_y=1e-6 * ureg.meter,
        waist_z=1e-6 * ureg.meter,
        rin=-120.0,
        polarization=0.0 * ureg.radian,
        bandwidth=digitizer.bandwidth,
        include_shot_noise=True,
        include_rin_noise=False,
        debug_mode=False,
    )

    # Use a time step consistent with the bandwidth convention:
    # Δt = 1 / (2 B)  ⇒  B = 1 / (2 Δt)
    bandwidth_hz = digitizer.bandwidth.to("hertz")
    dt = 1.0 / (2.0 * bandwidth_hz)

    noisy_power = power_signal.copy() * ureg.watt
    time_array = np.arange(N_ELEMENTS) * dt
    # C++ signature: add_shot_noise_to_signal(std::vector<double>& power_values, double time_step)
    noisy_power = source.add_shot_noise_to_signal(noisy_power, time_array)

    # Convert power → current using responsivity
    responsivity = 1 * ureg.ampere / ureg.watt
    current_amp = noisy_power * responsivity.to("ampere/watt")

    # Expected shot noise std: σ = sqrt(2 e I B)
    current_mean = (optical_power * responsivity).to("ampere")
    expected_std = np.sqrt(
        2 * PhysicalConstant.e * current_mean * digitizer.bandwidth
    ).to("ampere")

    validate_noise(current_amp, expected_std)


def test_dark_current_noise(digitizer):
    """
    Dark current noise is applied by the detector on a current signal.
    """

    dark_current = 1e-12 * ureg.ampere
    # Baseline signal (can be zero or dark_current; only noise std matters)
    signal = np.full(N_ELEMENTS, 0.0, dtype=float) * ureg.ampere

    detector = Detector(
        name="TestDetector",
        responsivity=1 * ureg.ampere / ureg.watt,
        numerical_aperture=0.2 * ureg.AU,
        dark_current=dark_current,
        phi_angle=0 * ureg.degree,
    )

    noisy_signal = detector.apply_dark_current_noise(
        signal=signal,
        bandwidth=digitizer.bandwidth,
    )

    # Expected dark current noise std: σ = sqrt(2 q I_d B)
    expected_std = (
        np.sqrt(2 * PhysicalConstant.e * dark_current * digitizer.bandwidth)
        .to("ampere")
        .magnitude
    )

    validate_noise(noisy_signal.to("ampere").magnitude, expected_std)


if __name__ == "__main__":
    pytest.main(["-W error", __file__, "-s"])
