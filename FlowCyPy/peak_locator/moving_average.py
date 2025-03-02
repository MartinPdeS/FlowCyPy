import numpy as np

class SlidingWindowPeakLocator:
    """
    A peak detection utility that identifies peaks in each row of a 2D array using a sliding window approach.

    This class segments each row of a 2D NumPy array into fixed-size windows and identifies the index of the
    local maximum within each window. The detected peak indices are returned in a structured 2D array.

    Unlike global peak-finding methods, this approach ensures that peaks are sampled evenly across the signal.

    Parameters
    ----------
    window_size : int
        The size of the sliding window used to detect local maxima.
    max_number_of_peaks : int, optional
        The maximum number of peaks to return per row. Default is 5.
    padding_value : int, optional
        The value used to pad the output when fewer than `max_number_of_peaks` peaks are detected. Default is -1.

    Examples
    --------
    >>> import numpy as np
    >>> data = np.array([
    ...     [1, 3, 2, 5, 4, 2, 8, 1],
    ...     [2, 1, 4, 3, 7, 0, 6, 2]
    ... ])
    >>> peak_locator = SlidingWindowPeakLocator(window_size=2, max_number_of_peaks=4, padding_value=-1)
    >>> peaks = peak_locator(data)
    >>> print(peaks)
    [[1. 3. 4. 6.]
     [0. 2. 4. 6.]]

    Notes
    -----
    - This method is particularly useful for signals containing multiple distinct regions of interest
      that need to be sampled at regular intervals.
    - If a row contains fewer peaks than `max_number_of_peaks`, the remaining entries are padded with `padding_value`.
    """

    def __init__(self, window_size: int, max_number_of_peaks: int = 5, padding_value: int = -1):
        """
        Initializes the SlidingWindowPeakLocator with the given parameters.

        Parameters
        ----------
        window_size : int
            The size of each sliding window.
        max_number_of_peaks : int, optional
            The maximum number of peaks to return per row. Default is 5.
        padding_value : int, optional
            The value used to pad missing peaks. Default is -1.
        """
        self.window_size = window_size
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value

    def __call__(self, array: np.ndarray) -> np.ndarray:
        """
        Detects peaks in each row of a 2D NumPy array using a sliding window.

        Each row is divided into non-overlapping windows of size `window_size`, and the index of the
        maximum value in each window is recorded.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate dataset for peak detection.

        Returns
        -------
        np.ndarray
            A 2D NumPy array of shape `(number_of_rows, max_number_of_peaks)`, where each entry contains
            the global index of the detected peak in the corresponding window. Rows with fewer detected
            peaks are padded with `padding_value`.

        Raises
        ------
        AssertionError
            If the input array is not a 2D NumPy array.

        Examples
        --------
        >>> import numpy as np
        >>> data = np.array([
        ...     [1, 3, 2, 5, 4, 2, 8, 1],
        ...     [2, 1, 4, 3, 7, 0, 6, 2]
        ... ])
        >>> peak_locator = SlidingWindowPeakLocator(window_size=2, max_number_of_peaks=4, padding_value=-1)
        >>> peaks = peak_locator(data)
        >>> print(peaks)
        [[1. 3. 4. 6.]
         [0. 2. 4. 6.]]
        """
        assert array.ndim == 2, "Input array must be 2D."

        num_rows, num_cols = array.shape
        num_windows = np.ceil(num_cols / self.window_size).astype(int)

        # Create an array to store peak indices
        peak_indices = np.full((num_rows, self.max_number_of_peaks), self.padding_value, dtype=int)

        for i in range(num_rows):
            row = array[i]

            # Generate window start and end indices
            window_starts = np.arange(0, num_cols, self.window_size)
            window_ends = np.minimum(window_starts + self.window_size, num_cols)

            # Extract indices of the local maxima within each window
            local_max_indices = []
            for start, end in zip(window_starts, window_ends):
                local_max_indices.append(start + np.argmax(row[start:end]))

            local_max_indices = np.array(local_max_indices)

            # Store the top max_number_of_peaks peaks, padding if necessary
            num_detected = min(len(local_max_indices), self.max_number_of_peaks)
            peak_indices[i, :num_detected] = local_max_indices[:num_detected]

        return peak_indices
