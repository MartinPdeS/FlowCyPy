import math

import numpy as np
import pytest

from PyMieSim.units import ureg
from FlowCyPy.signal_processing import Digitizer


def test_constructor_with_quantity_inputs():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=12,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
        use_auto_range=False,
    )

    assert digitizer.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)
    assert digitizer.sampling_rate.to("megahertz").magnitude == pytest.approx(100.0)
    assert digitizer.bit_depth == 12
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-1.0)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(1.0)
    assert digitizer.use_auto_range is False


def test_constructor_clamps_bandwidth_to_nyquist():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=50 * ureg.megahertz,
        bit_depth=12,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    assert digitizer.bandwidth.to("megahertz").magnitude == pytest.approx(50.0)
    assert digitizer.sampling_rate.to("megahertz").magnitude == pytest.approx(100.0)


def test_constructor_with_compact_units():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=10,
        min_voltage=-500 * ureg.millivolt,
        max_voltage=500 * ureg.millivolt,
    )

    assert digitizer.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)
    assert digitizer.sampling_rate.to("megahertz").magnitude == pytest.approx(100.0)
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-0.5)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(0.5)


def test_none_voltage_range_disables_clipping():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
        min_voltage=None,
        max_voltage=None,
    )

    assert digitizer.has_voltage_range() is False
    assert digitizer.min_voltage is None
    assert digitizer.max_voltage is None


def test_clear_voltage_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    digitizer.clear_voltage_range()

    assert digitizer.has_voltage_range() is False
    assert digitizer.min_voltage is None
    assert digitizer.max_voltage is None


def test_should_digitize():
    digitizer_disabled = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
    )
    digitizer_enabled = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=12,
    )

    assert digitizer_disabled.should_digitize() is False
    assert digitizer_enabled.should_digitize() is True


def test_get_min_max_ignores_nan():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
    )

    signal = np.array([0.0, -1.5, 0.2, 3.0, 0.0]) * ureg.volt
    min_value, max_value = digitizer.get_min_max(signal)

    assert min_value.to("volt").magnitude == pytest.approx(-1.5)
    assert max_value.to("volt").magnitude == pytest.approx(3.0)


def test_set_auto_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
    )

    digitizer.set_auto_range(np.array([-2.0, -0.5, 1.25]) * ureg.volt)

    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-2.0)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(1.25)
    assert digitizer.has_voltage_range() is True


def test_clip_signal_operates_in_place():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
        min_voltage=-0.5 * ureg.volt,
        max_voltage=0.5 * ureg.volt,
    )

    signal = np.array([-1.0, -0.25, 0.25, 1.0]) * ureg.volt
    signal = digitizer.clip_signal(signal)

    assert np.allclose(signal.to("volt").magnitude, [-0.5, -0.25, 0.25, 0.5])


def test_clip_signal_without_voltage_range_leaves_signal_unchanged():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
        min_voltage=None,
        max_voltage=None,
    )

    signal = np.array([-1.0, 0.0, 1.0]) * ureg.volt
    signal = digitizer.clip_signal(signal)

    assert np.allclose(signal.to("volt").magnitude, [-1.0, 0.0, 1.0])


def test_digitize_signal_disabled_when_bit_depth_is_zero():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([-1.0, -0.1, 0.2, 1.0]) * ureg.volt
    signal = digitizer.digitize_signal(signal)

    assert np.allclose(signal, [-1.0, -0.1, 0.2, 1.0])


def test_digitize_signal_requires_voltage_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=None,
        max_voltage=None,
    )

    signal = np.array([0.1, 0.2, 0.3]) * ureg.volt

    with pytest.raises(RuntimeError):
        digitizer.digitize_signal(signal)


def test_digitize_signal_quantizes_to_integer_levels_in_place():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([0.0, 0.2, 0.49, 0.51, 0.8, 1.0]) * ureg.volt
    signal = digitizer.digitize_signal(signal)

    expected = np.array([0.0, 1.0, 1.0, 2.0, 2.0, 3.0])

    assert np.allclose(signal, expected)


