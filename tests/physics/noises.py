import numpy as np
import pytest
from TypedUnit import ureg
from FlowCyPy.opto_electronics import Detector
from FlowCyPy.opto_electronics.source import Gaussian


SAMPLE_COUNT = 5000


def assert_noise_statistics(*, signal, expected_mean, expected_std):
    """Compare sampled mean and standard deviation within five standard errors."""
    assert signal.shape == (SAMPLE_COUNT,)
    assert abs(signal.mean() - expected_mean) <= 5 * expected_std / np.sqrt(
        SAMPLE_COUNT
    )
    # For independent Gaussian samples, the relative standard error of the
    # sample standard deviation is approximately 1 / sqrt(2 * (n - 1)).
    relative_error = abs(signal.std(ddof=1) / expected_std - 1)
    assert relative_error <= 5 / np.sqrt(2 * (SAMPLE_COUNT - 1))


def test_shot_noise():
    """Photon counts per sampling interval determine optical power variance."""
    optical_power = 1 * ureg.microwatt
    wavelength = 1550 * ureg.nanometer
    sample_interval = 0.5 * ureg.microsecond
    source = Gaussian(
        wavelength=wavelength,
        optical_power=optical_power,
        waist_y=1 * ureg.micrometer,
        waist_z=1 * ureg.micrometer,
        include_shot_noise=True,
        include_rin_noise=False,
    )
    signal = source.add_shot_noise_to_signal(
        np.ones(SAMPLE_COUNT) * optical_power,
        np.arange(SAMPLE_COUNT) * sample_interval,
        seed=42,
    )

    photon_energy = ureg.planck_constant * ureg.speed_of_light / wavelength
    expected_std = np.sqrt(optical_power * photon_energy / sample_interval).to("watt")
    assert_noise_statistics(
        signal=signal, expected_mean=optical_power, expected_std=expected_std
    )


def test_low_light_shot_noise_resolves_individual_photons():
    """A quarter photon per sample gives discrete counts and Poisson zero occupancy."""
    wavelength = 532 * ureg.nanometer
    sample_interval = 2 * ureg.microsecond
    single_photon_power = (
        ureg.planck_constant * ureg.speed_of_light / wavelength / sample_interval
    ).to("watt")
    expected_count = 0.25
    optical_power = expected_count * single_photon_power
    source = Gaussian(
        wavelength=wavelength,
        optical_power=optical_power,
        waist_y=1 * ureg.micrometer,
        waist_z=1 * ureg.micrometer,
        include_shot_noise=True,
        include_rin_noise=False,
    )
    powers = source.add_shot_noise_to_signal(
        np.ones(SAMPLE_COUNT) * optical_power,
        np.arange(SAMPLE_COUNT) * sample_interval,
        seed=42,
    )
    counts = (powers / single_photon_power).m_as("dimensionless")
    assert np.all(counts >= 0)
    observed_quantum = counts[counts > 0].min()
    # The native model rounds c to 3e8 m/s, within 0.1% of the SI value.
    assert abs(observed_quantum - 1) < 0.001
    observed_counts = counts / observed_quantum
    np.testing.assert_allclose(observed_counts, np.rint(observed_counts), rtol=1e-14, atol=0)
    zero_probability = np.exp(-expected_count)
    standard_error = np.sqrt(zero_probability * (1 - zero_probability) / SAMPLE_COUNT)
    assert abs(np.mean(counts == 0) - zero_probability) <= 5 * standard_error


def test_dark_current_noise():
    """Check the DC offset and the shot-noise variance 2 q I B in amperes."""
    dark_current = 1 * ureg.picoampere
    bandwidth = 1 * ureg.megahertz
    detector = Detector(
        name="TestDetector",
        responsivity=1 * ureg.ampere / ureg.watt,
        numerical_aperture=0.2 * ureg.AU,
        dark_current=dark_current,
        phi_angle=0 * ureg.degree,
    )
    signal = detector.apply_dark_current_noise(
        signal=np.zeros(SAMPLE_COUNT) * ureg.ampere,
        bandwidth=bandwidth,
        seed=42,
    )

    expected_std = np.sqrt(2 * ureg.elementary_charge * dark_current * bandwidth).to(
        "ampere"
    )
    assert_noise_statistics(
        signal=signal, expected_mean=dark_current, expected_std=expected_std
    )


if __name__ == "__main__":
    pytest.main(["-W", "error", __file__, "-s"])
