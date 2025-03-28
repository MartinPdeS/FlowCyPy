from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy import units
import numpy as np
from FlowCyPy.noises import NoiseSetting

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

    # voltage_noise_density: units.Quantity = 5e-9 * (1 * units.volt / units.sqrt_hertz)
    # current_noise_density: units.Quantity = 2e-12 * (1 * units.ampere / units.sqrt_hertz)

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

    def amplify(self, current_signal: units.Quantity) -> units.Quantity:
        """
        Converts photocurrent to voltage via transimpedance gain.

        Parameters
        ----------
        current_signal : units.Quantity
            The input photocurrent to amplify (in Amperes).

        Returns
        -------
        units.Quantity
            The amplified voltage signal.
        """
        if not current_signal.check('A'):
            raise ValueError(f"Signal must be in Amperes, got {current_signal.units}")


        if not NoiseSetting.include_amplifier_noise or not NoiseSetting.include_noises:
            return current_signal * self.gain

        voltage_signal = current_signal * self.gain

        amp_noise_std = self.total_output_noise.to('volt').magnitude

        # Generate random amplifier noise (Gaussian distributed) with the same shape as voltage_signal
        amp_noise = np.random.normal(loc=0.0, scale=amp_noise_std, size=voltage_signal.shape) * units.volt

        return voltage_signal + amp_noise
