from FlowCyPy.binary import interface_signal_generator
from FlowCyPy import units

class SignalGenerator(interface_signal_generator.SignalGenerator):
    """
    A class to generate signals for flow cytometry applications.

    This class extends the SignalGenerator from the FlowCyPy binary interface
    to provide additional functionality specific to flow cytometry signal generation.
    """

    def __init__(self, n_elements: int, time_units: units.Quantity, signal_units: units.Quantity):

        """
        Initializes the SignalGenerator with the specified number of elements and units.

        Parameters
        ----------
        n_elements : int
            The number of elements in the signal.
        time_units : units.Quantity, optional
            The units for time, default is seconds.
        signal_units : units.Quantity, optional
            The units for the signal, default is volts.
        """
        self.time_units = time_units
        self.signal_units = signal_units

        super().__init__(n_elements)

    def add_signal(self, signal_name: str, signal_data: units.Quantity) -> None:
        """
        Adds a signal with the specified name and data, converting the data to the defined signal units.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add.
        signal_data : units.Quantity
            The signal data in the specified units.
        """
        assert signal_data.dimensionality == self.signal_units.dimensionality, \
            f"Signal units {signal_data.units} do not match defined signal units {self.signal_units}."

        self._cpp_add_signal(signal_name, signal_data.to(self.signal_units).magnitude)

    def add_time(self, time_data: units.Quantity) -> None:
        """
        Adds a time array to the signal generator, converting it to the defined time units.

        Parameters
        ----------
        time_data : units.Quantity
            The time data in the specified units.
        """
        assert time_data.dimensionality == self.time_units.dimensionality, \
            f"Time units {time_data.units} do not match defined time units {self.time_units}."

        self._cpp_add_signal("Time", time_data.to(self.time_units).magnitude)

    def get_time(self) -> units.Quantity:
        """
        Retrieves the time array for the signal generator.

        Returns
        -------
        units.Quantity
            The time array in the specified time units.
        """
        time_data = self._cpp_get_signal("Time")
        return time_data * self.time_units

    def get_signal(self, signal_name: str) -> units.Quantity:
        """
        Retrieves the signal with the specified name and converts it to the defined signal units.

        Parameters
        ----------
        signal_name : str
            The name of the signal to retrieve.

        Returns
        -------
        units.Quantity
            The signal data in the specified units.
        """
        signal_data = self._cpp_get_signal(signal_name)
        return signal_data * self.signal_units

    def get_time(self) -> units.Quantity:
        """
        Retrieves the time array for the signal generator.

        Returns
        -------
        units.Quantity
            The time array in the specified time units.
        """
        time_data = self._cpp_get_signal("Time")
        return time_data * self.time_units

    def multiply(self, factor: units.Quantity, signal_name: str = None) -> None:
        """
        Multiplies the specified signal by a given factor.

        Parameters
        ----------
        signal_name : str
            The name of the signal to multiply.
        factor : float
            The factor by which to multiply the signal.
        """
        if signal_name is None:
            self._cpp_multiply(factor=factor.magnitude)
        else:
            self._cpp_multiply_signal(signal_name=signal_name, factor=factor.magnitude)

    def add_constant(self, constant: units.Quantity, signal_name: str = None) -> None:
        """
        Adds a constant value to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add the constant to.
        constant : float
            The constant value to add to the signal.
        """
        assert constant.dimensionality == self.signal_units.dimensionality, \
            f"Constant units {constant.units} do not match signal units {self.signal_units}."

        if signal_name is None:
            self._cpp_add_constant(
                constant=constant.to(self.signal_units).magnitude
            )
        else:
            self._cpp_add_constant_to_signal(
                signal_name=signal_name,
                constant=constant.to(self.signal_units).magnitude
            )

    def apply_gaussian_noise(self, mean: units.Quantity, standard_deviation: units.Quantity, signal_name: str = None) -> None:
        """
        Adds Gaussian noise to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add noise to.
        std : float
            The standard deviation of the Gaussian noise.
        """
        assert standard_deviation.dimensionality == self.signal_units.dimensionality, \
            f"Noise units {standard_deviation.units} do not match signal units {self.signal_units}."

        assert mean.dimensionality == self.signal_units.dimensionality, \
            f"Mean units {mean.units} do not match signal units {self.signal_units}."

        if signal_name is None:
            self._cpp_apply_gaussian_noise(
                mean=mean.to(self.signal_units).magnitude,
                standard_deviation=standard_deviation.to(self.signal_units).magnitude
            )
        else:
            self._cpp_apply_gaussian_noise_to_signal(
                signal_name=signal_name,
                mean=mean.to(self.signal_units).magnitude,
                standard_deviation=standard_deviation.to(self.signal_units).magnitude
            )

    def apply_poisson_noise(self, signal_name: str = None) -> None:
        """
        Adds Poisson noise to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add Poisson noise to.
        """
        if signal_name is None:
            self._cpp_apply_poisson_noise()
        else:
            self._cpp_apply_poisson_noise_to_signal(signal_name=signal_name)

    def apply_baseline_restoration(self, window_size: units.Quantity, signal_name: str = None) -> None:
        """
        Applies baseline restoration to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to apply baseline restoration to.
        """
        assert window_size.dimensionality == self.time_units.dimensionality, \
            f"Window size units {window_size.units} do not match time units {self.time_units}."

        time = self._cpp_get_signal("Time")

        dt = time[1] - time[0]  # Assuming uniform time intervals

        window_size_bins = int(window_size.to(self.time_units).magnitude / dt.magnitude)

        if signal_name is None:
            self._cpp_apply_baseline_restoration(window_size=window_size_bins)
        else:
            self._cpp_apply_baseline_restoration_to_signal(window_size=window_size_bins, signal_name=signal_name)

    def apply_butterworth_lowpass_filter(self, sampling_rate: units.Quantity, cutoff_frequency: units.Quantity, order: int = 1, gain: units.Quantity = 1.0 * units.dimensionless, signal_name: str = None) -> None:
        """
        Applies a Butterworth low-pass filter to the specified signal.

        Parameters
        ----------
        sampling_rate : units.Quantity
            The sampling rate of the signal.
        cutoff_frequency : units.Quantity
            The cutoff frequency of the filter.
        order : int, optional
            The order of the Butterworth filter, default is 1.
        gain : units.Quantity, optional
            The gain of the filter, default is 1.0.
        signal_name : str, optional
            The name of the signal to apply the filter to.
        """
        assert sampling_rate.dimensionality == units.hertz.dimensionality, \
            f"Sampling rate units {sampling_rate.units} do not match hertz."

        assert cutoff_frequency.dimensionality == units.hertz.dimensionality, \
            f"Cutoff frequency units {cutoff_frequency.units} do not match hertz."

        if signal_name is None:
            self._cpp_apply_butterworth_lowpass_filter(
                sampling_rate=sampling_rate.to(units.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(units.hertz).magnitude,
                order=order,
                gain=gain.magnitude
            )
        else:
            self._cpp_apply_butterworth_lowpass_filter_to_signal(
                signal_name=signal_name,
                sampling_rate=sampling_rate.to(units.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(units.hertz).magnitude,
                order=order,
                gain=gain.magnitude
            )

    def apply_bessel_lowpass_filter(self, sampling_rate: units.Quantity, cutoff_frequency: units.Quantity, gain: units.Quantity = 1.0 * units.dimensionless, order: int = 1, signal_name: str = None) -> None:
        """
        Applies a Bessel low-pass filter to the specified signal.

        Parameters
        ----------
        sampling_rate : units.Quantity
            The sampling rate of the signal.
        cutoff_frequency : units.Quantity
            The cutoff frequency of the filter.
        order : int, optional
            The order of the Bessel filter, default is 1.
        gain : units.Quantity, optional
            The gain of the filter, default is 1.0.
        signal_name : str, optional
            The name of the signal to apply the filter to.
        """
        assert sampling_rate.dimensionality == units.hertz.dimensionality, \
            f"Sampling rate units {sampling_rate.units} do not match hertz."

        assert cutoff_frequency.dimensionality == units.hertz.dimensionality, \
            f"Cutoff frequency units {cutoff_frequency.units} do not match hertz."

        if signal_name is None:
            self._cpp_apply_bessel_lowpass_filter(
                sampling_rate=sampling_rate.to(units.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(units.hertz).magnitude,
                order=order,
                gain=gain.magnitude
            )
        else:
            self._cpp_apply_bessel_lowpass_filter_to_signal(
                signal_name=signal_name,
                sampling_rate=sampling_rate.to(units.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(units.hertz).magnitude,
                order=order,
                gain=gain.magnitude
            )

    def generate_pulses(self, widths: units.Quantity, centers: units.Quantity, amplitudes: units.Quantity, base_level: units.Quantity, signal_name: str = None) -> None:
        """
        Generates gaussian pulses with specified widths, centers, and amplitudes.

        Parameters
        ----------
        widths : units.Quantity
            The widths of the pulses.
        centers : units.Quantity
            The centers of the pulses.
        amplitudes : units.Quantity
            The amplitudes of the pulses.
        signal_name : str, optional
            The name of the signal to add the pulses to.
        base_level : units.Quantity
            The base level of the signal, which is added to the amplitudes of the pulses.
        """
        assert widths.units.dimensionality == self.time_units.dimensionality, \
            f"Width units {widths.units} do not match time units {self.time_units}."

        assert centers.units.dimensionality == self.time_units.dimensionality, \
            f"Center units {centers.units} do not match time units {self.time_units}."

        assert amplitudes.units.dimensionality == self.signal_units.dimensionality, \
            f"Amplitude units {amplitudes.units} do not match signal units {self.signal_units}."

        if signal_name is None:

            self._cpp_generate_pulses(
                widths=widths.to(self.time_units).magnitude,
                centers=centers.to(self.time_units).magnitude,
                amplitudes=amplitudes.to(self.signal_units).magnitude,
                base_level=base_level.to(self.signal_units).magnitude
            )
        else:
            self._cpp_generate_pulses_to_signal(
                signal_name=signal_name,
                widths=widths.to(self.time_units).magnitude,
                centers=centers.to(self.time_units).magnitude,
                amplitudes=amplitudes.to(self.signal_units).magnitude,
                base_level=base_level.to(self.signal_units).magnitude
            )