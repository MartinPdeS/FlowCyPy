from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from FlowCyPy.peak_locator.base_class import BasePeakLocator
import pandas as pd
import pint_pandas
from FlowCyPy.units import Quantity, microsecond


@dataclass
class DerivativePeakLocator(BasePeakLocator):
    """
    Detects peaks in a signal using a derivative-based algorithm.
    A peak is identified when the derivative exceeds a defined threshold.

    Parameters
    ----------
    derivative_threshold : Quantity, optional
        The minimum derivative value required to detect a peak.
        Default is `Quantity(0.1)`.
    min_peak_distance : Quantity, optional
        The minimum distance between detected peaks.
        Default is `Quantity(0.1)`.
    rel_height : float, optional
        The relative height at which the peak width is measured. Default is `0.5` (half-height).

    """

    derivative_threshold: Quantity = Quantity(0.1, 'volt/microsecond')
    min_peak_distance: Quantity = Quantity(0.1, microsecond)
    rel_height: float = 0.5

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

        if self.derivative_threshold is not None:
            self.derivative_threshold = self.derivative_threshold.to(
                self.data['Signal'].values.units / self.data['Time'].values.units
            )

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

    def _compute_peak_positions(self) -> None:
        """
        Compute peaks based on the derivative of the signal and refine their positions
        to align with the actual maxima in the original signal.
        """
        # Compute the derivative of the signal
        derivative = np.gradient(
            self.data['Signal'].values.quantity.magnitude,
            self.data['Time'].values.quantity.magnitude
        )
        derivative = pint_pandas.PintArray(
            derivative, dtype=self.data['Signal'].values.units / self.data['Time'].values.units
        )

        # Add the derivative to the DataFrame
        self.data['Derivative'] = derivative

        # Detect peaks in the derivative signal
        derivative_peak_indices, _ = find_peaks(
            self.data['Derivative'].values.quantity.magnitude,
            height=self.derivative_threshold.magnitude,
            prominence=0.1,  # Adjust this if needed
            plateau_size=True,
            distance=None if self.min_peak_distance is None else int(np.ceil(self.min_peak_distance / self.dt))
        )

        # Refine detected peaks to align with maxima in the original signal
        refined_peak_indices = []
        refinement_window = 5  # Number of samples around each derivative peak to search for the max

        for idx in derivative_peak_indices:
            # Define search window boundaries
            window_start = max(0, idx - refinement_window)
            window_end = min(len(self.data) - 1, idx + refinement_window)

            # Find the maximum in the original signal within the window
            true_max_idx = window_start + np.argmax(self.data['Signal'].iloc[window_start:window_end])
            refined_peak_indices.append(true_max_idx)

        refined_peak_indices = np.unique(refined_peak_indices)  # Remove duplicates

        return refined_peak_indices

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
        # Plot the derivative
        ax.plot(
            self.data.Time,
            self.data.Derivative,
            linestyle='--',
            color='C2',
            label='Derivative'
        )

        # Plot the derivative threshold line
        ax.axhline(
            y=self.derivative_threshold.to(self.data['Derivative'].values.units).magnitude,
            color='black',
            linestyle='--',
            label='Derivative Threshold',
            lw=1
        )
