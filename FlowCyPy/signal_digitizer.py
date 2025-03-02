from pydantic.dataclasses import dataclass
from pydantic import field_validator
from typing import Union, Tuple
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
class SignalDigitizer:
    """
    Handles signal digitization and saturation for a detector.

    Attributes
    ----------
    sampling_rate : Quantity
        The sampling frequency of the detector in hertz.
    bit_depth : Union[int, str]
        The number of discretization bins or bit-depth (e.g., '12bit').
    saturation_levels : Union[str, Tuple[Quantity, Quantity]]
        A tuple defining the lower and upper bounds for saturation, or 'auto' to set bounds dynamically.
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

        self._saturation_levels = min_level, max_level
        # Generate bins for discretization
        bins = np.linspace(
            min_level.to(signal.pint.units).magnitude,
            max_level.to(signal.pint.units).magnitude,
            self._bit_depth
        )

        digitized_signal = np.digitize(signal.pint.magnitude, bins, right=True)

        self.is_saturated = np.any((signal < min_level) | (signal > max_level))

        # Throw a warning if saturated
        if self.is_saturated:
            logging.info("Signal values have been clipped to the saturation boundaries.")

        return digitized_signal, (min_level, max_level)