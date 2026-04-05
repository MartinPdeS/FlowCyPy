import numpy as np
import pytest

from PyMieSim.units import ureg
from FlowCyPy.opto_electronics import Detector


def test_constructor_with_quantity_inputs():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        cache_numerical_aperture=0.2,
        gamma_angle=15 * ureg.degree,
        sampling=256,
        responsivity=0.85 * ureg.ampere / ureg.watt,
        dark_current=2e-9 * ureg.ampere,
        bandwidth=20 * ureg.megahertz,
        name="side_scatter",
    )

    assert detector.phi_angle.to("degree").magnitude == pytest.approx(90.0)
    assert detector.numerical_aperture == pytest.approx(0.7)
    assert detector.cache_numerical_aperture == pytest.approx(0.2)
    assert detector.gamma_angle.to("degree").magnitude == pytest.approx(15.0)
    assert detector.sampling == 256
    assert detector.responsivity.to("ampere / watt").magnitude == pytest.approx(0.85)
    assert detector.dark_current.to("ampere").magnitude == pytest.approx(2e-9)
    assert detector.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)
    assert detector.name == "side_scatter"


def test_constructor_uses_default_values():
    detector = Detector(
        phi_angle=45 * ureg.degree,
        numerical_aperture=0.5,
    )

    assert detector.phi_angle.to("degree").magnitude == pytest.approx(45.0)
    assert detector.numerical_aperture == pytest.approx(0.5)
    assert detector.cache_numerical_aperture == pytest.approx(0.0)
    assert detector.gamma_angle.to("degree").magnitude == pytest.approx(0.0)
    assert detector.sampling == 200
    assert detector.responsivity.to("ampere / watt").magnitude == pytest.approx(1.0)
    assert detector.dark_current.to("ampere").magnitude == pytest.approx(0.0)
    assert detector.bandwidth is None
    assert isinstance(detector.name, str)
    assert len(detector.name) > 0


def test_constructor_accepts_compact_units():
    detector = Detector(
        phi_angle=np.pi / 2 * ureg.radian,
        numerical_aperture=0.9,
        gamma_angle=250 * ureg.milliradian,
        responsivity=500 * ureg.milliampere / ureg.watt,
        dark_current=3 * ureg.nanoampere,
        bandwidth=0.02 * ureg.gigahertz,
    )

    assert detector.phi_angle.to("degree").magnitude == pytest.approx(90.0)
    assert detector.gamma_angle.to("radian").magnitude == pytest.approx(0.25)
    assert detector.responsivity.to("ampere / watt").magnitude == pytest.approx(0.5)
    assert detector.dark_current.to("ampere").magnitude == pytest.approx(3e-9)
    assert detector.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)


def test_has_bandwidth():
    detector_without_bandwidth = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        bandwidth=None,
    )
    detector_with_bandwidth = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        bandwidth=20 * ureg.megahertz,
    )

    assert detector_without_bandwidth.has_bandwidth() is False
    assert detector_with_bandwidth.has_bandwidth() is True


def test_clear_bandwidth():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        bandwidth=20 * ureg.megahertz,
    )

    detector.clear_bandwidth()

    assert detector.has_bandwidth() is False
    assert detector.bandwidth is None


def test_apply_dark_current_noise_returns_input_when_no_bandwidth_is_available():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=2e-9 * ureg.ampere,
        bandwidth=None,
    )

    signal = np.array([1e-9, 2e-9, 3e-9]) * ureg.ampere
    noisy_signal = detector.apply_dark_current_noise(signal)

    assert np.allclose(
        noisy_signal.to("ampere").magnitude,
        signal.to("ampere").magnitude,
    )


def test_apply_dark_current_noise_uses_stored_bandwidth():
    np.random.seed(0)

    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=2e-9 * ureg.ampere,
        bandwidth=20 * ureg.megahertz,
    )

    signal = np.array([1e-9, 2e-9, 3e-9]) * ureg.ampere
    noisy_signal = detector.apply_dark_current_noise(signal)

    assert hasattr(noisy_signal, "to")
    assert noisy_signal.to("ampere").magnitude.shape == (3,)
    assert not np.allclose(
        noisy_signal.to("ampere").magnitude,
        signal.to("ampere").magnitude,
        atol=0.0,
        rtol=1e-12,
    )


