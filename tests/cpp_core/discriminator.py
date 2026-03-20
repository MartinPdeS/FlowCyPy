import numpy as np
import pytest
from FlowCyPy.signal_processing.discriminator import DoubleThreshold, FixedWindow
from FlowCyPy.units import ureg

N_POINTS = 1000


# ----------------- TESTS -----------------
def test_add_time_and_signal_accept_valid_inputs():
    discriminator = FixedWindow(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
    )
    time = np.linspace(0, 1, N_POINTS) * ureg.second
    signal = np.zeros_like(time) * ureg.volt
    discriminator.add_time(time)
    discriminator.add_channel("det1", signal)


def test_add_time_rejects_bad_shape():
    discriminator = FixedWindow(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
    )
    with pytest.raises(AttributeError):
        discriminator.add_time(np.zeros((10, 10)))


def test_add_channel_rejects_bad_shape():
    discriminator = FixedWindow(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
    )
    with pytest.raises(AttributeError):
        discriminator.add_channel("det1", np.zeros((5, 5)))


def test_fixed_window_triggering_extracts_expected_segments():
    time = np.linspace(0, 1, N_POINTS) * ureg.second
    signal = np.zeros_like(time)
    signal[100:120] = 2.0
    signal[400:420] = 2.0
    signal[800:820] = 2.0
    signal = signal * ureg.volt

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

    discriminator.add_time(time)
    discriminator.add_channel("det1", signal)

    discriminator.run()

    signals = discriminator.trigger.get_segmented_signal("det1")

    ids = discriminator.trigger.segment_ids
    assert len(np.unique(ids)) == 3
    assert len(signals) > 0


def test_dynamic_triggering_detects_rising_and_falling_edges():
    time = np.linspace(0, 1, N_POINTS) * ureg.second
    signal = np.zeros_like(time)
    signal[100:150] = 2.0
    signal[300:380] = 2.0
    signal = signal * ureg.volt

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

    discriminator.add_time(time)
    discriminator.add_channel("det1", signal)
    discriminator.run()

    seg_ids = discriminator.trigger.segment_ids
    assert len(np.unique(seg_ids)) == 2


def test_dynamic_simple_triggering_segments_plateaus():
    time = np.linspace(0, 1, N_POINTS) * ureg.second
    signal = np.zeros_like(time)
    signal[200:250] = 3.0
    signal[700:760] = 3.0
    signal = signal * ureg.volt

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=2.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=3,
        max_triggers=3,
        debounce_enabled=False,
        min_window_duration=-1,
    )
    discriminator.add_time(time)
    discriminator.add_channel("det1", signal)

    discriminator.run()

    seg_ids = discriminator.trigger.segment_ids
    assert len(np.unique(seg_ids)) == 2


# === Error / edge case tests ===


def test_run_raises_if_no_time_added():
    signal = np.zeros(N_POINTS) * ureg.volt
    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=1.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )

    discriminator.add_channel("det1", signal)
    with pytest.raises(RuntimeError):
        discriminator.run()


def test_run_warns_if_no_triggers_found():
    time = np.linspace(0, 1, N_POINTS) * ureg.second
    signal = np.ones_like(time) * 0.1 * ureg.volt  # never crosses threshold

    discriminator = DoubleThreshold(
        trigger_channel="det1",
        threshold=5.0 * ureg.volt,
        pre_buffer=2,
        post_buffer=2,
        max_triggers=10,
        debounce_enabled=False,
        min_window_duration=-1,
    )
    discriminator.add_time(time)
    discriminator.add_channel("det1", signal)
    discriminator.run()

    output = discriminator.trigger.get_segmented_signal("det1")
    assert len(output) == 0


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
