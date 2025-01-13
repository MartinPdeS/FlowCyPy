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

    def __post_init__(self):
        """
        Validates and processes the bit_depth attribute.
        """
        self.bit_depth = self._process_bit_depth(self.bit_depth)

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

    def _compute_bounds(self, signal: Quantity) -> Tuple[Quantity, Quantity]:
        """
        Computes the min and max boundaries for saturation when 'auto' is enabled.

        Parameters
        ----------
        signal : Quantity
            The input signal to determine the bounds from.

        Returns
        -------
        Tuple[Quantity, Quantity]
            The dynamically computed min and max boundaries.
        """
        return signal.min(), signal.max()

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

    def _validate_bounds(self, bounds: Tuple[Quantity, Quantity]) -> Tuple[Quantity, Quantity]:
        """
        Validates that the lower boundary is less than the upper boundary.

        Parameters
        ----------
        bounds : Tuple[Quantity, Quantity]
            The saturation bounds to validate.

        Returns
        -------
        Tuple[Quantity, Quantity]
            The validated bounds.

        Raises
        ------
        ValueError
            If the bounds are invalid (e.g., min >= max).
        """
        min_level, max_level = bounds
        if min_level >= max_level:
            raise ValueError(f"Invalid bounds: min_level ({min_level}) must be less than max_level ({max_level}).")
        return min_level, max_level

    def discretize_signal(self, signal: Quantity) -> Quantity:
        """
        Applies saturation and discretization to the signal.

        Parameters
        ----------
        signal : Quantity
            The signal to be discretized, in volts.

        Returns
        -------
        Quantity
            The digitized signal.
        """
        # Determine bounds
        if self.saturation_levels == 'auto':
            min_level, max_level = self._compute_bounds(signal)
        elif isinstance(self.saturation_levels, Quantity):
            # If only max_level is provided, assume min_level is 0 volt
            min_level = Quantity(0, volt)
            max_level = self.saturation_levels
        elif isinstance(self.saturation_levels, tuple) and len(self.saturation_levels) == 2:
            # Use provided min_level and max_level
            min_level, max_level = self._validate_bounds(self.saturation_levels)
        else:
            raise ValueError("saturation_levels must be 'auto', a single Quantity, or a tuple of two Quantities.")

        # Generate bins for discretization
        bins = np.linspace(
            min_level.to(signal.pint.units).magnitude,
            max_level.to(signal.pint.units).magnitude,
            self.bit_depth
        )
        self.digitization_ratio = abs(max_level - min_level) / self.bit_depth
        # Digitize the signal
        digitized = np.digitize(signal.pint.magnitude, bins, right=True)

        # Check if the signal is saturated
        is_saturated = np.any((signal < min_level) | (signal > max_level))

        # Throw a warning if saturated
        if is_saturated:
            logging.info("Signal values have been clipped to the saturation boundaries.")


        return digitized, is_saturated
