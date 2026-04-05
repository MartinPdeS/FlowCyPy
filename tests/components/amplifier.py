import math
import numpy as np
import pytest
from FlowCyPy.opto_electronics.amplifier import Amplifier
from pint import UnitRegistry


ureg = UnitRegistry()


def test_constructor_with_all_quantity_inputs():
    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        bandwidth=20e6 * ureg.hertz,
        voltage_noise_density=4e-9 * ureg.volt / ureg.hertz**0.5,
        current_noise_density=2e-15 * ureg.ampere / ureg.hertz**0.5,
    )

    assert amplifier.gain.to("ohm").magnitude == pytest.approx(1e6)
    assert amplifier.bandwidth.to("hertz").magnitude == pytest.approx(20e6)
    assert amplifier.voltage_noise_density.to(
        "volt / hertz ** 0.5"
    ).magnitude == pytest.approx(4e-9)
    assert amplifier.current_noise_density.to(
        "ampere / hertz ** 0.5"
    ).magnitude == pytest.approx(2e-15)


def test_constructor_with_none_defaults():
    amplifier = Amplifier(
        gain=5e5 * ureg.ohm,
        bandwidth=None,
        voltage_noise_density=None,
        current_noise_density=None,
    )

    assert amplifier.gain.to("ohm").magnitude == pytest.approx(5e5)
    assert amplifier.bandwidth is None
    assert amplifier.voltage_noise_density.to(
        "volt / hertz ** 0.5"
    ).magnitude == pytest.approx(0.0)
    assert amplifier.current_noise_density.to(
        "ampere / hertz ** 0.5"
    ).magnitude == pytest.approx(0.0)


def test_constructor_with_only_required_argument():
    amplifier = Amplifier(gain=2e6 * ureg.ohm)

    assert amplifier.gain.to("ohm").magnitude == pytest.approx(2e6)
    assert amplifier.bandwidth is None
    assert amplifier.voltage_noise_density.to(
        "volt / hertz ** 0.5"
    ).magnitude == pytest.approx(0.0)
    assert amplifier.current_noise_density.to(
        "ampere / hertz ** 0.5"
    ).magnitude == pytest.approx(0.0)


def test_gain_is_returned_as_quantity():
    amplifier = Amplifier(gain=3e6 * ureg.ohm)

    assert hasattr(amplifier.gain, "to")
    assert amplifier.gain.to("ohm").magnitude == pytest.approx(3e6)


def test_bandwidth_is_returned_as_none_when_unlimited():
    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        bandwidth=None,
    )

    assert amplifier.bandwidth is None


def test_bandwidth_is_returned_as_quantity_when_defined():
    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        bandwidth=50e6 * ureg.hertz,
    )

    assert hasattr(amplifier.bandwidth, "to")
    assert amplifier.bandwidth.to("hertz").magnitude == pytest.approx(50e6)


def test_noise_densities_are_returned_as_quantities():
    voltage_noise_density = 3e-9 * ureg.volt / ureg.hertz**0.5
    current_noise_density = 7e-15 * ureg.ampere / ureg.hertz**0.5
    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        voltage_noise_density=voltage_noise_density,
        current_noise_density=current_noise_density,
    )

    assert hasattr(amplifier.voltage_noise_density, "to")
    assert hasattr(amplifier.current_noise_density, "to")

    assert amplifier.voltage_noise_density.to(
        "volt / hertz ** 0.5"
    ).magnitude == pytest.approx(3e-9)
    assert amplifier.current_noise_density.to(
        "ampere / hertz ** 0.5"
    ).magnitude == pytest.approx(7e-15)


def test_get_rms_noise_returns_voltage_quantity():

    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        bandwidth=10e6 * ureg.hertz,
        voltage_noise_density=2e-9 * ureg.volt / ureg.hertz**0.5,
        current_noise_density=0.0 * ureg.ampere / ureg.hertz**0.5,
    )

    rms_noise = amplifier.get_rms_noise()

    assert hasattr(rms_noise, "to")
    assert rms_noise.to("volt").magnitude >= 0.0


def test_get_rms_noise_matches_cpp_formula_for_voltage_noise_only():
    amplifier = Amplifier(
        gain=1e6 * ureg.ohm,
        bandwidth=10e6 * ureg.hertz,
        voltage_noise_density=2e-9 * ureg.volt / ureg.hertz**0.5,
        current_noise_density=0.0 * ureg.ampere / ureg.hertz**0.5,
    )

    rms_noise = amplifier.get_rms_noise().to("volt").magnitude

    expected_rms_noise = amplifier.voltage_noise_density.to(
        "volt / hertz ** 0.5"
    ).magnitude * np.sqrt(amplifier.bandwidth.to("hertz").magnitude)

    assert rms_noise == pytest.approx(expected_rms_noise, rel=1e-12, abs=0.0)


def test_reject_non_positive_gain():
    with pytest.raises(RuntimeError, match="gain must be strictly positive"):
        Amplifier(gain=0.0 * ureg.ohm)

    with pytest.raises(RuntimeError, match="gain must be strictly positive"):
        Amplifier(gain=-1.0 * ureg.ohm)


def test_reject_non_positive_bandwidth():
    with pytest.raises(RuntimeError, match="bandwidth must be strictly positive"):
        Amplifier(
            gain=1e6 * ureg.ohm,
            bandwidth=0.0 * ureg.hertz,
        )

    with pytest.raises(RuntimeError, match="bandwidth must be strictly positive"):
        Amplifier(
            gain=1e6 * ureg.ohm,
            bandwidth=-1.0 * ureg.hertz,
        )


def test_reject_negative_voltage_noise_density():
    with pytest.raises(
        RuntimeError, match="voltage_noise_density must be non negative"
    ):
        Amplifier(
            gain=1e6 * ureg.ohm,
            voltage_noise_density=-1e-9 * ureg.volt / ureg.hertz**0.5,
        )


def test_reject_negative_current_noise_density():
    with pytest.raises(
        RuntimeError, match="current_noise_density must be non negative"
    ):
        Amplifier(
            gain=1e6 * ureg.ohm,
            current_noise_density=-1e-15 * ureg.ampere / ureg.hertz**0.5,
        )


def test_reject_gain_with_wrong_units():
    with pytest.raises(Exception):
        Amplifier(gain=10.0 * ureg.volt)


def test_reject_bandwidth_with_wrong_units():
    with pytest.raises(Exception):
        Amplifier(
            gain=1e6 * ureg.ohm,
            bandwidth=10.0 * ureg.volt,
        )


def test_reject_voltage_noise_density_with_wrong_units():
    with pytest.raises(Exception):
        Amplifier(
            gain=1e6 * ureg.ohm,
            voltage_noise_density=1.0 * ureg.hertz,
        )


def test_reject_current_noise_density_with_wrong_units():
    with pytest.raises(Exception):
        Amplifier(
            gain=1e6 * ureg.ohm,
            current_noise_density=1.0 * ureg.hertz,
        )


if __name__ == "__main__":
    pytest.main(["-s", "-W", "error", __file__])
