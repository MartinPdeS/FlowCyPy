import numpy as np
import pint_pandas
from scipy.signal import butter, bessel, sosfilt
import pint


def bessel_lowpass_filter(signal: pint_pandas.PintArray, cutoff: pint.Quantity, sampling_rate: pint.Quantity, order: int = 4) -> np.ndarray:
    """
    Applies a Bessel low-pass filter to a given signal while maintaining pint-based units.

    Parameters
    ----------
    signal : pint_pandas.PintArray
        The input signal to be filtered, with associated units.
    cutoff : pint.Quantity
        The cutoff frequency of the filter (e.g., `30 * units.hertz`).
    sampling_rate : pint.Quantity
        The sampling rate of the signal (e.g., `1000 * units.hertz`).
    order : int, optional
        The order of the Bessel filter (default: 4).

    Returns
    -------
    pint_pandas.PintArray
        The filtered signal with preserved units.

    Raises
    ------
    ValueError
        If the cutoff frequency is greater than or equal to half the sampling rate (Nyquist frequency).
    """

    # Ensure the cutoff and sampling rate are converted to Hertz
    cutoff_hz = cutoff.to("hertz").magnitude
    fs_hz = sampling_rate.to("hertz").magnitude
    nyquist_freq = 0.5 * fs_hz

    if cutoff_hz >= nyquist_freq:
        raise ValueError("Cutoff frequency must be below the Nyquist frequency (sampling_rate / 2).")

    # Design the low-pass Bessel filter
    sos = bessel(N=order, Wn=cutoff_hz / nyquist_freq, btype='low', analog=False, output='sos')

    # Apply the filter
    filtered_signal = sosfilt(sos, signal)

    # Return the filtered signal with the same units
    return filtered_signal


def dc_highpass_filter(signal: pint_pandas.PintArray, cutoff: pint.Quantity, sampling_rate: pint.Quantity, order: int = 4) -> pint_pandas.PintArray:
    """
    Applies a high-pass Butterworth filter to a given signal while maintaining pint-based units.

    Parameters
    ----------
    signal : pint_pandas.PintArray
        The input signal to be filtered, with associated units.
    cutoff : pint.Quantity
        The cutoff frequency of the filter (e.g., `5 * units.hertz`).
    sampling_rate : pint.Quantity
        The sampling rate of the signal (e.g., `1000 * units.hertz`).
    order : int, optional
        The order of the high-pass filter (default: 4).

    Returns
    -------
    pint_pandas.PintArray
        The filtered signal with preserved units.

    Raises
    ------
    ValueError
        If the cutoff frequency is greater than or equal to half the sampling rate (Nyquist frequency).
    """

    # Ensure the cutoff and sampling rate are converted to Hertz
    cutoff_hz = cutoff.to("hertz").magnitude
    fs_hz = sampling_rate.to("hertz").magnitude
    nyquist_freq = 0.5 * fs_hz

    if cutoff_hz >= nyquist_freq:
        raise ValueError("Cutoff frequency must be below the Nyquist frequency (sampling_rate / 2).")

    # Design the high-pass Butterworth filter
    sos = butter(N=order, Wn=cutoff_hz / nyquist_freq, btype='high', analog=False, output='sos')

    # Apply the filter
    filtered_signal = sosfilt(sos, signal)

    # Return the filtered signal with the same units
    return filtered_signal
