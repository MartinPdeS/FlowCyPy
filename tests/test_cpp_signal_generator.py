import numpy as np
import pytest

from FlowCyPy.binary import interface_signal_generator


# === Shared signal model setup (used by most tests) ===

WIDTHS = np.full(5, 0.1)
CENTERS = np.linspace(0.2, 0.8, 5)
COUPLING_POWER = np.linspace(1.0, 2.0, 5)

N_ELEMENTS = 5000
TIME_ARRAY = np.linspace(0.0, 1.0, N_ELEMENTS)
BACKGROUND_POWER = 1.0


@pytest.fixture
def signal_generator():
    """
    Returns a SignalGenerator instance with a predefined time array.
    This is used to avoid code duplication in tests.
    """
    signal_generator = interface_signal_generator.SignalGenerator(N_ELEMENTS)
    signal_generator.add_signal("Time", TIME_ARRAY)
    signal_generator.create_zero_signal(signal_name="Signal")
    return signal_generator

# === Signal tests ===

def test_signal_after_pulse_generation(signal_generator):
    """
    Test that the signal is generated correctly after pulse generation.
    """
    signal_generator.generate_pulses(
        widths=WIDTHS,
        centers=CENTERS,
        coupling_power=COUPLING_POWER,
        background_power=BACKGROUND_POWER
    )

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape
    assert array.dtype == np.float64
    assert np.all(array >= 0.0)


def test_signal_constant_addition(signal_generator):
    """
    Test that adding a constant modifies the signal correctly.
    """
    constant = 10.0
    signal_generator.add_constant(constant)

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape
    assert array.dtype == np.float64
    assert np.all(array >= 0.0)
    assert np.isclose(np.mean(array), constant, atol=0.1)


# === Gaussian noise tests ===

def test_add_gaussian_noise_changes_signal(signal_generator):
    """
    Test that adding Gaussian noise modifies the signal.
    """

    signal_generator.add_gaussian_noise(
        mean=0.0,
        standard_deviation=1.0
    )

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape

    assert np.isclose(np.mean(array), 0.0, atol=0.1)

    assert np.isclose(np.std(array), 1.0, atol=0.1)


# === Poisson noise ===

def test_add_poisson_noise(signal_generator):
    """
    Test that adding Poisson noise modifies the signal.
    """
    signal_generator.add_poisson_noise()

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert np.all(np.isclose(array, 0.0))


def test_poisson_noise_statistics(signal_generator):
    """
    Test that Poisson noise has the expected statistical properties.
    """

    constant = 10.0
    signal_generator.add_constant(10.0)

    signal_generator.add_poisson_noise()
    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert np.isclose(np.mean(array), constant, atol=0.1)

    assert np.isclose(np.std(array), np.sqrt(constant), atol=0.1)


# === API call tests ===

def test_butterworth_low_pass_filter(signal_generator):
    """
    Test that the low-pass filter modifies the signal correctly.
    """
    signal_generator.add_gaussian_noise(mean=0.0, standard_deviation=1.0)

    signal_generator.apply_butterworth_lowpass_filter(sampling_rate=1, cutoff_frequency=10.0, order=2, gain=1.0)

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape
    assert array.dtype == np.float64
    assert not np.allclose(array, 0.0)
    assert np.max(np.abs(array)) < 10.0

def test_bessel_low_pass_filter(signal_generator):
    """
    Test that the Bessel low-pass filter modifies the signal correctly.
    """
    signal_generator.add_gaussian_noise(mean=0.0, standard_deviation=1.0)

    signal_generator.apply_bessel_lowpass_filter(sampling_rate=1, cutoff_frequency=10.0, order=2, gain=1.0)

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape
    assert array.dtype == np.float64
    assert not np.allclose(array, 0.0)
    assert np.max(np.abs(array)) < 10.0


def test_baseline_restoration(signal_generator):
    """
    Test that baseline restoration modifies the signal correctly.
    """
    signal_generator.add_gaussian_noise(mean=0.0, standard_deviation=1.0)

    signal_generator.apply_baseline_restoration(window_size=10)

    array = signal_generator.get_signal("Signal")

    array = np.asarray(array)

    assert array.shape == TIME_ARRAY.shape
    assert array.dtype == np.float64
    assert not np.allclose(array, 0.0)
    assert np.max(np.abs(array)) < 10.0

if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
