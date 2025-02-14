import numpy as np
from typing import List
from FlowCyPy.units import second, volt, Quantity
from scipy.signal import butter, filtfilt
import pandas as pd
import pint_pandas
from FlowCyPy.peak_locator import BasePeakLocator
from copy import copy


class ProxyDetector():
    def __init__(self, signal, time):
        self.name = str(id(self))
        self.signal = signal
        self.time = time
        self.dt = time[1] - time[0]

        self.dataframe = pd.DataFrame(
            data={
                'Signal': pint_pandas.PintArray(self.signal, dtype=self.signal.units),
                'Time': pint_pandas.PintArray(self.time, dtype=self.time.units)
            }
        )

    def set_peak_locator(self, algorithm: BasePeakLocator, compute_peak_area: bool = True) -> None:
        # Ensure the algorithm is an instance of BasePeakLocator
        if not isinstance(algorithm, BasePeakLocator):
            raise TypeError("The algorithm must be an instance of BasePeakLocator.")

        # Ensure the detector has signal data available for analysis
        if not hasattr(self, 'dataframe') or self.dataframe is None:
            raise RuntimeError("The detector does not have signal data available for peak detection.")

        # Set the algorithm and perform peak detection
        self.algorithm = copy(algorithm)
        self.algorithm.init_data(self.dataframe)
        self.algorithm.detect_peaks(compute_area=compute_peak_area)

    def get_properties(self) -> List[List[str]]:
        return [
            ['name', 'proxy']
        ]


def generate_dummy_detector(time: np.ndarray, centers: List[float], heights: List[float], stds: List[float]):
    """
    Generate a synthetic signal composed of multiple Gaussian pulses.

    Parameters
    ----------
    time : numpy.ndarray
        A numpy array representing the time axis over which the signal is generated.
    centers : list of floats
        A list of centers (in time) for each Gaussian pulse.
    heights : list of floats
        A list of peak heights (amplitudes) for each Gaussian pulse.
    stds : list of floats
        A list of widths (standard deviations) for each Gaussian pulse.

    Returns
    -------
    numpy.ndarray
        A numpy array representing the generated signal composed of Gaussian pulses.
    """
    time = Quantity(time, second)
    centers = Quantity(centers, second)
    heights = Quantity(heights, volt)
    stds = Quantity(stds, second)

    signal = np.zeros_like(time) * volt

    for center, height, sigma in zip(centers, heights, stds):
        signal += height * np.exp(-((time - center) ** 2) / (2 * sigma ** 2))

    return ProxyDetector(time=time, signal=signal)

from scipy.signal import bessel, sosfilt
import numpy as np
import pint
import pint_pandas

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
