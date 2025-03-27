import numpy as np
from FlowCyPy.binary import peak_locator_binding

class SlidingWindowPeakLocator:
    r"""
    SlidingWindowPeakLocator(window_size, window_step=-1, max_number_of_peaks=5, padding_value=-1,
                               compute_width=False, compute_area=False, threshold=0.5)

    A sliding-window-based peak detection utility for 1D signals. This class segments the input signal
    into fixed-size windows (which can be overlapping if window_step is less than window_size) and identifies
    the local maximum in each window. Optionally, it computes additional metrics for each peak:
    - Width: the number of contiguous samples above a specified fraction of the peak's height.
    - Area: the sum of signal values under the peak within its window.

    The results are returned as a dictionary containing fixed-length arrays. If fewer peaks are detected than
    max_number_of_peaks, the arrays are padded with padding_value (for indices) or NaN (for numeric values).

    Parameters
    ----------
    window_size : int
        The size of the sliding window used for local peak detection.
    window_step : int, optional
        The step size between consecutive windows. If not provided or set to -1, defaults to window_size
        (i.e., non-overlapping windows). To create overlapping windows, specify a value less than window_size.
    max_number_of_peaks : int, optional
        The maximum number of peaks to report. If fewer peaks are detected, the results are padded. Default is 5.
    padding_value : int, optional
        The value used to pad the output array for indices when fewer than max_number_of_peaks peaks are found.
        Default is -1.
    compute_width : bool, optional
        If True, compute and return the width of each detected peak (in samples). Default is False.
    compute_area : bool, optional
        If True, compute and return the area (sum of signal values) under each detected peak. Default is False.
    threshold : float, optional
        The fraction of the peak's height used to determine the boundaries for width and area calculations.
        For example, a threshold of 0.5 uses 50% of the peak height as the cutoff. Default is 0.5.

    Returns
    -------
    dict
        A dictionary containing the following keys:
          - "Index": A fixed-length array of detected peak indices, padded as necessary.
          - "Height": A fixed-length array of the corresponding peak values.
          - "Width": (optional) A fixed-length array of computed peak widths (if compute_width is True).
          - "Area": (optional) A fixed-length array of computed peak areas (if compute_area is True).

    Examples
    --------
    >>> import numpy as np
    >>> # Example signal
    >>> data = np.array([1, 3, 2, 5, 4, 2, 8, 1], dtype=float)
    >>> # Create a peak locator without additional metrics (non-overlapping windows).
    >>> locator = SlidingWindowPeakLocator(window_size=2, max_number_of_peaks=4, padding_value=-1)
    >>> result = locator(data)
    >>> print("Indices:", result["Index"])
    [1, 3, 4, 6]
    >>> print("Heights:", result["Height"])
    [3.0, 5.0, 4.0, 8.0]
    >>> # Create a peak locator with overlapping windows and with width and area computations.
    >>> locator_metrics = SlidingWindowPeakLocator(window_size=4, window_step=2, max_number_of_peaks=4,
    ...                                             padding_value=-1, compute_width=True, compute_area=True, threshold=0.5)
    >>> result = locator_metrics(data)
    >>> print("Peak indices:", result["Index"])
    >>> print("Heights:", result["Height"])
    >>> print("Widths:", result["Width"])
    >>> print("Areas:", result["Area"])
    """
    def __init__(self,
        window_size: int,
        max_number_of_peaks: int = 5,
        padding_value: int = -1,
        window_step: int = -1,
        compute_width: bool = False,
        compute_area: bool = False,
        threshold: float = 0.5):

        self.max_number_of_peaks = max_number_of_peaks

        self.instance = peak_locator_binding.SlidingWindowPeakLocator(
            window_size=window_size,
            window_step=window_step,
            max_number_of_peaks=max_number_of_peaks,
            padding_value=padding_value,
            compute_width=compute_width,
            compute_area=compute_area,
            threshold=threshold
        )

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects peaks in a 1D NumPy array using a sliding window approach.

        The signal is divided into non-overlapping windows of size `window_size`, and within each window,
        the index of the local maximum is recorded. Optionally, for each detected peak, the width and area
        are computed based on a threshold (a fraction of the peak's height).

        Parameters
        ----------
        array : np.ndarray
            A 1D NumPy array representing the signal for peak detection.

        Returns
        -------
        dict
            A dictionary containing:
              - "Index": A 1D array of fixed length (max_number_of_peaks) with detected peak indices.
              - "Height": A 1D array with the corresponding peak heights.
              - "Width": (Optional) A 1D array with computed widths, if compute_width is True.
              - "Area": (Optional) A 1D array with computed areas, if compute_area is True.
        """
        return self.instance(array)