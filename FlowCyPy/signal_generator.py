from TypedUnit import AnyUnit, Frequency, Time, ureg, validate_units

from FlowCyPy.binary import interface_signal_generator


class SignalGenerator(interface_signal_generator.SignalGenerator):
    """
    A class to generate signals for flow cytometry applications.

    This class extends the SignalGenerator from the FlowCyPy binary interface
    to provide additional functionality specific to flow cytometry signal generation.
    """

    def __init__(self, n_elements: int, time_units: Time, signal_units: AnyUnit):
        """
        Initializes the SignalGenerator with the specified number of elements and units.

        Parameters
        ----------
        n_elements : int
            The number of elements in the signal.
        time_units : Time, optional
            The units for time, default is seconds.
        signal_units : AnyUnit, optional
            The units for the signal, default is volts.
        """
        self.time_units = time_units
        self.signal_units = signal_units

        super().__init__(n_elements)

    def add_signal(self, signal_name: str, signal_data: AnyUnit) -> None:
        """
        Adds a signal with the specified name and data, converting the data to the defined signal units.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add.
        signal_data : AnyUnit
            The signal data in the specified units.
        """
        assert (
            signal_data.dimensionality == self.signal_units.dimensionality
        ), f"Signal units {signal_data.units} do not match defined signal units {self.signal_units}."

        self._cpp_add_signal(signal_name, signal_data.to(self.signal_units).magnitude)

    def add_time(self, time_data: Time) -> None:
        """
        Adds a time array to the signal generator, converting it to the defined time units.

        Parameters
        ----------
        time_data : Time
            The time data in the specified units.
        """
        assert (
            time_data.dimensionality == self.time_units.dimensionality
        ), f"Time units {time_data.units} do not match defined time units {self.time_units}."

        self._cpp_add_signal("Time", time_data.to(self.time_units).magnitude)

    def get_time(self) -> Time:
        """
        Retrieves the time array for the signal generator.

        Returns
        -------
        Any
            The time array in the specified time units.
        """
        time_data = self._cpp_get_signal("Time")
        return time_data * self.time_units

    def get_signal(self, signal_name: str) -> AnyUnit:
        """
        Retrieves the signal with the specified name and converts it to the defined signal units.

        Parameters
        ----------
        signal_name : str
            The name of the signal to retrieve.

        Returns
        -------
        AnyUnit
            The signal data in the specified units.
        """
        signal_data = self._cpp_get_signal(signal_name)
        return signal_data * self.signal_units

    def multiply(self, factor: AnyUnit, signal_name: str = None) -> None:
        """
        Multiplies the specified signal by a given factor.

        Parameters
        ----------
        signal_name : str
            The name of the signal to multiply.
        factor : AnyUnit
            The factor by which to multiply the signal.
        """
        if signal_name is None:
            self._cpp_multiply(factor=factor.magnitude)
        else:
            self._cpp_multiply_signal(signal_name=signal_name, factor=factor.magnitude)

    def add_constant(self, constant: AnyUnit, signal_name: str = None) -> None:
        """
        Adds a constant value to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add the constant to.
        constant : float
            The constant value to add to the signal.
        """
        assert (
            constant.dimensionality == self.signal_units.dimensionality
        ), f"Constant units {constant.units} do not match signal units {self.signal_units}."

        if signal_name is None:
            self._cpp_add_constant(constant=constant.to(self.signal_units).magnitude)
        else:
            self._cpp_add_constant_to_signal(
                signal_name=signal_name,
                constant=constant.to(self.signal_units).magnitude,
            )

    def apply_gaussian_noise(
        self, mean: AnyUnit, standard_deviation: AnyUnit, signal_name: str = None
    ) -> None:
        """
        Adds Gaussian noise to the specified signal.

        Parameters
        ----------
        signal_name : str
            The name of the signal to add noise to.
        std : float
            The standard deviation of the Gaussian noise.
        """
        assert (
            standard_deviation.dimensionality == self.signal_units.dimensionality
        ), f"Noise units {standard_deviation.units} do not match signal units {self.signal_units}."

        assert (
            mean.dimensionality == self.signal_units.dimensionality
        ), f"Mean units {mean.units} do not match signal units {self.signal_units}."

        if signal_name is None:
            self._cpp_apply_gaussian_noise(
                mean=mean.to(self.signal_units).magnitude,
                standard_deviation=standard_deviation.to(self.signal_units).magnitude,
            )
        else:
            self._cpp_apply_gaussian_noise_to_signal(
                signal_name=signal_name,
                mean=mean.to(self.signal_units).magnitude,
                standard_deviation=standard_deviation.to(self.signal_units).magnitude,
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

    @validate_units
    def apply_baseline_restoration(
        self, window_size: Time, signal_name: str = None
    ) -> None:
        """
        Applies baseline restoration to the specified signal.

        Parameters
        ----------
        window_size : Time
            The size of the window to use for baseline restoration.
        signal_name : str
            The name of the signal to apply baseline restoration to.
        """
        time = self._cpp_get_signal("Time")

        dt = time[1] - time[0]  # Assuming uniform time intervals

        window_size_bins = int(window_size.to(self.time_units).magnitude / dt.magnitude)

        if signal_name is None:
            self._cpp_apply_baseline_restoration(window_size=window_size_bins)
        else:
            self._cpp_apply_baseline_restoration_to_signal(
                window_size=window_size_bins, signal_name=signal_name
            )

    @validate_units
    def apply_butterworth_lowpass_filter(
        self,
        sampling_rate: Frequency,
        cutoff_frequency: Frequency,
        order: int = 1,
        gain: AnyUnit = 1.0 * ureg.dimensionless,
        signal_name: str = None,
    ) -> None:
        """
        Applies a Butterworth low-pass filter to the specified signal.

        Parameters
        ----------
        sampling_rate : Frequency
            The sampling rate of the signal.
        cutoff_frequency : Frequency
            The cutoff frequency of the filter.
        order : int, optional
            The order of the Butterworth filter, default is 1.
        gain : Dimensionless, optional
            The gain of the filter, default is 1.0.
        signal_name : str, optional
            The name of the signal to apply the filter to.
        """
        if signal_name is None:
            self._cpp_apply_butterworth_lowpass_filter(
                sampling_rate=sampling_rate.to(ureg.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(ureg.hertz).magnitude,
                order=order,
                gain=gain.magnitude,
            )
        else:
            self._cpp_apply_butterworth_lowpass_filter_to_signal(
                signal_name=signal_name,
                sampling_rate=sampling_rate.to(ureg.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(ureg.hertz).magnitude,
                order=order,
                gain=gain.magnitude,
            )

    @validate_units
    def apply_bessel_lowpass_filter(
        self,
        sampling_rate: Frequency,
        cutoff_frequency: Frequency,
        gain: AnyUnit = 1.0 * ureg.dimensionless,
        order: int = 1,
        signal_name: str = None,
    ) -> None:
        """
        Applies a Bessel low-pass filter to the specified signal.

        Parameters
        ----------
        sampling_rate : Frequency
            The sampling rate of the signal.
        cutoff_frequency : Frequency
            The cutoff frequency of the filter.
        order : int, optional
            The order of the Bessel filter, default is 1.
        gain : Dimensionless, optional
            The gain of the filter, default is 1.0.
        signal_name : str, optional
            The name of the signal to apply the filter to.
        """
        if signal_name is None:
            self._cpp_apply_bessel_lowpass_filter(
                sampling_rate=sampling_rate.to(ureg.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(ureg.hertz).magnitude,
                order=order,
                gain=gain.magnitude,
            )
        else:
            self._cpp_apply_bessel_lowpass_filter_to_signal(
                signal_name=signal_name,
                sampling_rate=sampling_rate.to(ureg.hertz).magnitude,
                cutoff_frequency=cutoff_frequency.to(ureg.hertz).magnitude,
                order=order,
                gain=gain.magnitude,
            )

    @validate_units
    def generate_pulses(
        self,
        widths: Time,
        centers: Time,
        amplitudes: AnyUnit,
        base_level: AnyUnit,
        signal_name: str = None,
    ) -> None:
        """
        Generates gaussian pulses with specified widths, centers, and amplitudes.

        Parameters
        ----------
        widths : Time
            The widths of the pulses.
        centers : Time
            The centers of the pulses.
        amplitudes : Any
            The amplitudes of the pulses.
        signal_name : str, optional
            The name of the signal to add the pulses to.
        base_level : Any
            The base level of the signal, which is added to the amplitudes of the pulses.
        """
        assert (
            amplitudes.units.dimensionality == self.signal_units.dimensionality
        ), f"Amplitude units {amplitudes.units} do not match signal units {self.signal_units}."

        if signal_name is None:
            self._cpp_generate_pulses(
                widths=widths.to(self.time_units).magnitude,
                centers=centers.to(self.time_units).magnitude,
                amplitudes=amplitudes.to(self.signal_units).magnitude,
                base_level=base_level.to(self.signal_units).magnitude,
            )
        else:
            self._cpp_generate_pulses_to_signal(
                signal_name=signal_name,
                widths=widths.to(self.time_units).magnitude,
                centers=centers.to(self.time_units).magnitude,
                amplitudes=amplitudes.to(self.signal_units).magnitude,
                base_level=base_level.to(self.signal_units).magnitude,
            )
