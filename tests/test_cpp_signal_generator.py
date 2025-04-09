import numpy as np
import pytest

from FlowCyPy.binary import interface_signal_generator

# === Shared signal model setup (used by most tests) ===

WIDTHS = np.full(5, 0.1)
CENTERS = np.linspace(0.2, 0.8, 5)
COUPLING_POWER = np.linspace(1.0, 2.0, 5)
TIME_ARRAY = np.linspace(0.0, 1.0, 100)
BACKGROUND_POWER = 1.0

# === Signal tests ===

def test_signal_after_pulse_generation():
    signal = np.zeros_like(TIME_ARRAY)
    interface_signal_generator.generate_pulses(
        signal=signal,
        widths=WIDTHS,
        centers=CENTERS,
        coupling_power=COUPLING_POWER,
        time=TIME_ARRAY,
        background_power=BACKGROUND_POWER
    )

    assert signal.shape == TIME_ARRAY.shape
    assert signal.dtype == np.float64
    assert np.all(signal >= 0.0)

# === Gaussian noise tests ===

def test_add_gaussian_noise_changes_signal():
    signal = np.zeros_like(TIME_ARRAY)

    interface_signal_generator.add_gaussian_noise(
        signal=signal,
        mean=0.0,
        standard_deviation=1.0
    )

    assert not np.allclose(signal, 0.0)

def test_add_gaussian_noise_statistics():
    signal = np.full(10000, 5.0)

    interface_signal_generator.add_gaussian_noise(
        signal=signal,
        mean=0.0,
        standard_deviation=1.0
    )

    assert np.abs(np.mean(signal) - 5.0) < 0.1
    assert 0.9 < np.std(signal) < 1.1

# === Poisson noise ===

def test_add_poisson_noise():
    signal = np.full_like(TIME_ARRAY, 5.0)
    before = signal.copy()
    interface_signal_generator.add_poisson_noise(signal=signal)
    assert not np.array_equal(signal, before)
    assert np.all(signal >= 0)

# === FFT filtering ===

def test_fft_filtering_runs_and_modifies_signal():
    time = np.linspace(0.0, 1.0, 1024)
    signal = np.sin(2 * np.pi * 50 * time).astype(np.float64)

    processed_signal = signal.copy()
    unprocessed_signal = signal.copy()

    dt = time[1] - time[0]
    interface_signal_generator.bessel_lowpass_filter(
        signal=processed_signal,
        sampling_rate=1 / dt,
        cutoff_frequency=10.0,
        order=2,
        gain=1
    )

    assert processed_signal.shape == unprocessed_signal.shape
    assert processed_signal.dtype == np.float64
    assert not np.allclose(processed_signal, unprocessed_signal)
    assert np.max(np.abs(processed_signal)) < np.max(np.abs(unprocessed_signal))

# === Noise in-place check ===

def test_noise_modifies_signal_inplace():
    signal = np.ones(100, dtype=np.float64) * 3.0

    interface_signal_generator.add_gaussian_noise(
        signal=signal,
        mean=0.0,
        standard_deviation=0.1
    )
    assert not np.allclose(signal, 3.0)

# === Baseline restoration tests ===

def test_baseline_restoration_global():
    signal = np.array([1, 2, 3, 4, 5, 6], dtype=np.float64)
    expected = signal.copy()
    expected[1:] = expected[1:] - 1

    interface_signal_generator.baseline_restoration(signal=signal, window_size=-1)

    np.testing.assert_allclose(signal[1:], expected[1:])

def test_baseline_restoration_sliding_window():
    original = np.array([5, 2, 3, 4, 6, 7, 2, 3, 1], dtype=np.float64)
    signal = original.copy()
    interface_signal_generator.baseline_restoration(signal=signal, window_size=3)

    assert signal[0] == 0
    assert signal[1] >= 0
    assert signal[2] >= 0
    assert signal.shape == original.shape
    assert signal.dtype == np.float64
    assert not np.allclose(signal, original)

if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
