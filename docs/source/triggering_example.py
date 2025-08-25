import numpy as np
import matplotlib.pyplot as plt
from FlowCyPy.binary import triggering_system

def generate_noisy_signal(n_points=1000, seed=42):
    """
    Generate a synthetic noisy signal and a corresponding time array.

    The base signal is a noisy sine wave with:
      - brief spurious spikes inserted at a few locations (to simulate false triggers)
      - one sustained high region (to simulate a valid trigger event)

    Parameters
    ----------
    n_points : int, optional
        The number of data points in the signal (default is 1000).
    seed : int, optional
        The random seed for reproducibility (default is 42).

    Returns
    -------
    t : np.ndarray
        A linearly spaced time array from 0 to 10 seconds.
    signal : np.ndarray
        The synthetic signal array.
    """
    np.random.seed(seed)
    t = np.linspace(0, 10, n_points)
    # Base sine wave scaled to range ~0 to 1 with added noise.
    base = 0.5 * np.sin(2 * np.pi * 1 * t) + 0.5
    noise = 0.1 * np.random.randn(n_points)
    signal = base + noise
    # Insert brief spurious spikes (simulate false triggers)
    for idx in [300, 600, 800]:
        signal[idx:idx+3] += 0.3
    # Insert a sustained high region (simulate a valid trigger event)
    signal[450:470] += 0.4
    return t, signal

def plot_debouncing_effect():
    """
    Plot the effect of debouncing and lower threshold on trigger detection.

    Two subplots are created:
      - Left: Dynamic triggering with debouncing disabled.
      - Right: Dynamic triggering with debouncing enabled (using min_duration).

    Both plots show:
      - The synthetic signal.
      - The upper threshold (dashed line) and lower threshold (dotted line).
      - Scatter points marking the trigger events (first sample of each segment).
    """
    t, signal = generate_noisy_signal()

    kwargs = dict(
        threshold=0.7,
        pre_buffer=1,
        post_buffer=1,
        max_triggers=-1,
        lower_threshold=0.7,
        scheme="dynamic",
        trigger_detector_name="detector1",
    )

    triggering_no_debouncer = triggering_system.TriggeringSystem(debounce_enabled=False, min_window_duration=-1, **kwargs)
    triggering_no_debouncer.add_time(t)
    triggering_no_debouncer.add_signal("detector1", signal)
    times_no_debounce, signals_no_debounce, detectors_no_debounce, segment_ids_no_debounce = triggering_no_debouncer.run()
    index_sequence_no_debounce = np.where(np.diff(segment_ids_no_debounce) == 1)
    trigger_times_no_debounce = times_no_debounce[index_sequence_no_debounce]


    triggering_debouncer = triggering_system.TriggeringSystem(debounce_enabled=True, min_window_duration=10, **kwargs)
    triggering_debouncer.add_time(t)
    triggering_debouncer.add_signal("detector1", signal)
    times_debounce, signals_debounce, detectors_debounce, segment_ids_debounce = triggering_debouncer.run()
    index_sequence_debounce = np.where(np.diff(segment_ids_debounce) == 1)
    trigger_times_debounce = times_debounce[index_sequence_debounce]

    # Create subplots.
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    # Plot without debouncing.
    axes[0].scatter(trigger_times_no_debounce, np.interp(trigger_times_no_debounce, t, signal), color="C3", marker="o", s=100, label="Triggers (no debounce)")
    axes[0].set_title("Dynamic Triggering (No Debounce)")


    # Plot with debouncing.
    axes[1].scatter(trigger_times_debounce, np.interp(trigger_times_debounce, t, signal), color="C4", marker="o", s=100, label="Triggers (with debounce)")
    axes[1].set_title("Dynamic Triggering (With Debounce)")

    for ax in axes:
        ax.plot(t, signal, label="Signal", color="black", zorder=-1)
        ax.axhline(kwargs['threshold'], color="C1", linestyle="--", label="Upper Threshold")
        ax.axhline(kwargs['lower_threshold'], color="C2", linestyle=":", label="Lower Threshold")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Signal Amplitude")
        ax.legend(loc='lower right')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_debouncing_effect()
