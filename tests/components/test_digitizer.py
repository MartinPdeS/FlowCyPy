import numpy as np
import pytest

from PyMieSim.units import ureg
from FlowCyPy.opto_electronics import Digitizer


def test_constructor_with_quantity_inputs():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=12,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
        use_auto_range=False,
        output_signed_codes=False,
        channel_range_mode="disabled",
    )

    assert digitizer.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)
    assert digitizer.sampling_rate.to("megahertz").magnitude == pytest.approx(100.0)
    assert digitizer.bit_depth == 12
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-1.0)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(1.0)
    assert digitizer.use_auto_range is False
    assert digitizer.output_signed_codes is False
    assert digitizer.channel_range_mode == "disabled"


def test_constructor_with_compact_units():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=10,
        min_voltage=-500 * ureg.millivolt,
        max_voltage=500 * ureg.millivolt,
        channel_range_mode="disabled",
    )

    assert digitizer.bandwidth.to("megahertz").magnitude == pytest.approx(20.0)
    assert digitizer.sampling_rate.to("megahertz").magnitude == pytest.approx(100.0)
    assert digitizer.min_voltage.to("volt").magnitude == pytest.approx(-0.5)
    assert digitizer.max_voltage.to("volt").magnitude == pytest.approx(0.5)


def test_constructor_accepts_channel_range_modes():
    digitizer_disabled = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        channel_range_mode="disabled",
    )
    digitizer_global = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        channel_range_mode="global",
    )
    digitizer_per_channel = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        channel_range_mode="per_channel",
    )

    assert digitizer_disabled.channel_range_mode == "disabled"
    assert digitizer_global.channel_range_mode == "global"
    assert digitizer_per_channel.channel_range_mode == "per_channel"


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

    signal = np.array([0.0, -1.5, np.nan, 3.0, 0.0]) * ureg.volt
    minimum_value, maximum_value = digitizer.get_min_max(signal)

    assert minimum_value.to("volt").magnitude == pytest.approx(-1.5)
    assert maximum_value.to("volt").magnitude == pytest.approx(3.0)


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


def test_digitize_signal_quantizes_to_integer_levels():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bandwidth=20 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([0.0, 0.2, 0.49, 0.51, 0.8, 1.0]) * ureg.volt
    signal = digitizer.digitize_signal(signal)

    expected = np.array([0, 1, 1, 2, 2, 3], dtype=np.uint64)

    assert np.array_equal(signal, expected)
    assert signal.dtype == np.uint64


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

    expected = np.array([0, 0, 128, 255, 255], dtype=np.uint64)

    assert np.array_equal(signal, expected)


def test_digitize_signal_returns_signed_codes_when_requested():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        min_voltage=-1.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
        output_signed_codes=True,
    )

    signal = np.array([-1.0, -0.25, 0.25, 1.0]) * ureg.volt
    signal = digitizer.digitize_signal(signal)

    expected = np.array([-2, -1, 0, 1], dtype=np.int64)

    assert np.array_equal(signal, expected)
    assert signal.dtype == np.int64


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
    signal = digitizer.process_signal(signal)

    assert np.allclose(signal.to("volt").magnitude, [-0.5, -0.25, 0.25, 0.5])


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
    signal = digitizer.process_signal(signal)

    expected = np.array([0, 1, 2, 3], dtype=np.uint64)

    assert np.array_equal(signal, expected)
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


def test_process_signal_preserves_nan_when_digitization_is_disabled():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=0,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([0.0, np.nan, 0.6, 1.2]) * ureg.volt
    processed_signal = digitizer.process_signal(signal)

    assert processed_signal[0].to("volt").magnitude == pytest.approx(0.0)
    assert np.isnan(processed_signal[1].to("volt").magnitude)
    assert processed_signal[2].to("volt").magnitude == pytest.approx(0.6)
    assert processed_signal[3].to("volt").magnitude == pytest.approx(1.0)


def test_process_signal_raises_on_nan_when_digitization_is_enabled():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
    )

    signal = np.array([0.0, np.nan, 0.6, 1.0]) * ureg.volt

    with pytest.raises(RuntimeError):
        digitizer.process_signal(signal)


def test_get_time_series():
    digitizer = Digitizer(
        sampling_rate=4 * ureg.hertz,
        bit_depth=8,
    )

    time_series = digitizer.get_time_series(1 * ureg.second)

    assert time_series.to("second").magnitude == pytest.approx([0.0, 0.25, 0.5, 0.75])


def test_set_channel_voltage_range_accepts_volt_quantities():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=12,
    )

    digitizer.set_channel_voltage_range(
        "forward",
        -0.2 * ureg.volt,
        1.5 * ureg.volt,
    )

    assert digitizer.has_channel_voltage_range("forward") is True

    minimum_voltage, maximum_voltage = digitizer.get_channel_voltage_range("forward")

    assert minimum_voltage.to("volt").magnitude == pytest.approx(-0.2)
    assert maximum_voltage.to("volt").magnitude == pytest.approx(1.5)


