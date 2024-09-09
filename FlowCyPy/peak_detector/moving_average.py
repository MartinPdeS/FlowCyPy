from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks
from FlowCyPy.peak_detector.base_class import BasePeakDetector

@dataclass
class MovingAveragePeakDetector(BasePeakDetector):
    """
    A class to detect peaks in a signal using a moving average algorithm.
    A peak is detected when the signal exceeds the moving average by a defined threshold.

    Attributes
    ----------
    threshold : float
        The minimum difference between the signal and its moving average required to detect a peak.
    window_size : int
        The window size for calculating the moving average.
    min_peak_distance : float
        The minimum distance between detected peaks, in seconds.

    Methods
    -------
    detect_peaks(signal, time, dt, compute_area=True):
        Detects peaks and calculates their properties from the input signal.
    """

    threshold: Optional[float] = 0.2
    window_size: Optional[int] = 500
    min_peak_distance: Optional[float] = 0.1  # Minimum distance between peaks in time units
    rel_height: Optional[float] = 0.5

    def detect_peaks(self, signal: np.ndarray, time: np.ndarray, dt: float, compute_area: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects peaks in the signal using a moving average and a threshold.

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
        # Calculate the moving average of the signal
        moving_avg = uniform_filter1d(signal.magnitude, size=self.window_size)

        # Convert the time-based minimum peak distance to the corresponding number of samples
        min_peak_distance_samples = int(self.min_peak_distance / dt.magnitude)

        # Find peaks in this "thresholded" signal using the calculated sample distance
        peak_indices, _ = find_peaks(
            x=signal.magnitude,
            distance=min_peak_distance_samples,
            height=self.threshold,
            rel_height=self.rel_height
        )

        # Calculate peak times, heights, and widths
        peak_times = peak_indices * dt
        heights = signal[peak_indices]

        # Estimate widths using the distance between successive peaks
        if len(peak_indices) > 1:
            widths = np.diff(peak_indices) * dt
            widths = np.append(widths, widths[-1])  # Repeat the last width for the final peak
        else:
            widths = np.array([0])

        # If area computation is required
        areas = self.get_areas(
            peak_indices=peak_indices,
            widths=widths,
            signal=signal,
            time=time,
            dt=dt
        ) if compute_area else None

        return peak_times, heights, widths, areas
