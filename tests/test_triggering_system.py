import numpy as np
import pytest

# Import the C++ module exposed via pybind11.
from FlowCyPy.binary.interface_triggering_system import DOUBLETHRESHOLD # type: ignore

# ---------------------------------------------------------------------------
# Fixtures for synthetic signals and time arrays
# ---------------------------------------------------------------------------
@pytest.fixture
def simple_signal():
    """
    Returns a simple synthetic signal and a corresponding time array.

    The time array is linearly spaced from 0 to 10 seconds with 1000 samples.
    The signal is initially a sine wave (scaled between 0 and 1) that we can modify
    later to create clear trigger events.
    """
    t = np.linspace(0, 10, 1000)
    # Create a sine wave shifted to be always positive (range 0 to 1)
    signal = 0.5 * np.sin(2 * np.pi * 1 * t) + 0.5
    return t, signal

@pytest.fixture
def no_trigger_signal():
    """
    Returns a signal that never exceeds the threshold.

    The signal is constant and remains below the trigger threshold.
    """
    t = np.linspace(0, 10, 1000)
    signal = np.full_like(t, 0.5)  # constant signal
    return t, signal

# ---------------------------------------------------------------------------
# Tests for DOUBLETHRESHOLD functionality
# ---------------------------------------------------------------------------
def test_add_signal_and_time(simple_signal):
    """
    Test that add_time() and add_signal() correctly add the time and signal data
    to the DOUBLETHRESHOLD instance.
    """
    t, signal = simple_signal
    ts = DOUBLETHRESHOLD(
        trigger_detector_name="detector1",
        pre_buffer=5,
        post_buffer=5,
        max_triggers=10,
    )
    ts._cpp_add_time(t)
    ts._cpp_add_signal("detector1", signal)

    # Check that the global time array is set.
    np.testing.assert_array_equal(ts.trigger.global_time, t)

def test_no_time_error(simple_signal):
    """
    Test that if no time array is provided, the run() method raises a RuntimeError.
    """
    t, signal = simple_signal
    ts = DOUBLETHRESHOLD(
        trigger_detector_name="detector1",
        pre_buffer=5,
        post_buffer=5,
    )
    ts._cpp_add_signal("detector1", signal)
    with pytest.raises(ValueError):
        ts._cpp_run(threshold=0.6, lower_threshold=0.6, min_window_duration=-1, debounce_enabled=False)

def test_no_trigger(no_trigger_signal):
    """
    Test that when the signal never exceeds the threshold, run() produces
    empty arrays and issues a warning.
    """
    t, signal = no_trigger_signal
    ts = DOUBLETHRESHOLD(
        trigger_detector_name="detector1",
        pre_buffer=5,
        post_buffer=5,
    )
    ts._cpp_add_time(t)
    ts._cpp_add_signal("detector2", signal)

    with pytest.raises(IndexError):
        ts._cpp_run(threshold=0.6, lower_threshold=0.6, min_window_duration=-1, debounce_enabled=False)

    # Expect that no triggers are found (empty arrays returned)
    assert len(ts.trigger.segmented_time) == 0
    assert len(ts.trigger.get_segmented_signal("detector2")) == 0

def test_trigger_fixed_window(simple_signal):
    """
    Test fixed-window triggering by creating a signal with a distinct trigger event.

    The synthetic signal is modified to produce a spike above the threshold so that
    a trigger is detected. The test verifies that the run() method returns non-empty
    output arrays.
    """
    t, _ = simple_signal
    # Create a signal that is zero except for a spike between indices 410 and 415.
    signal = np.zeros_like(t)
    signal[410:415] = 1.0  # spike well above a threshold of 0.6
    ts = DOUBLETHRESHOLD(
        trigger_detector_name="detector1",
        pre_buffer=5,
        post_buffer=5
    )
    ts._cpp_add_time(t)
    ts._cpp_add_signal("detector1", signal)
    ts._cpp_run(threshold=0.6, lower_threshold=0.6, min_window_duration=-1, debounce_enabled=False)
    # Expect non-empty output arrays (i.e. at least one trigger is detected).
    assert len(ts.trigger.segmented_time) > 0
    assert len(ts.trigger.get_segmented_signal("detector1")) > 0

def test_trigger_dynamic_single_threshold(simple_signal):
    """
    Test dynamic triggering (using single threshold mode) by creating a continuous
    region above the threshold with debouncing enabled.

    A segment is generated where the signal is high (above threshold) over a number
    of samples. The test checks that run() returns output arrays with at least one trigger.
    """
    t, _ = simple_signal
    # Create a signal that is zero except for a continuous high region between indices 300 and 350.
    signal = np.zeros_like(t)
    signal[300:350] = 1.0  # continuous high region
    ts = DOUBLETHRESHOLD(
        trigger_detector_name="detector1",
        pre_buffer=10,
        post_buffer=10,
    )
    ts._cpp_add_time(t)
    ts._cpp_add_signal("detector1", signal)
    ts._cpp_run(threshold=0.6, lower_threshold=0.6, debounce_enabled=True, min_window_duration=3)
    # Ensure that triggers are detected.
    assert len(ts.trigger.segmented_time) > 0
    assert len(ts.trigger.get_segmented_signal("detector1")) > 0
    # Check that at least one segment is present by examining segment IDs.
    unique_ids = np.unique(ts.trigger.segment_ids)
    assert len(unique_ids) >= 1

if __name__ == "__main__":
    pytest.main(["-W error", __file__])
