from pydantic.dataclasses import dataclass
from pydantic import field_validator
from typing import Union, Tuple
import logging
import numpy as np
from FlowCyPy.units import Quantity, volt

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
    sampling_freq : Quantity
        The sampling frequency of the detector in hertz.
    bit_depth : Union[int, str]
        The number of discretization bins or bit-depth (e.g., '12bit').
    saturation_levels : Union[str, Tuple[Quantity, Quantity]]
        A tuple defining the lower and upper bounds for saturation, or 'auto' to set bounds dynamically.
    """
    sampling_freq: Quantity
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
        return self.sampling_freq / 2

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

    @field_validator('sampling_freq')
    def _validate_sampling_freq(cls, value):
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
            raise ValueError(f"sampling_freq must be in hertz, but got {value.units}")
        return value
