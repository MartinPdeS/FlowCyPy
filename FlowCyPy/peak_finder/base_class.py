from typing import Callable
import numpy as np
from FlowCyPy.units import ureg, volt, second
from FlowCyPy.detector import Detector
from scipy.integrate import cumulative_trapezoid
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
import pint_pandas


class BaseClass:
    """
    A base class to handle common functionality for peak detection,
    including area calculation under peaks.
    """

    def get_areas(self, peak_indices: np.ndarray, widths: np.ndarray, signal: np.ndarray, time: np.ndarray) -> np.ndarray:
        """
        Computes the area under each peak.

        Parameters
        ----------
        peak_indices : np.ndarray
            The indices of detected peaks in the signal.
        widths : np.ndarray
            The widths of the detected peaks.
        signal : np.ndarray
            The signal array.
        time : np.ndarray
            The time array corresponding to the signal.
        dt : float
            The time difference between consecutive samples in the signal.

        Returns
        -------
        np.ndarray
            The area under each peak.
        """
        dt = 1
        start_idx = np.maximum(0, (peak_indices - widths / (2 * self.dt)).astype(int)).magnitude
        end_idx = np.minimum(len(signal), (peak_indices + widths / (2 * dt)).astype(int)).magnitude

        areas = np.array([
            np.trapz(signal.magnitude[start:end], time.magnitude[start:end])
            for start, end in zip(start_idx, end_idx)
        ]) * ureg.volt * ureg.second

        return areas

    def _compute_peak_areas(self, detector: Detector) -> None:
        """
        Computes the areas under the detected peaks using vectorized operations.

        Parameters
        ----------
        detector : Detector
            DataFrame containing the signal data.

        """
        # Compute cumulative integral of the signal
        cumulative = cumulative_trapezoid(
            detector.dataframe.Signal.values.numpy_data,
            x=detector.dataframe.Time.values.numpy_data
        )
        cumulative_integral = np.concatenate(([0], cumulative))

        # Interpolate cumulative integral at left and right interpolated positions
        left_cum_integral = np.interp(
            x=detector.peak_properties.LeftIPs,
            xp=np.arange(len(detector.dataframe)),
            fp=cumulative_integral
        )

        right_cum_integral = np.interp(
            x=detector.peak_properties.RightIPs,
            xp=np.arange(len(detector.dataframe)),
            fp=cumulative_integral
        )

        # Compute areas under peaks
        areas = right_cum_integral - left_cum_integral

        detector.peak_properties['Areas'] = pint_pandas.PintArray(areas, dtype=volt * second)

    def plot_wrapper(plot_function: Callable) -> Callable:
        def wrapper(self, detector: object, show: bool = True, **kwargs):

            # Ensure the detector has the required signal data by running peak detection if needed
            if not hasattr(detector, 'peak_properties'):
                self.detect_peaks(detector=detector)

            with plt.style.context(mps):
                plot_function(self, detector=detector, **kwargs)

            # Display the plot if the show flag is set to True
            if show:
                plt.show()

        return wrapper
