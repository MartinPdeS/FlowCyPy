from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks, peak_widths
from FlowCyPy.detector import Detector
from FlowCyPy.peak_finder.base_class import BaseClass
from FlowCyPy.units import Quantity, volt
import pint_pandas


@dataclass
class Basic(BaseClass):
    """
    A basic peak detector class that identifies peaks in a signal using a threshold-based method.

    Parameters
    ----------
    height_threshold : Quantity, optional
        The minimum height required for a peak to be considered significant.
        Default is `Quantity(0.1, volt)`.
    rel_height : float, optional
        The relative height at which the peak width is measured. Default is `0.5`.

    """

    height_threshold: Quantity = Quantity(0.0, volt)
    rel_height: float = 0.5

    def detect_peaks(self, detector: Detector, compute_area: bool = True) -> None:
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
        # Ensure signal and time are from the DataFrame
        signal = detector.dataframe['Signal'].values
        time = detector.dataframe.Time.values

        self.height_threshold = self.height_threshold.to(signal.units)

        # Find peaks in the signal using the height threshold
        peak_indices, _ = find_peaks(signal, height=self.height_threshold.magnitude)

        # Calculate peak properties
        widths_samples, width_heights, left_ips, right_ips = peak_widths(signal, peak_indices, rel_height=self.rel_height)
        dt = time[1] - time[0]
        widths = widths_samples * dt

        detector.peak_properties = pd.DataFrame({
            'PeakTimes': detector.dataframe.Time[peak_indices].values,
            'Heights': detector.dataframe.Signal[peak_indices].values,
            'Widths': pint_pandas.PintArray(widths, dtype=widths.units),
            'WidthHeights': pint_pandas.PintArray(width_heights, dtype=volt),
            'LeftIPs': pint_pandas.PintArray(left_ips * dt, dtype=dt.units),
            'RightIPs': pint_pandas.PintArray(right_ips * dt, dtype=dt.units),
        })

        if compute_area:
            detector.peak_properties['Areas'] = self._compute_peak_areas(detector)

    @BaseClass.plot_wrapper
    def plot(self, detector: Detector, ax: plt.Axes = None, show: bool = True) -> None:
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
        # Convert units of signal and time for consistency
        signal_unit = detector.dataframe.Signal.max().to_compact().units
        time_unit = detector.dataframe.Time.max().to_compact().units

        # Update the detector dataframe with converted units
        detector.dataframe['Time'] = detector.dataframe.Time.pint.to(time_unit)
        detector.dataframe['Signal'] = detector.dataframe['Signal'].pint.to(signal_unit)

        # Create the plot using pandas plot method for the dataframe
        ax = detector.dataframe.plot(
            y='Signal',
            x='Time',
            style=['-', '--', '--'],
            ax=ax,
            ylabel=f'{detector.name} Signal [{signal_unit}]',
            xlabel=f'Time [{time_unit}]'
        )

        # Plot vertical lines at peak times
        for _, row in detector.peak_properties.iterrows():
            ax.axvline(row['PeakTimes'].to(time_unit), color='r', linestyle='--', lw=1, label='Peak')
