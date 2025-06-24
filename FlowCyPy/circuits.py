from FlowCyPy import helper
from FlowCyPy import units
from FlowCyPy.binary import interface_circuits



class SignalProcessor():
    """
    Abstract base class for signal processing operations.
    """


class BaselineRestorator(interface_circuits.BaseLineRestoration, SignalProcessor):
    """
    Applies a baseline restoration filter by subtracting the minimum value over a given window size.

    Parameters
    ----------
    window_size : int
        Number of past samples to consider for the minimum value.
        If set to -1, it acts as if the window is infinite.
    """
    @helper.validate_input_units(window_size=units.second)
    def __init__(self, window_size: units.Quantity):
        self.window_size = window_size
        super().__init__()

    def process(self, signal_generator: object, sampling_rate: units.Quantity, **kwargs) -> None:
        """
        Processes the signal generator to apply baseline restoration.

        Parameters
        ----------
        signal_generator : object
            An object that generates the signal to be processed.
        sampling_rate : units.Quantity
            The sampling rate of the signal.

        Returns
        -------
        units.Quantity
            The processed signal with baseline restoration applied.
        """
        self._cpp_window_size = int((self.window_size * sampling_rate).to('').magnitude)

        self._cpp_process(signal_generator)


class BesselLowPass(interface_circuits.BesselLowPassFilter, SignalProcessor):
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
    @helper.validate_input_units(cutoff=units.hertz)
    def __init__(self, cutoff: units.Quantity, order: int, gain: float):
        self.cutoff = cutoff
        self.order = order
        self.gain = gain

        super().__init__()

    def process(self, signal_generator: object, sampling_rate: units.Quantity, **kwargs) -> units.Quantity:
        """
        Applies Bessel low-pass filtering in-place.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        self._cpp_sampling_rate = sampling_rate.to('hertz').magnitude
        self._cpp_cutoff_frequency = self.cutoff.to('hertz').magnitude
        self._cpp_order = self.order
        self._cpp_gain = self.gain

        self._cpp_process(signal_generator)


class ButterworthlLowPass(interface_circuits.ButterworthLowPassFilter, SignalProcessor):
    """
    Applies a Butterworth low-pass filter to smooth the signal.
    Parameters
    ----------
    cutoff : float
        The cutoff frequency for the filter.
    order : int
        The order of the filter.
    gain : float
        The gain applied after filtering.
    """
    @helper.validate_input_units(cutoff=units.hertz)
    def __init__(self, cutoff: units.Quantity, order: int, gain: float):
        self.cutoff = cutoff
        self.order = order
        self.gain = gain

        super().__init__()

    def process(self, signal_generator: object, sampling_rate: units.Quantity, **kwargs) -> None:
        """
        Applies Bessel low-pass filtering in-place.

        Parameters
        ----------
        signal : np.ndarray
            The signal to be modified in-place.
        """
        self._cpp_sampling_rate = sampling_rate.to('hertz').magnitude
        self._cpp_cutoff_frequency = self.cutoff.to('hertz').magnitude
        self._cpp_order = self.order
        self._cpp_gain = self.gain

        self._cpp_process(signal_generator)
