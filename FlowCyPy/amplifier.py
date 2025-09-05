import numpy as np
from pydantic.dataclasses import dataclass
from TypedUnit import AnyUnit, Frequency, Ohm, ureg, validate_units

from FlowCyPy.simulation_settings import SimulationSettings

config_dict = dict(
    arbitrary_types_allowed=True, kw_only=True, slots=True, extra="forbid"
)


@dataclass(config=config_dict)
class TransimpedanceAmplifier:
    """
    Represents a transimpedance amplifier (TIA) used to convert photocurrent signals into voltage.

    This model simulates a TIA with a specified gain and bandwidth while incorporating
    input-referred noise sources. Both voltage (thermal) noise and current noise are modeled
    to account for the effects these factors have on the overall signal-to-noise ratio in
    photodetection systems, particularly in low-light or high-sensitivity applications.

    Parameters
    ----------
    gain : Quantity
        The amplifier gain in ohms (Ω), which sets the conversion factor from photocurrent
        to voltage. Typical values range from 1e3 Ω to 1e7 Ω, depending on the detector type
        (e.g., photomultiplier tubes or photodiodes).
    bandwidth : Quantity
        The -3 dB bandwidth of the amplifier in Hertz (Hz). This defines the frequency
        range over which the amplifier effectively converts current to voltage.
    voltage_noise_density : Quantity
        The input-referred voltage noise spectral density (in V/√Hz). Typical values are
        in the range of 1 nV/√Hz to 10 nV/√Hz.
    current_noise_density : Quantity
        The input-referred current noise spectral density (in A/√Hz). Typical values are
        on the order of 2 fA/√Hz to 20 fA/√Hz.

    Attributes
    ----------
    gain : Ohm
        The amplifier gain (Ω) used to convert photocurrent into voltage.
    bandwidth : Frequency/
        The -3 dB frequency bandwidth (Hz) of the amplifier.
    voltage_noise_density : AnyUnit
        The spectral density of voltage noise at the amplifier input (V/√Hz).
    current_noise_density : AnyUnit
        The spectral density of current noise at the amplifier input (A/√Hz).

    Notes
    -----
    In applications such as flow cytometry or low-light detection, the noise characteristics
    of the TIA play a crucial role in determining the overall sensitivity and performance
    of the detection system. This model allows simulation of how the gain and noise parameters
    affect the output voltage and the signal-to-noise ratio.
    """

    gain: Ohm
    bandwidth: Frequency
    voltage_noise_density: AnyUnit = 0 * ureg.volt / ureg.sqrt_hertz
    current_noise_density: AnyUnit = 0 * ureg.ampere / ureg.sqrt_hertz

    @property
    def voltage_rms_noise(self) -> AnyUnit:
        """
        Total RMS voltage noise introduced by the amplifier over its bandwidth.
        """
        return self.voltage_noise_density * np.sqrt(self.bandwidth)

    @property
    def current_rms_noise(self) -> AnyUnit:
        """
        Total RMS current noise (converted to voltage via gain).
        """
        return self.current_noise_density * np.sqrt(self.bandwidth) * self.gain

    @property
    def total_output_noise(self) -> AnyUnit:
        """
        Total RMS output noise (in volts) from both voltage and current contributions.
        """
        v_rms = self.voltage_rms_noise
        i_rms = self.current_rms_noise
        return np.sqrt(v_rms**2 + i_rms**2)

    @validate_units
    def amplify(self, signal_generator: object, sampling_rate: Frequency):
        """
        Amplifies the input signal from a detector using the transimpedance amplifier's gain.
        The noise is added after the amplification.

        Parameters
        ----------
        signal_generator : object
            An instance of a signal generator that provides the input signal to be amplified.
        sampling_rate : Frequency
            The sampling rate of the signal generator, used for filtering and noise calculations.
        Raises
        ------
        ValueError
            If the signal  generator does not have a method to get the signal for the specified detector.

        Notes
        -----
        This method retrieves the signal from the specified detector, applies the amplifier's gain,
        and adds noise if enabled in the SimulationSettings. It also applies a low-pass Butterworth filter
        to the amplified signal if a bandwidth is specified. The filter is applied using the
        `apply_butterworth_lowpass_filter_to_signal` method of the signal generator.
        """
        if (
            self.bandwidth is None
            or SimulationSettings.assume_amplifier_bandwidth_is_infinite
        ):
            signal_generator.multiply(factor=self.gain)
        else:
            signal_generator.apply_butterworth_lowpass_filter(
                gain=self.gain,
                sampling_rate=sampling_rate,
                cutoff_frequency=self.bandwidth,
                order=1,
            )

        # Add voltage related noise if enabled
        if (
            SimulationSettings.include_amplifier_noise
            and SimulationSettings.include_noises
        ):
            signal_generator.apply_gaussian_noise(
                mean=0.0 * self.total_output_noise.units,
                standard_deviation=self.total_output_noise,
            )
