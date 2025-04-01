from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy import units
import numpy as np
from FlowCyPy.noises import NoiseSetting
from FlowCyPy.helper import validate_units
import numpy.fft as fft  # Using numpy's FFT routines

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)

@dataclass(config=config_dict)
class TransimpedanceAmplifier:
    """
    Models a transimpedance amplifier (TIA) that converts photocurrent to voltage
    and introduces thermal and voltage noise based on gain and bandwidth.

    Attributes
    ----------
    gain : units.Quantity
        Amplifier gain (Ohms), typically 10^3-10^7 Ohm for PMTs or photodiodes.
    bandwidth : units.Quantity
        -3dB bandwidth of the amplifier, usually in Hz.
    voltage_noise_density : units.Quantity
        Input-referred voltage noise spectral density (V/√Hz).
    current_noise_density : units.Quantity
        Input-referred current noise spectral density (A/√Hz).
    """
    gain: units.Quantity
    bandwidth: units.Quantity
    voltage_noise_density: units.Quantity = 0 * units.volt / units.sqrt_hertz
    current_noise_density: units.Quantity = 0 * units.ampere / units.sqrt_hertz

    @field_validator('gain')
    def _validate_gain(cls, value):
        if not value.check('ohm'):
            raise ValueError(f"gain must be in ohms, got {value.units}")
        return value

    @field_validator('bandwidth')
    def _validate_bandwidth(cls, value):
        if not value.check('Hz'):
            raise ValueError(f"bandwidth must be in Hz, got {value.units}")
        return value

    @property
    def voltage_rms_noise(self) -> units.Quantity:
        """
        Total RMS voltage noise introduced by the amplifier over its bandwidth.
        """
        return self.voltage_noise_density * np.sqrt(self.bandwidth)

    @property
    def current_rms_noise(self) -> units.Quantity:
        """
        Total RMS current noise (converted to voltage via gain).
        """
        return self.current_noise_density * np.sqrt(self.bandwidth) * self.gain

    @property
    def total_output_noise(self) -> units.Quantity:
        """
        Total RMS output noise (in volts) from both voltage and current contributions.
        """
        v_rms = self.voltage_rms_noise
        i_rms = self.current_rms_noise
        return np.sqrt(v_rms**2 + i_rms**2)

    @validate_units(signal=units.ampere, dt=units.second)
    def amplify(self, signal: units.Quantity, dt: units.Quantity) -> units.Quantity:
        """
        Converts photocurrent to voltage via transimpedance gain,
        adds noise, and applies an FFT-based low-pass filter to simulate
        the finite bandwidth of the amplifier.

        Parameters
        ----------
        signal : units.Quantity
            The input photocurrent to amplify (in Amperes).
        dt : float
            The time step (in seconds) between consecutive samples in the signal.

        Returns
        -------
        units.Quantity
            The amplified and filtered voltage signal.
        """
        # Convert current to voltage via the amplifier gain
        voltage_signal = signal * self.gain

        # Add noise if enabled
        if NoiseSetting.include_amplifier_noise and NoiseSetting.include_noises:
            amp_noise_std = self.total_output_noise.to('volt').magnitude
            # Generate random amplifier noise (Gaussian distributed) with the same shape as voltage_signal
            amp_noise = np.random.normal(loc=0.0, scale=amp_noise_std, size=voltage_signal.shape) * units.volt
            amplified_signal = voltage_signal + amp_noise
        else:
            amplified_signal = voltage_signal

        if self.bandwidth is not None:
            return self._apply_bandwidth(signal=amplified_signal, dt=dt)

        return amplified_signal


    def _apply_bandwidth(self, signal: units.Quantity, dt: units.Quantity) -> units.Quantity:
        # --- FFT-based filtering ---
        # Remove units for FFT processing (voltage_signal is in volts)
        signal_magnitude = signal.magnitude
        N = len(signal_magnitude)

        # Compute the FFT of the signal
        signal_fft = fft.fft(signal_magnitude)
        # Create frequency bins (in Hz)
        freqs = fft.fftfreq(N, d=dt.to('second').magnitude)

        # Define the filter's cutoff frequency (bandwidth)
        fc = self.bandwidth.to("Hz").magnitude

        # Build the frequency response of a first-order low-pass filter:
        # H(f) = 1/sqrt(1 + (f/fc)^2)
        H = 1 / np.sqrt(1 + (freqs / fc)**2)

        # Apply the filter in the frequency domain
        filtered_fft = signal_fft * H

        # Inverse FFT to convert back to the time domain and take the real part
        filtered_signal = np.real(fft.ifft(filtered_fft))

        # Reapply the units (volts)
        return filtered_signal * signal.units
