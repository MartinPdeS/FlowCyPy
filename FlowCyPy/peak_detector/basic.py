import numpy as np
from typing import Optional
from scipy.signal import find_peaks, peak_widths
from dataclasses import dataclass
from FlowCyPy.peak_detector.base_class import BasePeakDetector


@dataclass
class BasicPeakDetector(BasePeakDetector):
    """
    A class to detect peaks in a signal and calculate their properties such as height, width, and area.

    Attributes
    ----------
    height_threshold : float
        The minimum height required for a peak to be considered significant.

    Methods
    -------
    detect_peaks(signal, time, dt, compute_area=True, height_threshold=None):
        Detects peaks and calculates their properties from the input signal.
    """

    height_threshold: Optional[float] = None

    def detect_peaks(self, signal: np.ndarray, time: np.ndarray, dt: float, compute_area: bool = True):
        """
        Detects peaks in the signal and calculates their features such as height, width, and area.

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
        # Find peak indices using scipy's find_peaks
        peak_indices, _ = find_peaks(signal.magnitude, height=self.height_threshold)

        # Calculate peak times, heights, and widths
        peak_times = peak_indices * dt
        heights = signal[peak_indices]
        widths = peak_widths(signal.magnitude, peak_indices, rel_height=0.5)[0] * dt

        # If area computation is required
        if compute_area:
            areas = self.get_areas(peak_indices, widths, signal, time, dt)
            return peak_times, heights, widths, areas

        return peak_times, heights, widths, None