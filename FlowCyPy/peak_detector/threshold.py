from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple
from FlowCyPy.peak_detector.base_class import BasePeakDetector

@dataclass
class ThresholdPeakDetector(BasePeakDetector):
    """
    A class to detect peaks in a signal using a first derivative (slope) method combined
    with thresholding to identify peaks.

    Attributes
    ----------
    slope_threshold : float
        The minimum slope required to detect a peak. Default is 0.1.
    """

    slope_threshold: float = 0.1

    def detect_peaks(self, signal: np.ndarray, time: np.ndarray, dt: float, compute_area: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects peaks in the signal using a slope threshold method and calculates their features
        such as height, width, and area.

        Parameters
        ----------
        signal : np.ndarray
            The signal data to detect peaks in.
        time : np.ndarray
            The time array corresponding to the signal.
        dt : float
            The time difference between consecutive samples in the signal.
        compute_area : bool, optional
            If True, computes the area under each peak. Default is True.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]
            Peak times, heights, widths, and optionally areas of detected peaks.
        """
        # First derivative (slope) of the signal
        signal_slope = np.diff(signal) / dt

        # Identify zero-crossings where the slope changes from positive to negative (peaks)
        peak_indices = np.where((signal_slope.magnitude[:-1] > self.slope_threshold) & (signal_slope.magnitude[1:] < -self.slope_threshold))[0] + 1

        # Extract peak properties
        peak_times = peak_indices * dt
        heights = signal[peak_indices]

        # Estimate width using the time between successive peaks
        if len(peak_indices) > 1:
            widths = np.diff(peak_indices) * dt
            widths = np.append(widths, widths[-1])  # Repeat the last width for the final peak
        else:
            widths = np.array([0])

        # Calculate areas if required
        areas = self.get_areas(peak_indices, widths, signal, time, dt) if compute_area else None

        return peak_times, heights, widths, areas
