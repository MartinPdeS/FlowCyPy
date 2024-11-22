from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from FlowCyPy.peak_locator.base_class import BasePeakLocator
from FlowCyPy.units import Quantity, volt


@dataclass
class BasicPeakLocator(BasePeakLocator):
    """
    A basic peak detector class that identifies peaks in a signal using a threshold-based method.

    Parameters
    ----------
    threshold : Quantity, optional
        The minimum height required for a peak to be considered significant. Default is `Quantity(0.1, volt)`.
    min_peak_distance : Quantity, optional
        The minimum distance between detected peaks. Default is `Quantity(0.1)`.
    rel_height : float, optional
        The relative height at which the peak width is measured. Default is `0.5`.

    """

    threshold: Quantity = Quantity(0.0, volt)
    rel_height: float = 0.5
    min_peak_distance: Quantity = None

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

        if self.min_peak_distance is not None:
            self.min_peak_distance = self.min_peak_distance.to(self.data['Time'].values.units)

    def _compute_algorithm_specific_features(self) -> None:
        """
        Compute peaks based on the moving average algorithm.
        """
        peak_indices = self._compute_peak_positions()

        widths_samples, width_heights, left_ips, right_ips = self._compute_peak_widths(
            peak_indices,
            self.data['Signal'].values
        )

        return peak_indices, widths_samples, width_heights, left_ips, right_ips

    def _compute_peak_positions(self) -> pd.DataFrame:
        """
        Detects peaks in the signal and calculates their properties such as heights, widths, and areas.

        Parameters
        ----------
        detector : pd.DataFrame
            DataFrame with the signal data to detect peaks in.

        Returns
        -------
        peak_times : Quantity
            The times at which peaks occur.
        heights : Quantity
            The heights of the detected peaks.
        widths : Quantity
            The widths of the detected peaks.
        areas : Quantity or None
            The areas under each peak, if `compute_area` is True.
        """
        # Find peaks in the difference signal
        peak_indices, _ = find_peaks(
            self.data['Signal'].values,
            height=None if self.threshold is None else self.threshold.magnitude,
            distance=None if self.min_peak_distance is None else int(np.ceil(self.min_peak_distance / self.dt))
        )

        return peak_indices

    def _add_custom_to_ax(self, time_unit: str | Quantity, signal_unit: str | Quantity, ax: plt.Axes = None) -> None:
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
        # Plot the signal threshold line
        ax.axhline(y=self.threshold.to(signal_unit).magnitude, color='black', linestyle='--', label='Threshold', lw=1)
