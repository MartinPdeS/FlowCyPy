from abc import ABC, abstractmethod
import numpy as np
from FlowCyPy.binary import filtering
from FlowCyPy.helper import validate_units
from FlowCyPy import units

class SignalProcessor(ABC):
    """
    Abstract base class for signal processing operations.
    """
    @abstractmethod
    def apply(self, signal: np.ndarray) -> None:
        """
        Applies a signal processing transformation **in-place**.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        pass

class BaselineRestorator(SignalProcessor):
    """
    Applies a baseline restoration filter by subtracting the minimum value over a given window size.

    Parameters
    ----------
    window_size : int
        Number of past samples to consider for the minimum value.
        If set to -1, it acts as if the window is infinite.
    """
    def __init__(self, window_size: int):
        self.window_size = window_size

    def apply(self, signal: np.ndarray, sampling_rate: units.Quantity, **kwargs) -> np.ndarray:
        """
        Applies baseline restoration in-place.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        window_size_bin = int((self.window_size * sampling_rate).to('').magnitude)
        filtering.apply_baseline_restoration(signal=signal, window_size=window_size_bin)

        return signal


class BesselLowPass(SignalProcessor):
    """
    Applies a Bessel low-pass filter to smooth the signal.

    Parameters
    ----------
    cutoff : float
        The cutoff frequency for the filter.
    order : int
        The order of the filter.
    gain : float
        The gain applied after filtering.
    """
    @validate_units(cutoff=units.hertz)
    def __init__(self, cutoff: units.Quantity, order: int, gain: float):
        self.cutoff = cutoff
        self.order = order
        self.gain = gain

    def apply(self, signal: np.ndarray, sampling_rate: units.Quantity, **kwargs) -> None:
        """
        Applies Bessel low-pass filtering in-place.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        filtering.apply_bessel_lowpass_filter(
            signal=signal,
            sampling_rate=sampling_rate.to('hertz').magnitude,
            cutoff=self.cutoff.to('hertz').magnitude,
            order=self.order,
            gain=self.gain
        )

        return signal

class ButterworthlLowPass(SignalProcessor):
    """
    Applies a Bessel low-pass filter to smooth the signal.

    Parameters
    ----------
    cutoff : float
        The cutoff frequency for the filter.
    order : int
        The order of the filter.
    gain : float
        The gain applied after filtering.
    """
    @validate_units(cutoff=units.hertz)
    def __init__(self, cutoff: units.Quantity, order: int, gain: float):
        self.cutoff = cutoff
        self.order = order
        self.gain = gain

    def apply(self, signal: np.ndarray, sampling_rate: units.Quantity, **kwargs) -> None:
        """
        Applies Bessel low-pass filtering in-place.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        filtering.apply_butterworth_lowpass_filter(
            signal=signal,
            sampling_rate=sampling_rate.to('hertz').magnitude,
            cutoff=self.cutoff.to('hertz').magnitude,
            order=self.order,
            gain=self.gain
        )

        return signal
