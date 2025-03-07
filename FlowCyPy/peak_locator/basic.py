import numpy as np

class BasicPeakLocator:
    r"""
    A peak detection utility that identifies the maximum value in each row of a 2D array.

    Optionally, the peak detection can also compute the width and area of the peak.

    The width is computed as the number of contiguous points around the maximum that remain above
    a specified fraction (threshold) of the maximum value. The area is the sum of the values over
    that same region.

    Parameters
    ----------
    padding_value : object, optional
        Value used to pad the output if a row contains no data. Default is -1.
    compute_width : bool, optional
        If True, the width of the peak (number of samples) is computed. Default is False.
    compute_area : bool, optional
        If True, the area (sum of values) of the peak is computed. Default is False.
    threshold : float, optional
        Fraction of the peak value used to determine the boundaries for width and area computation.
        For example, a threshold of 0.5 means the region above 50% of the maximum is considered.
        Default is 0.5.

    Examples
    --------
    >>> import numpy as np
    >>> data = np.array([
    ...     [0, 800, 100, 2000, 150, 9000],
    ...     [50, 1000, 200, 3000, 4000, 100]
    ... ])
    >>> # Only compute peak indices:
    >>> peak_locator = BasicPeakLocator(padding_value=-1)
    >>> results = peak_locator(data)
    >>> print("Peak Indices:\n", results["peak_index"])
    >>> print("Widths:\n", results["width"])
    >>> print("Areas:\n", results["area"])
    >>> # Compute peak index, width, and area:
    >>> peak_locator_metrics = BasicPeakLocator(padding_value=-1, compute_width=True, compute_area=True, threshold=0.5)
    >>> results = peak_locator_metrics(data)
    >>> print("Peak Indices:\n", results["peak_index"])
    >>> print("Widths:\n", results["width"])
    >>> print("Areas:\n", results["area"])
    """

    def __init__(self, padding_value: object = -1, compute_width: bool = False, compute_area: bool = False, threshold: float = 0.5):
        """
        Initializes the BasicPeakLocator with a specified padding value and options
        to compute additional metrics (width and area).
        """
        self.padding_value = padding_value
        self.compute_width = compute_width
        self.compute_area = compute_area
        self.threshold = threshold

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects the index of the maximum value in each row of a 2D NumPy array.
        Optionally computes the width and area of the peak.

        For each row, the method finds the index of the maximum value. If compute_width or compute_area
        is enabled, it computes the boundaries where the data fall below the specified threshold
        (fraction of the maximum value) and uses that to compute the width (number of samples) and the area.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate dataset for peak detection.

        Returns
        -------
        dict
            A dictionary with key "peak_index" (2D array of shape (n_rows, 1) containing the index of the
            maximum in each row) and, if enabled, keys "width" and/or "area" (2D arrays with the computed
            peak widths and areas, respectively).

        Raises
        ------
        AssertionError
            If the input array is not 2-dimensional.
        """
        assert array.ndim == 2, "Input array must be 2D."
        num_rows = array.shape[0]
        peak_indices = np.full((num_rows, 1), self.padding_value, dtype=float)
        widths = np.full((num_rows, 1), np.nan, dtype=float) if self.compute_width else None
        areas = np.full((num_rows, 1), np.nan, dtype=float) if self.compute_area else None

        for i in range(num_rows):
            if array.shape[1] == 0:
                continue
            row = array[i]
            max_idx = np.argmax(row)
            peak_indices[i, 0] = max_idx

            if self.compute_width or self.compute_area:
                max_val = row[max_idx]
                threshold_val = self.threshold * max_val

                # Find left boundary: move left until value falls below threshold.
                left = max_idx
                while left > 0 and row[left] >= threshold_val:
                    left -= 1
                left_boundary = left + 1  # first index above threshold

                # Find right boundary: move right until value falls below threshold.
                right = max_idx
                while right < row.size - 1 and row[right] >= threshold_val:
                    right += 1
                right_boundary = right - 1  # last index above threshold

                if self.compute_width:
                    widths[i, 0] = right_boundary - left_boundary + 1

                if self.compute_area:
                    areas[i, 0] = np.sum(row[left_boundary:right_boundary + 1])

        result = {"peak_index": peak_indices}
        if self.compute_width:
            result["width"] = widths
        if self.compute_area:
            result["area"] = areas

        return result