def test_digitize_signal_clips_before_quantization():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([-1.0, 0.0, 0.5, 1.0, 2.0]) * ureg.volt
    signal = digitizer.digitize_signal(signal)

    expected = np.array([0.0, 0.0, 128.0, 255.0, 255.0])

    assert np.allclose(signal, expected)


def test_process_signal_only_clips_when_bit_depth_is_zero():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=0,
        min_voltage=-0.5 * ureg.volt,
        max_voltage=0.5 * ureg.volt,
        use_auto_range=False,
    )

    signal = np.array([-1.0, -0.25, 0.25, 1.0]) * ureg.volt
    digitizer.capture_signal(signal)
    signal = digitizer.process_signal(signal)

    assert np.allclose(signal.to("volt").magnitude, [-0.5, -0.25, 0.25, 0.5])


def test_process_signal_with_explicit_auto_range_override():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=2,
        min_voltage=None,
        max_voltage=None,
        use_auto_range=True,
    )

    signal = np.array([0.0, 0.25, 0.75, 1.0]) * ureg.volt
    digitizer.capture_signal(signal)
    signal = digitizer.process_signal(signal)

    expected = np.array([0.0, 1.0, 2.0, 3.0])

    assert np.allclose(signal, expected)
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(0.0)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(1.0)


def test_process_signal_uses_persistent_auto_range_setting():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=2,
        min_voltage=None,
        max_voltage=None,
        use_auto_range=True,
    )

    signal = np.array([0.0, 0.25, 0.75, 1.0]) * ureg.volt
    digitizer.capture_signal(signal)
    signal = digitizer.process_signal(signal)

    expected = np.array([0.0, 1.0, 2.0, 3.0])

    assert np.allclose(signal, expected)
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(0.0)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(1.0)


def test_capture_signal_updates_range_with_explicit_override():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=None,
        max_voltage=None,
        use_auto_range=False,
    )

    signal = np.array([-0.2, 0.1, 0.8]) * ureg.volt
    result = digitizer.capture_signal(signal, use_auto_range=True)

    assert result is None
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-0.2)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(0.8)


def test_capture_signal_uses_persistent_auto_range_setting():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=None,
        max_voltage=None,
        use_auto_range=True,
    )

    signal = np.array([-0.2, 0.1, 0.8]) * ureg.volt
    result = digitizer.capture_signal(signal)

    assert result is None
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-0.2)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(0.8)


def test_nan_values_are_preserved_during_processing():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([0.0, 0.0, 0.6, 1.0]) * ureg.volt
    signal = digitizer.process_signal(signal)

    assert signal[0] == pytest.approx(0.0)
    assert signal[2] == pytest.approx(2.0)
    assert signal[3] == pytest.approx(3.0)


def test_get_time_series():
    digitizer = Digitizer(
        sampling_rate=4 * ureg.hertz,
        bit_depth=8,
    )

    time_series = digitizer.get_time_series(1 * ureg.second)

    assert time_series.to("second").magnitude == pytest.approx([0.0, 0.25, 0.5, 0.75])


def test_rejects_unitless_sampling_rate():
    with pytest.raises(Exception):
        Digitizer(
            sampling_rate=100e6,
            bandwidth=20 * ureg.megahertz,
        )


def test_rejects_unitless_voltage_bounds():
    with pytest.raises(Exception):
        Digitizer(
            sampling_rate=100 * ureg.megahertz,
            bandwidth=20 * ureg.megahertz,
            min_voltage=-1.0,
            max_voltage=1.0,
        )


def test_rejects_unitless_signal():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=8,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    with pytest.raises(Exception):
        digitizer.process_signal(np.array([0.0, 0.5, 1.0]))


if __name__ == "__main__":
    pytest.main(["-s", "-W", "error", __file__])
