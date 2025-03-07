import numpy as np

class SlidingWindowPeakLocator:
    r"""
    A peak detection utility that identifies peaks in each row of a 2D array using a sliding window approach.

    Each row is segmented into fixed-size windows, and the local maximum is found in each window.
    Optionally, the width (number of samples above a threshold) and the area (sum of values) of each
    peak within its window are computed.

    Parameters
    ----------
    window_size : int
        The size of the sliding window used to detect local maxima.
    max_number_of_peaks : int, optional
        The maximum number of peaks to return per row. Default is 5.
    padding_value : int, optional
        The value used to pad the output when fewer than `max_number_of_peaks` peaks are detected. Default is -1.
    compute_width : bool, optional
        If True, compute the width (in samples) of each detected peak. Default is False.
    compute_area : bool, optional
        If True, compute the area (sum of signal values) under each detected peak. Default is False.
    threshold : float, optional
        Fraction of the peak height used to determine the boundaries for width and area calculations.
        Default is 0.5.

    Examples
    --------
    >>> import numpy as np
    >>> data = np.array([
    ...     [1, 3, 2, 5, 4, 2, 8, 1],
    ...     [2, 1, 4, 3, 7, 0, 6, 2]
    ... ])
    >>> # Without additional metrics:
    >>> locator = SlidingWindowPeakLocator(window_size=2, max_number_of_peaks=4, padding_value=-1)
    >>> result = locator(data)
    >>> print(result["peak_index"])
    [[1 3 4 6]
     [0 2 4 6]]
    >>> # With width and area computations enabled:
    >>> locator_metrics = SlidingWindowPeakLocator(window_size=2, max_number_of_peaks=4, padding_value=-1,
    ...                                             compute_width=True, compute_area=True, threshold=0.5)
    >>> result = locator_metrics(data)
    >>> print("Peak indices:\n", result["peak_index"])
    >>> print("Widths:\n", result["width"])
    >>> print("Areas:\n", result["area"])
    """

    def __init__(self, window_size: int, max_number_of_peaks: int = 5, padding_value: int = -1,
                 compute_width: bool = False, compute_area: bool = False, threshold: float = 0.5):
        self.window_size = window_size
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value
        self.compute_width = compute_width
        self.compute_area = compute_area
        self.threshold = threshold

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects peaks in each row of a 2D NumPy array using a sliding window approach.

        Each row is divided into non-overlapping windows of size `window_size`, and the index of the local
        maximum within each window is recorded. Optionally, for each detected peak the width and area are computed.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a dataset for peak detection.

        Returns
        -------
        dict
            A dictionary containing:
              - "peak_index": A 2D array of shape (num_rows, max_number_of_peaks) with detected peak indices.
              - "width": (Optional) A 2D array with computed widths, if compute_width is True.
              - "area": (Optional) A 2D array with computed areas, if compute_area is True.
        """
        assert array.ndim == 2, "Input array must be 2D."
        num_rows, num_cols = array.shape
        num_windows = int(np.ceil(num_cols / self.window_size))

        # Prepare lists to collect per-row results.
        all_peak_indices = []
        all_widths = [] if self.compute_width else None
        all_areas = [] if self.compute_area else None

        for i in range(num_rows):
            row = array[i]
            window_starts = np.arange(0, num_cols, self.window_size)
            window_ends = np.minimum(window_starts + self.window_size, num_cols)

            local_peak_indices = []
            local_widths = [] if self.compute_width else None
            local_areas = [] if self.compute_area else None

            # Process each window.
            for start, end in zip(window_starts, window_ends):
                window = row[start:end]
                if window.size == 0:
                    continue
                # Global index of the local maximum.
                local_peak = start + np.argmax(window)
                local_peak_indices.append(local_peak)

                if self.compute_width or self.compute_area:
                    peak_value = row[local_peak]
                    thresh_val = self.threshold * peak_value

                    # Compute left boundary within the window.
                    left = local_peak
                    while left > start and row[left] >= thresh_val:
                        left -= 1
                    left_boundary = left + 1  # first index above threshold

                    # Compute right boundary within the window.
                    right = local_peak
                    while right < end - 1 and row[right] >= thresh_val:
                        right += 1
                    right_boundary = right - 1  # last index above threshold

                    if self.compute_width:
                        local_widths.append(right_boundary - left_boundary + 1)
                    if self.compute_area:
                        local_areas.append(np.sum(row[left_boundary:right_boundary + 1]))

            # Pad results to ensure fixed size output per row.
            num_found = len(local_peak_indices)
            pad_peak = np.full(self.max_number_of_peaks, self.padding_value, dtype=int)
            pad_peak[:min(num_found, self.max_number_of_peaks)] = local_peak_indices[:self.max_number_of_peaks]
            all_peak_indices.append(pad_peak)

            if self.compute_width:
                pad_width = np.full(self.max_number_of_peaks, np.nan, dtype=float)
                if local_widths is not None:
                    pad_width[:min(num_found, self.max_number_of_peaks)] = np.array(local_widths)[:self.max_number_of_peaks]
                all_widths.append(pad_width)
            if self.compute_area:
                pad_area = np.full(self.max_number_of_peaks, np.nan, dtype=float)
                if local_areas is not None:
                    pad_area[:min(num_found, self.max_number_of_peaks)] = np.array(local_areas)[:self.max_number_of_peaks]
                all_areas.append(pad_area)

        # Convert lists to arrays.
        peak_indices_arr = np.vstack(all_peak_indices)
        result = {"peak_index": peak_indices_arr}
        if self.compute_width:
            result["width"] = np.vstack(all_widths)
        if self.compute_area:
            result["area"] = np.vstack(all_areas)
        return result
