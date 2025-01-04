import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
import matplotlib.pyplot as plt
import pint_pandas
from abc import ABC, abstractmethod
from FlowCyPy.units import Quantity
from scipy.signal import peak_widths


class BasePeakLocator(ABC):
    """
    A base class to handle common functionality for peak detection,
    including area calculation under peaks.
    """

    peak_properties: pd.DataFrame = None

    def init_data(self, dataframe: pd.DataFrame) -> None:
        """
        Initialize signal and time data for peak detection.

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

        self.dt = self.data.Time[1] - self.data.Time[0]

    @abstractmethod
    def _compute_algorithm_specific_features(self) -> None:
        """
        Abstract method for computing features specific to the detection algorithm.
        This must be implemented by subclasses.
        """
        pass

    def detect_peaks(self, compute_area: bool = True) -> pd.DataFrame:
        """
        Detect peaks and compute peak properties.

        Parameters
        ----------
        compute_area : bool, optional
            If True, computes the area under each peak (default is True).

        Returns
        -------
        pd.DataFrame
            A DataFrame containing peak properties (times, heights, widths, etc.).
        """
        peak_indices, widths_samples, width_heights, left_ips, right_ips = self._compute_algorithm_specific_features()

        peak_times = self.data['Time'].values[peak_indices]
        heights = self.data['Signal'].values[peak_indices]
        widths = widths_samples * self.dt

        # Store results in `peak_properties`
        self.peak_properties = pd.DataFrame({
            'PeakTimes': peak_times,
            'Heights': heights,
            'Widths': pint_pandas.PintArray(widths, dtype=widths.units),
            'WidthHeights': pint_pandas.PintArray(width_heights, dtype=heights.units),
            'LeftIPs': pint_pandas.PintArray(left_ips * self.dt, dtype=self.dt.units),
            'RightIPs': pint_pandas.PintArray(right_ips * self.dt, dtype=self.dt.units),
        })

        # Compute areas if needed
        if compute_area:
            self._compute_peak_areas()

        return self.peak_properties

    def _compute_peak_areas(self) -> None:
        """
        Computes the areas under the detected peaks using cumulative integration.

        The cumulative integral of the signal is interpolated at the left and right
        interpolated positions of each peak to compute the enclosed area.

        Adds an 'Areas' column to `self.peak_properties`.

        Raises
        ------
        RuntimeError
            If `peak_properties` or `data` has not been initialized.
        """
        if not hasattr(self, 'peak_properties') or self.peak_properties.empty:
            raise RuntimeError("No peaks detected. Run `detect_peaks()` first.")

        if not hasattr(self, 'data') or self.data.empty:
            raise RuntimeError("Signal data is not initialized. Call `init_data()` first.")

        # Compute cumulative integral of the signal
        cumulative = cumulative_trapezoid(
            self.data.Signal.values.quantity.magnitude,
            x=self.data.Time.values.quantity.magnitude,
            initial=0  # Include 0 at the start
        )

        # Interpolate cumulative integral at left and right interpolated positions
        left_cum_integral = np.interp(
            x=self.peak_properties.LeftIPs,
            xp=self.data.index,
            fp=cumulative
        )
        right_cum_integral = np.interp(
            x=self.peak_properties.RightIPs,
            xp=self.data.index,
            fp=cumulative
        )

        # Compute areas under peaks
        areas = right_cum_integral - left_cum_integral

        # Add areas with units to peak properties
        self.peak_properties['Areas'] = pint_pandas.PintArray(
            areas, dtype=self.data.Signal.pint.units * self.data.Time.pint.units
        )

    def _add_to_ax(self, time_unit: str | Quantity, signal_unit: str | Quantity, ax: plt.Axes = None) -> None:
        """
        Plots the signal with detected peaks and FWHM lines.

        Parameters
        ----------
        time_unit : str or Quantity
            Unit for the time axis (e.g., 'microsecond').
        signal_unit : str or Quantity
            Unit for the signal axis (e.g., 'volt').
        ax : plt.Axes
            The matplotlib Axes to plot on. Creates a new figure if not provided.
        """
        # Plot vertical lines at peak times
        for _, row in self.peak_properties.iterrows():
            ax.axvline(row['PeakTimes'].to(time_unit), color='black', linestyle='-', lw=0.8)

        self._add_custom_to_ax(ax=ax, time_unit=time_unit, signal_unit=signal_unit)

    def _compute_peak_widths(self, peak_indices: list[int], values: np.ndarray) -> None:
        # Compute peak properties
        widths_samples, width_heights, left_ips, right_ips = peak_widths(
            x=values,
            peaks=peak_indices,
            rel_height=self.rel_height
        )

        return widths_samples, width_heights, left_ips, right_ips
