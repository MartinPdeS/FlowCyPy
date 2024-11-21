from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
from FlowCyPy.peak_locator.base_class import BasePeakLocator
import pandas as pd
import pint_pandas

from FlowCyPy.units import Quantity, volt, microsecond
PT_ = pint_pandas.PintType


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
    window_size: Quantity = Quantity(5, microsecond)
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
        if not {'Signal', 'Time'}.issubset(dataframe.columns):
            raise ValueError("The DataFrame must contain 'Signal' and 'Time' columns.")

        if dataframe.empty:
            raise ValueError("The DataFrame is empty. Please provide valid signal data.")

        self.data = pd.DataFrame(index=np.arange(len(dataframe)))
        self.data['Signal'] = dataframe['Signal']
        self.data['Time'] = dataframe['Time']
        self.peak_properties = pd.DataFrame()

        if self.threshold is not None:
            self.threshold = self.threshold.to(self.data['Signal'].values.units)

        self.window_size = self.window_size.to(self.data['Time'].values.units)

        if self.min_peak_distance is not None:
            self.min_peak_distance = self.min_peak_distance.to(self.data['Time'].values.units)

        self.dt = self.data.Time[1] - self.data.Time[0]

    def compute_moving_average(self) -> None:
        """
        Compute the moving average of the signal and calculate the difference.
        """
        window_size_samples = int(np.ceil(self.window_size / self.dt))

        moving_avrg = self.data['Signal'].rolling(window=window_size_samples, center=True, min_periods=1).mean()

        self.data['MovingAverage'] = pint_pandas.PintArray(moving_avrg, dtype=self.data['Signal'].values.units)
        self.data['Difference'] = self.data['Signal'] - self.data['MovingAverage']

    def detect_peaks(self, compute_area: bool = True) -> pd.DataFrame:
        """
        Detects peaks in the signal using a moving average and a threshold.

        Parameters
        ----------
        detector : Detector
            The detector which owns the signal data.
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
        self.compute_moving_average()

        # Find peaks in the difference signal
        peak_indices, _ = find_peaks(
            self.data['Difference'].values.quantity.magnitude,
            height=None if self.threshold is None else self.threshold.magnitude,
            distance=None if self.min_peak_distance is None else int(np.ceil(self.min_peak_distance / self.dt))
        )

        # Calculate peak properties
        widths_samples, width_heights, left_ips, right_ips = peak_widths(
            x=self.data['Difference'].values,
            peaks=peak_indices,
            rel_height=self.rel_height
        )

        # Convert widths from samples to time units
        widths = widths_samples * self.dt
        peak_times = self.data['Time'].values[peak_indices]
        heights = self.data['Signal'].values[peak_indices]

        self.peak_properties = pd.DataFrame({
            'PeakTimes': peak_times,
            'Heights': heights,
            'Widths': pint_pandas.PintArray(widths, dtype=widths.units),
            'WidthHeights': pint_pandas.PintArray(width_heights, dtype=volt),
            'LeftIPs': pint_pandas.PintArray(left_ips * self.dt, dtype=self.dt.units),
            'RightIPs': pint_pandas.PintArray(right_ips * self.dt, dtype=self.dt.units),
        })

        # Compute areas under peaks
        if compute_area:
            self._compute_peak_areas()

    def _add_to_ax(self, time_unit: str | Quantity, signal_unit: str | Quantity, ax: plt.Axes) -> None:
        """
        Plots the signal data from the detector, including peaks, moving average, and signal differences.
        Optionally, this method can also display the plot.

        Parameters:
        -----------
        detector : object
            The detector object containing the signal data and peak properties.
            It should have a 'dataframe' attribute for the signal data and 'peak_properties' for peak information.
        ax : matplotlib.axes.Axes, optional
            A matplotlib Axes object to plot the graph. If not provided, a new one will be created.
        show : bool, optional, default=True
            Whether to display the plot after creating it.

        """
        ax.plot(
            self.data.Time,
            self.data.Difference,
            linestyle='--',
            color='C1',
            label='MA-difference'
        )

        # Plot vertical lines at peak times
        for _, row in self.peak_properties.iterrows():
            ax.axvline(row['PeakTimes'].to(time_unit), color='black', linestyle='-', lw=0.8)

        # Plot the signal threshold line
        ax.axhline(y=self.threshold.to(signal_unit).magnitude, color='black', linestyle='--', label='Threshold', lw=1)