def test_clear_channel_voltage_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=12,
    )

    digitizer.set_channel_voltage_range(
        "forward",
        -0.2 * ureg.volt,
        1.5 * ureg.volt,
    )
    assert digitizer.has_channel_voltage_range("forward") is True

    digitizer.clear_channel_voltage_range("forward")

    assert digitizer.has_channel_voltage_range("forward") is False


def test_clear_all_channel_voltage_ranges():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=12,
    )

    digitizer.set_channel_voltage_range("forward", -0.2 * ureg.volt, 1.5 * ureg.volt)
    digitizer.set_channel_voltage_range("side", -0.1 * ureg.volt, 0.8 * ureg.volt)

    digitizer.clear_all_channel_voltage_ranges()

    assert digitizer.has_channel_voltage_range("forward") is False
    assert digitizer.has_channel_voltage_range("side") is False


def test_digitize_data_dict_uses_shared_instance_voltage_range_when_disabled():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
        channel_range_mode="disabled",
    )

    data_dict = {
        "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
        "forward": np.array([0.0, 0.5, 1.0]) * ureg.volt,
        "side": np.array([0.0, 0.5, 1.0]) * ureg.volt,
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.array_equal(
        processed_data_dict["forward"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.array_equal(
        processed_data_dict["side"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.allclose(
        processed_data_dict["Time"].to("second").magnitude,
        [0.0, 1.0, 2.0],
    )


def test_digitize_data_dict_uses_global_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        channel_range_mode="global",
    )

    data_dict = {
        "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
        "forward": np.array([0.0, 1.0, 2.0]) * ureg.volt,
        "side": np.array([0.5, 1.0, 1.5]) * ureg.volt,
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.array_equal(
        processed_data_dict["forward"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.array_equal(
        processed_data_dict["side"], np.array([1, 2, 2], dtype=np.uint64)
    )


def test_digitize_data_dict_uses_per_channel_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        channel_range_mode="per_channel",
    )

    data_dict = {
        "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
        "forward": np.array([0.0, 1.0, 2.0]) * ureg.volt,
        "side": np.array([10.0, 20.0, 30.0]) * ureg.volt,
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.array_equal(
        processed_data_dict["forward"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.array_equal(
        processed_data_dict["side"], np.array([0, 2, 3], dtype=np.uint64)
    )


def test_digitize_data_dict_channel_override_takes_precedence_over_global_mode():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        channel_range_mode="global",
    )

    digitizer.set_channel_voltage_range(
        "side",
        0.0 * ureg.volt,
        1.0 * ureg.volt,
    )

    data_dict = {
        "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
        "forward": np.array([0.0, 1.0, 2.0]) * ureg.volt,
        "side": np.array([0.0, 0.5, 1.0]) * ureg.volt,
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.array_equal(
        processed_data_dict["forward"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.array_equal(
        processed_data_dict["side"], np.array([0, 2, 3], dtype=np.uint64)
    )


def test_digitize_data_dict_returns_voltage_quantities_when_digitization_is_disabled():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=0,
        channel_range_mode="per_channel",
    )

    data_dict = {
        "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
        "forward": np.array([0.0, 1.0, 2.0]) * ureg.volt,
        "side": np.array([10.0, 20.0, 30.0]) * ureg.volt,
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.allclose(
        processed_data_dict["forward"].to("volt").magnitude, [0.0, 1.0, 2.0]
    )
    assert np.allclose(
        processed_data_dict["side"].to("volt").magnitude, [10.0, 20.0, 30.0]
    )


def test_digitize_data_dict_supports_nested_trigger_dictionary():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
        bit_depth=2,
        min_voltage=0.0 * ureg.volt,
        max_voltage=1.0 * ureg.volt,
        channel_range_mode="disabled",
    )

    data_dict = {
        0: {
            "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
            "forward": np.array([0.0, 0.5, 1.0]) * ureg.volt,
        },
        1: {
            "Time": np.array([0.0, 1.0, 2.0]) * ureg.second,
            "forward": np.array([0.25, 0.75, 1.0]) * ureg.volt,
        },
    }

    processed_data_dict = digitizer.digitize_data_dict(data_dict)

    assert np.array_equal(
        processed_data_dict[0]["forward"], np.array([0, 2, 3], dtype=np.uint64)
    )
    assert np.array_equal(
        processed_data_dict[1]["forward"], np.array([1, 2, 3], dtype=np.uint64)
    )


def test_rejects_invalid_channel_range_mode():
    with pytest.raises(Exception):
        Digitizer(
            sampling_rate=100 * ureg.megahertz,
            channel_range_mode="not_a_mode",
        )


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


def test_rejects_unitless_channel_voltage_range():
    digitizer = Digitizer(
        sampling_rate=100 * ureg.megahertz,
    )

    with pytest.raises(Exception):
        digitizer.set_channel_voltage_range("forward", -0.2, 1.5)


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
