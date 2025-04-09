import numpy as np
import pytest

from FlowCyPy.binary.interface_triggering_system import TriggeringSystem

N_POINTS = 1000

def test_add_time_and_signal_accept_valid_inputs():
    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=5, post_buffer=5, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    time = np.linspace(0, 1, N_POINTS)
    signal = np.zeros_like(time)
    ts.add_time(time)
    ts.add_signal("det1", signal)


def test_add_time_rejects_bad_shape():
    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=5, post_buffer=5, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    with pytest.raises(RuntimeError, match="1D"):
        ts.add_time(np.zeros((10, 10)))


def test_add_signal_rejects_bad_shape():
    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=5, post_buffer=5, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    with pytest.raises(RuntimeError, match="1D"):
        ts.add_signal("det1", np.zeros((5, 5)))


# === Triggering algorithm tests ===

def test_fixed_window_triggering_extracts_expected_segments():
    time = np.linspace(0, 1, N_POINTS)
    signal = np.zeros_like(time)
    signal[100:120] = 2.0
    signal[400:420] = 2.0
    signal[800:820] = 2.0


    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=5, post_buffer=5, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_time(time)
    ts.add_signal("det1", signal)
    ts.run(algorithm="fixed-window")



    signals = ts.get_signals("det1")

    ids = ts.get_segments_ID("det1")
    assert len(np.unique(ids)) == 3
    assert len(signals) > 0


def test_dynamic_triggering_detects_rising_and_falling_edges():
    time = np.linspace(0, 1, N_POINTS)
    signal = np.zeros_like(time)
    signal[100:150] = 2.0
    signal[300:380] = 2.0

    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=0.5,
        pre_buffer=5, post_buffer=5, max_triggers=5,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_time(time)
    ts.add_signal("det1", signal)
    ts.run(algorithm="dynamic")

    seg_ids = ts.get_segments_ID("det1")
    assert len(np.unique(seg_ids)) == 2


def test_dynamic_simple_triggering_segments_plateaus():
    time = np.linspace(0, 1, N_POINTS)
    signal = np.zeros_like(time)
    signal[200:250] = 3.0
    signal[700:760] = 3.0

    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=2.0, lower_threshold=np.nan,
        pre_buffer=2, post_buffer=3, max_triggers=3,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_time(time)
    ts.add_signal("det1", signal)
    ts.run(algorithm="dynamic-simple")

    seg_ids = ts.get_segments_ID("det1")
    assert len(np.unique(seg_ids)) == 2


# === Error / edge case tests ===

def test_run_raises_if_no_time_added():
    signal = np.zeros(N_POINTS)
    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=2, post_buffer=2, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_signal("det1", signal)
    with pytest.raises(ValueError):
        ts.run(algorithm="dynamic")


def test_run_raises_on_invalid_scheme():
    time = np.linspace(0, 1, N_POINTS)
    signal = np.zeros_like(time)

    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=1.0, lower_threshold=np.nan,
        pre_buffer=2, post_buffer=2, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_time(time)
    ts.add_signal("det1", signal)
    with pytest.raises(ValueError, match="Invalid triggering algorithm"):
        ts.run(algorithm="banana")


def test_run_warns_if_no_triggers_found():
    time = np.linspace(0, 1, N_POINTS)
    signal = np.ones_like(time) * 0.1  # never crosses threshold

    ts = TriggeringSystem(
        trigger_detector_name="det1", threshold=5.0, lower_threshold=np.nan,
        pre_buffer=2, post_buffer=2, max_triggers=10,
        debounce_enabled=False, min_window_duration=-1
    )
    ts.add_time(time)
    ts.add_signal("det1", signal)
    ts.run(algorithm="dynamic")

    output = ts.get_signals("det1")
    assert len(output) == 0


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
