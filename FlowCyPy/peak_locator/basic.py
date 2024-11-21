from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, peak_widths
from FlowCyPy.peak_locator.base_class import BasePeakLocator
from FlowCyPy.units import Quantity, volt
import pint_pandas


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
        if not {'Signal', 'Time'}.issubset(dataframe.columns):
            raise ValueError("The DataFrame must contain 'Signal' and 'Time' columns.")

        if dataframe.empty:
            raise ValueError("The DataFrame is empty. Please provide valid signal data.")

        self.data = pd.DataFrame(index=np.arange(len(dataframe)))
        self.data['Signal'] = dataframe['Signal']
        self.data['Time'] = dataframe['Time']

        if self.threshold is not None:
            self.threshold = self.threshold.to(self.data['Signal'].values.units)

        if self.min_peak_distance is not None:
            self.min_peak_distance = self.min_peak_distance.to(self.data['Time'].values.units)

        self.dt = self.data.Time[1] - self.data.Time[0]

    def detect_peaks(self, compute_area: bool = True) -> pd.DataFrame:
        """
        Detects peaks in the signal and calculates their properties such as heights, widths, and areas.

        Parameters
        ----------
        detector : pd.DataFrame
            DataFrame with the signal data to detect peaks in.
        compute_area : bool, optional
            If True, computes the area under each peak. Default is True.

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

        # Calculate peak properties
        widths_samples, width_heights, left_ips, right_ips = peak_widths(
            x=self.data['Signal'].values,
            peaks=peak_indices,
            rel_height=self.rel_height
        )

        # Convert widths from samples to time units
        widths = widths_samples * self.dt
        peak_times = self.data['Time'].values[peak_indices]
        heights = self.data['Signal'].values[peak_indices]

        self.peak_properties = pd.DataFrame({
            'PeakTimes': pint_pandas.PintArray(peak_times, dtype=peak_times.units),
            'Heights': pint_pandas.PintArray(heights, dtype=volt),
            'Widths': pint_pandas.PintArray(widths, dtype=widths.units),
            'WidthHeights': pint_pandas.PintArray(width_heights, dtype=volt),
            'LeftIPs': pint_pandas.PintArray(left_ips * self.dt, dtype=self.dt.units),
            'RightIPs': pint_pandas.PintArray(right_ips * self.dt, dtype=self.dt.units),
        })

        # Compute areas under peaks
        if compute_area:
            self._compute_peak_areas()

    def _add_to_ax(self, time_unit: str | Quantity, signal_unit: str | Quantity, ax: plt.Axes = None) -> None:
        """
        Plots the signal with detected peaks and FWHM lines.

        Parameters
        ----------
        detector : pd.DataFrame
            The detector object containing the data to plot.
        ax : plt.Axes, optional
            The matplotlib Axes to plot on. If not provided, a new figure is created.
        show : bool, optional
            Whether to display the plot immediately. Default is True.
        """
        # Plot vertical lines at peak times
        for _, row in self.peak_properties.iterrows():
            ax.axvline(row['PeakTimes'].to(time_unit), color='black', linestyle='-', lw=0.8)
