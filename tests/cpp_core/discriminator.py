import numpy as np
import pytest

from FlowCyPy.signal_processing.discriminator import DoubleThreshold, FixedWindow
from FlowCyPy.units import ureg

N_POINTS = 1000


def make_time() -> ureg.Quantity:
    return np.linspace(0, 1, N_POINTS) * ureg.second


def test_fixed_window_run_with_dict_returns_flat_segmented_dictionary():
    time = make_time()

    det1 = np.zeros(N_POINTS)
    det2 = np.zeros(N_POINTS)

    det1[100:120] = 2.0
    det1[400:420] = 2.0
    det1[800:820] = 2.0

    det2[100:120] = 5.0
    det2[400:420] = 6.0
    det2[800:820] = 7.0

    input_dict = {
        "Time": time,
        "det1": det1 * ureg.volt,
        "det2": det2 * ureg.volt,
    }

    discriminator = FixedWindow(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
    )

    output = discriminator.run_with_dict(input_dict)

    assert set(output.keys()) == {"segment_id", "Time", "det1", "det2"}

    assert len(output["segment_id"]) == len(output["Time"])
    assert len(output["segment_id"]) == len(output["det1"])
    assert len(output["segment_id"]) == len(output["det2"])

    assert len(np.unique(output["segment_id"])) == 3
    assert len(output["det1"]) > 0


def test_double_threshold_run_with_dict_detects_expected_segments():
    time = make_time()

    signal = np.zeros(N_POINTS)
    signal[100:120] = 2.0
    signal[400:420] = 2.0
    signal[800:820] = 2.0

    input_dict = {
        "Time": time,
        "det1": signal * ureg.volt,
    }

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        lower_threshold=0.5 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    output = discriminator.run_with_dict(input_dict)

    assert len(np.unique(output["segment_id"])) == 3
    assert len(output["det1"]) > 0


def test_double_threshold_run_with_dict_detects_rising_and_falling_edges():
    time = make_time()

    signal = np.zeros(N_POINTS)
    signal[100:150] = 2.0
    signal[300:380] = 2.0

    input_dict = {
        "Time": time,
        "det1": signal * ureg.volt,
    }

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        lower_threshold=0.5 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=5,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    output = discriminator.run_with_dict(input_dict)

    assert len(np.unique(output["segment_id"])) == 2


def test_double_threshold_simple_triggering_segments_plateaus():
    time = make_time()

    signal = np.zeros(N_POINTS)
    signal[200:250] = 3.0
    signal[700:760] = 3.0

    input_dict = {
        "Time": time,
        "det1": signal * ureg.volt,
    }

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=2.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=3,
        max_triggers=3,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    output = discriminator.run_with_dict(input_dict)

    assert len(np.unique(output["segment_id"])) == 2


def test_run_with_dict_raises_if_time_missing():
    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    input_dict = {
        "det1": np.zeros(N_POINTS) * ureg.volt,
    }

    with pytest.raises(RuntimeError, match="Time"):
        discriminator.run_with_dict(input_dict)


def test_run_with_dict_raises_if_no_signal_channel():
    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    input_dict = {
        "Time": make_time(),
    }

    with pytest.raises(RuntimeError, match="at least one signal channel"):
        discriminator.run_with_dict(input_dict)


def test_run_with_dict_returns_empty_output_if_no_trigger_found():
    time = make_time()
    signal = np.ones(N_POINTS) * 0.1 * ureg.volt

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=5.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    output = discriminator.run_with_dict(
        {
            "Time": time,
            "det1": signal,
        }
    )

    assert set(output.keys()) == {"segment_id", "Time", "det1"}
    assert len(output["segment_id"]) == 0
    assert len(output["Time"]) == 0
    assert len(output["det1"]) == 0


def test_run_with_dict_preserves_alignment_between_all_outputs():
    time = make_time()

    det1 = np.zeros(N_POINTS)
    det2 = np.zeros(N_POINTS)

    det1[300:320] = 4.0
    det2[300:320] = 9.0

    output = FixedWindow(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=4,
        post_buffer=6,
        max_triggers=10,
    ).run_with_dict(
        {
            "Time": time,
            "det1": det1 * ureg.volt,
            "det2": det2 * ureg.volt,
        }
    )

    assert len(output["segment_id"]) == len(output["Time"])
    assert len(output["segment_id"]) == len(output["det1"])
    assert len(output["segment_id"]) == len(output["det2"])


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