def test_apply_dark_current_noise_method_bandwidth_overrides_instance_bandwidth():
    np.random.seed(0)

    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=2e-9 * ureg.ampere,
        bandwidth=5 * ureg.megahertz,
    )

    signal = np.array([1e-9, 2e-9, 3e-9]) * ureg.ampere

    noisy_signal_with_override = detector.apply_dark_current_noise(
        signal,
        bandwidth=50 * ureg.megahertz,
    )
    noisy_signal_with_instance_bandwidth = detector.apply_dark_current_noise(signal)

    assert noisy_signal_with_override.to("ampere").magnitude.shape == (3,)
    assert noisy_signal_with_instance_bandwidth.to("ampere").magnitude.shape == (3,)
    assert not np.allclose(
        noisy_signal_with_override.to("ampere").magnitude,
        noisy_signal_with_instance_bandwidth.to("ampere").magnitude,
        atol=0.0,
        rtol=1e-12,
    )


def test_apply_dark_current_noise_returns_current_quantity():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=1e-9 * ureg.ampere,
        bandwidth=10 * ureg.megahertz,
    )

    signal = np.array([0.0, 1e-9, 2e-9]) * ureg.ampere
    noisy_signal = detector.apply_dark_current_noise(signal)

    converted_signal = noisy_signal.to("ampere").magnitude
    assert converted_signal.shape == (3,)


def test_apply_dark_current_noise_raises_on_empty_signal():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=1e-9 * ureg.ampere,
        bandwidth=10 * ureg.megahertz,
    )

    signal = np.array([]) * ureg.ampere

    with pytest.raises(ValueError):
        detector.apply_dark_current_noise(signal)


def test_name_is_auto_generated_when_not_provided():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
    )

    assert isinstance(detector.name, str)
    assert len(detector.name) > 0


def test_name_is_preserved_when_provided():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        name="forward_scatter",
    )

    assert detector.name == "forward_scatter"


def test_property_setters_accept_quantities():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
    )

    detector.phi_angle = 30 * ureg.degree
    detector.gamma_angle = 5 * ureg.degree
    detector.responsivity = 0.65 * ureg.ampere / ureg.watt
    detector.dark_current = 4e-9 * ureg.ampere
    detector.bandwidth = 15 * ureg.megahertz

    assert detector.phi_angle.to("degree").magnitude == pytest.approx(30.0)
    assert detector.gamma_angle.to("degree").magnitude == pytest.approx(5.0)
    assert detector.responsivity.to("ampere / watt").magnitude == pytest.approx(0.65)
    assert detector.dark_current.to("ampere").magnitude == pytest.approx(4e-9)
    assert detector.bandwidth.to("megahertz").magnitude == pytest.approx(15.0)


def test_bandwidth_can_be_set_to_none():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        bandwidth=10 * ureg.megahertz,
    )

    detector.bandwidth = None

    assert detector.bandwidth is None
    assert detector.has_bandwidth() is False


def test_rejects_unitless_phi_angle():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90.0,
            numerical_aperture=0.7,
        )


def test_rejects_unitless_gamma_angle():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            gamma_angle=15.0,
        )


def test_rejects_unitless_responsivity():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            responsivity=0.8,
        )


def test_rejects_unitless_dark_current():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            dark_current=2e-9,
        )


def test_rejects_unitless_bandwidth():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            bandwidth=20e6,
        )


def test_rejects_unitless_signal_in_apply_dark_current_noise():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=1e-9 * ureg.ampere,
        bandwidth=10 * ureg.megahertz,
    )

    with pytest.raises(Exception):
        detector.apply_dark_current_noise(np.array([0.0, 1e-9, 2e-9]))


def test_rejects_negative_numerical_aperture():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=-0.1,
        )


def test_rejects_negative_cache_numerical_aperture():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            cache_numerical_aperture=-0.1,
        )


def test_rejects_non_positive_sampling():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            sampling=0,
        )


def test_rejects_negative_responsivity():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            responsivity=-1 * ureg.ampere / ureg.watt,
        )


def test_rejects_negative_dark_current():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            dark_current=-1e-9 * ureg.ampere,
        )


def test_rejects_non_positive_bandwidth():
    with pytest.raises(Exception):
        Detector(
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.7,
            bandwidth=0 * ureg.hertz,
        )


def test_rejects_non_positive_method_bandwidth_in_apply_dark_current_noise():
    detector = Detector(
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.7,
        dark_current=1e-9 * ureg.ampere,
        bandwidth=None,
    )

    signal = np.array([1e-9, 2e-9, 3e-9]) * ureg.ampere

    with pytest.raises(Exception):
        detector.apply_dark_current_noise(signal, bandwidth=0 * ureg.hertz)


if __name__ == "__main__":
    pytest.main(["-s", "-W", "error", __file__])
