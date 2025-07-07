from pydantic.dataclasses import dataclass
from pydantic import field_validator
from typing import Union, Tuple
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.units import Quantity
import pandas as pd
import numpy as np
import logging

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)

@dataclass(config=config_dict)
class Digitizer:
    """
    Simulates the digitization and saturation process for detector signals.

    This class models the conversion of continuous (analog) detector signals into discrete
    digital values, accounting for the sampling rate and bit-depth of the digitizer. It also
    handles saturation effects by limiting the signal within defined bounds, which is critical
    for preventing unrealistic values when the input signal exceeds the device's dynamic range.

    Parameters
    ----------
    sampling_rate : Quantity
        The sampling frequency of the digitizer in hertz (Hz), defining how frequently the
        analog signal is sampled.
    bit_depth : Union[int, str]
        The number of quantization levels for the digitizer. This can be provided either as an
        integer (e.g., 12) or as a descriptive string (e.g., '12bit').
    saturation_levels : Union[str, Tuple[Quantity, Quantity]]
        The saturation limits for the digitizer. This can be specified as a tuple containing
        the lower and upper bounds (each a Quantity with appropriate units), or as 'auto' to allow
        the digitizer to set these bounds dynamically based on the signal characteristics.

    Attributes
    ----------
    sampling_rate : Quantity
        The digitizer's sampling rate in Hz.
    bit_depth : Union[int, str]
        The bit-depth or the number of discrete levels available for digitizing the analog signal.
    saturation_levels : Union[str, Tuple[Quantity, Quantity]]
        The defined saturation range as a tuple (lower bound, upper bound) or 'auto' if the limits
        are determined dynamically.

    Notes
    -----
    Accurate digitization is essential for faithfully representing the detector's output, while
    proper handling of saturation prevents clipping of the signal when it exceeds the digitizer's
    dynamic range. This class provides the flexibility to configure both the sampling resolution
    and saturation behavior for simulation purposes.
    """
    sampling_rate: Quantity
    bit_depth: Union[int, str] = '10bit'
    saturation_levels: Union[str, Tuple[Quantity, Quantity], Quantity] = 'auto'

    @property
    def _bit_depth(self) -> int:
        return self._process_bit_depth(self.bit_depth)

    @property
    def bandwidth(self) -> Quantity:
        """
        Automatically calculates the bandwidth based on the sampling frequency.

        Returns
        -------
        Quantity
            The bandwidth of the detector, which is half the sampling frequency (Nyquist limit).
        """
        return self.sampling_rate / 2

    @staticmethod
    def _process_bit_depth(bit_depth: Union[int, str]) -> int:
        """
        Converts bit-depth to the number of bins.

        Parameters
        ----------
        bit_depth : Union[int, str]
            The bit-depth as an integer or a string (e.g., '10bit').

        Returns
        -------
        int
            The number of bins corresponding to the bit-depth.
        """
        if isinstance(bit_depth, str):
            bit_depth = int(bit_depth.rstrip('bit'))
            bit_depth = 2 ** bit_depth

        return bit_depth

    @field_validator('sampling_rate')
    def _validate_sampling_rate(cls, value):
        """
        Validates that the sampling frequency is provided in hertz.

        Parameters
        ----------
        value : Quantity
            The sampling frequency to validate.

        Returns
        -------
        Quantity
            The validated sampling frequency.

        Raises:
            ValueError: If the sampling frequency is not in hertz.
        """
        if not value.check('Hz'):
            raise ValueError(f"sampling_rate must be in hertz, but got {value.units}")
        return value

    def get_time_series(self, run_time: Quantity) -> Quantity:
        time_points = int(self.sampling_rate * run_time)

        time_series = np.linspace(0, run_time.magnitude, time_points) * run_time.units

        return time_series

    def get_saturation_values(self, signal: pd.Series) -> Tuple[Quantity, Quantity]:
        if self.saturation_levels == 'auto':
            return signal.pint.quantity.min(), signal.pint.quantity.max()
        elif isinstance(self.saturation_levels, tuple) and len(self.saturation_levels) == 2:
            return self.saturation_levels

        raise ValueError("saturation_levels must be 'auto' or a tuple of two Quantities.")

    def capture_signal(self, signal: pd.Series) -> Tuple[Quantity, Quantity, Quantity]:
        """
        Processes and captures the final signal by applying noise and saturation.
        """
        min_level, max_level = self.get_saturation_values(signal)

        if SimulationSettings.assume_perfect_digitizer:
            signal = np.clip(
                a=signal.pint.quantity.magnitude,
                a_min=min_level.to(signal.pint.units).magnitude,
                a_max=max_level.to(signal.pint.units).magnitude
            )

            # If the digitizer is assumed to be perfect, return the signal without processing
            return signal, (min_level, max_level)

        assert signal.pint.check(min_level.units), f"Signal units: {signal.pint.units} do not match the saturation level units: {min_level.units}"

        self._saturation_levels = min_level, max_level
        # Generate bins for discretization
        bins = np.linspace(
            min_level.to(signal.pint.units).magnitude,
            max_level.to(signal.pint.units).magnitude,
            self._bit_depth
        )

        digitized_signal = np.digitize(signal.pint.magnitude, bins, right=True).astype(float)

        # Throw a warning if saturated
        if np.any((signal < min_level) | (signal > max_level)):
            logging.info("Signal values have been clipped to the saturation boundaries.")

        return digitized_signal, (min_level, max_level)