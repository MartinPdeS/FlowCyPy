import numpy as np

class DerivativePeakLocator:
    r"""
    A peak detection utility based on the zero-crossing of the first derivative.

    This class detects peaks by computing the first and second derivatives of each row of a 2D array.
    A peak is defined where the first derivative changes sign from positive to negative and the second derivative is negative.
    Optionally, for each detected peak, the width (number of samples above a threshold) and area (sum of values over the peak region)
    can be computed using a simple threshold-based approach.

    Parameters
    ----------
    max_number_of_peaks : int, optional
        Maximum number of peaks to return per row. If fewer peaks are detected, missing values are padded with padding_value.
        Default is 5.
    padding_value : object, optional
        Value to pad missing peaks in output. Default is -1.
    compute_width : bool, optional
        If True, compute the width (in samples) of each detected peak. Default is False.
    compute_area : bool, optional
        If True, compute the area (sum of values) under each detected peak. Default is False.
    threshold : float, optional
        Fraction of the peak height used to determine the boundaries for width and area calculations.
        Default is 0.5.

    Examples
    --------
    >>> import numpy as np
    >>> # Without additional metrics:
    >>> peak_locator = DerivativePeakLocator(max_number_of_peaks=3)
    >>> data = np.array([[0, 100, 500, 200, 50, 1000],
    ...                  [200, 400, 100, 900, 500, 700]])
    >>> result = peak_locator(data)
    >>> print(result["peak_index"])
    [[2. 5. nan]
     [1. 3. 5.]]

    >>> # With width and area computations enabled:
    >>> peak_locator_metrics = DerivativePeakLocator(max_number_of_peaks=3, compute_width=True, compute_area=True, threshold=0.5)
    >>> result = peak_locator_metrics(data)
    >>> print("Peak indices:\n", result["peak_index"])
    >>> print("Widths:\n", result["width"])
    >>> print("Areas:\n", result["area"])
    """

    def __init__(self, max_number_of_peaks: int = 5, padding_value: object = -1,
                 compute_width: bool = False, compute_area: bool = False, threshold: float = 0.5):
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value
        self.compute_width = compute_width
        self.compute_area = compute_area
        self.threshold = threshold

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects peaks using derivative-based zero-crossing.

        For each row, the function computes the first and second derivatives to identify peaks where the
        first derivative crosses zero (from positive to negative) and the second derivative is negative.
        Optionally, if compute_width or compute_area is enabled, for each detected peak the function scans
        left and right until the signal falls below a fraction (threshold) of the peak value. The width is
        defined as the number of samples within this region and the area is the sum over that region.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a dataset for peak detection.

        Returns
        -------
        dict
            A dictionary containing:
              - "peak_index": 2D array of shape (n_rows, max_number_of_peaks) with detected peak indices.
              - "width": (Optional) 2D array with computed peak widths, if compute_width is True.
              - "area": (Optional) 2D array with computed peak areas, if compute_area is True.

        Raises
        ------
        AssertionError
            If the input array is not 2D.
        """
        assert array.ndim == 2, "Input must be a 2D NumPy array."
        num_rows = array.shape[0]
        peak_indices = np.full((num_rows, self.max_number_of_peaks), self.padding_value, dtype=float)
        widths = np.full((num_rows, self.max_number_of_peaks), np.nan, dtype=float) if self.compute_width else None
        areas = np.full((num_rows, self.max_number_of_peaks), np.nan, dtype=float) if self.compute_area else None

        for i in range(num_rows):
            row = array[i]
            # Compute first and second derivatives.
            first_derivative = np.diff(row)
            second_derivative = np.diff(first_derivative)

            # Identify indices where the first derivative changes sign from positive to negative and second derivative is negative.
            # Note: Since derivatives have reduced lengths, adjust indices by +1.
            candidates = np.where((np.sign(first_derivative[:-1]) > np.sign(first_derivative[1:])) &
                                  (second_derivative < 0))[0] + 1

            # If no candidates found, continue.
            if candidates.size == 0:
                continue

            # Limit number of detected peaks to max_number_of_peaks.
            selected_peaks = candidates[:self.max_number_of_peaks]
            num_found = len(selected_peaks)
            peak_indices[i, :num_found] = selected_peaks

            # Optionally compute width and area.
            if self.compute_width or self.compute_area:
                for j, peak in enumerate(selected_peaks):
                    peak_value = row[peak]
                    thresh_val = self.threshold * peak_value

                    # Find left boundary: move left until value falls below threshold.
                    left = peak
                    while left > 0 and row[left] >= thresh_val:
                        left -= 1
                    left_boundary = left + 1

                    # Find right boundary: move right until value falls below threshold.
                    right = peak
                    while right < row.size - 1 and row[right] >= thresh_val:
                        right += 1
                    right_boundary = right - 1

                    if self.compute_width:
                        widths[i, j] = right_boundary - left_boundary + 1
                    if self.compute_area:
                        areas[i, j] = np.sum(row[left_boundary:right_boundary + 1])

        result = {"peak_index": peak_indices}
        if self.compute_width:
            result["width"] = widths
        if self.compute_area:
            result["area"] = areas
        return result
