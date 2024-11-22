from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from FlowCyPy.peak_locator.base_class import BasePeakLocator
import pandas as pd
import pint_pandas
from FlowCyPy.units import Quantity, microsecond


@dataclass
class MovingAverage(BasePeakLocator):
    """
    Detects peaks in a signal using a moving average algorithm.
    A peak is identified when the signal exceeds the moving average by a defined threshold.

    Parameters
    ----------
    threshold : Quantity, optional
        The minimum difference between the signal and its moving average required to detect a peak. Default is `Quantity(0.2)`.
    window_size : Quantity, optional
        The window size for calculating the moving average. Default is `Quantity(500)`.
    min_peak_distance : Quantity, optional
        The minimum distance between detected peaks. Default is `Quantity(0.1)`.
    rel_height : float, optional
        The relative height at which the peak width is measured. Default is `0.5` (half-height).

    """

    threshold: Quantity = None
    window_size: Quantity = Quantity(1, microsecond)
    min_peak_distance: Quantity = None
    rel_height: float = 0.8

    def init_data(self, dataframe: pd.DataFrame) -> None:
        """
        Initialize the data for peak detection.

        Parameters
        ----------
        dataframe : pd.DataFrame
            A DataFrame containing the signal data with columns 'Signal' and 'Time'.

        Raises
        ------
        ValueError
            If the DataFrame is missing required columns or is empty.
        """
        super().init_data(dataframe)

        if self.threshold is not None:
            self.threshold = self.threshold.to(self.data['Signal'].values.units)

        self.window_size = self.window_size.to(self.data['Time'].values.units)

        if self.min_peak_distance is not None:
            self.min_peak_distance = self.min_peak_distance.to(self.data['Time'].values.units)

    def _compute_algorithm_specific_features(self) -> None:
        """
        Compute peaks based on the moving average algorithm.
        """
        peak_indices = self._compute_peak_positions()

        widths_samples, width_heights, left_ips, right_ips = self._compute_peak_widths(peak_indices, self.data['Difference'].values)

        return peak_indices, widths_samples, width_heights, left_ips, right_ips

    def _compute_peak_positions(self) -> None:
        # Calculate moving average
        window_size_samples = int(np.ceil(self.window_size / self.dt))
        moving_avg = self.data['Signal'].rolling(window=window_size_samples, center=True, min_periods=1).mean()

        # Reattach Pint units to the moving average
        moving_avg = pint_pandas.PintArray(moving_avg, dtype=self.data['Signal'].values.units)

        # Add the moving average to the DataFrame
        self.data['MovingAverage'] = moving_avg

        # Compute the difference signal
        self.data['Difference'] = self.data['Signal'] - self.data['MovingAverage']

        # Detect peaks
        peak_indices, _ = find_peaks(
            self.data['Difference'].values.quantity.magnitude,
            height=None if self.threshold is None else self.threshold.magnitude,
            distance=None if self.min_peak_distance is None else int(np.ceil(self.min_peak_distance / self.dt))
        )

        return peak_indices

    def _add_custom_to_ax(self, time_unit: str | Quantity, signal_unit: str | Quantity, ax: plt.Axes) -> None:
        """
        Add algorithm-specific elements to the plot.

        Parameters
        ----------
        time_unit : str or Quantity
            The unit for the time axis (e.g., 'microsecond').
        signal_unit : str or Quantity
            The unit for the signal axis (e.g., 'volt').
        ax : matplotlib.axes.Axes
            The Axes object to add elements to.
        """
        ax.plot(
            self.data.Time,
            self.data.Difference,
            linestyle='--',
            color='C1',
            label='MA-difference'
        )

        # Plot the signal threshold line
        ax.axhline(y=self.threshold.to(signal_unit).magnitude, color='black', linestyle='--', label='Threshold', lw=1)
