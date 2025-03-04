import numpy as np
from scipy.signal import find_peaks, peak_widths

class ScipyPeakLocator:
    """
    A peak detection utility that uses SciPy's find_peaks to detect prominent peaks in each row of a 2D NumPy array.
    Optionally, it can also compute additional metrics such as the peak width and area.

    The width is computed using SciPy's peak_widths function (with rel_height=0.5 by default),
    and the area is computed as the sum of the signal over the interval defined by the left and right
    interpolated positions returned by peak_widths.

    Parameters
    ----------
    height : float, optional
        Minimum height a peak must have to be detected. Default is 2000.
    distance : int, optional
        Minimum horizontal distance between detected peaks. Default is 1.
    width : float, optional
        Minimum width of detected peaks. If None, width is not explicitly constrained. Default is None.
    prominence : float, optional
        Minimum prominence of detected peaks. If None, prominence is not explicitly constrained. Default is None.
    max_number_of_peaks : int, optional
        Maximum number of peaks to return per row. If fewer peaks are detected, missing values
        are padded with the padding_value. Default is 5.
    padding_value : object, optional
        Value used to pad missing peaks. Default is -1.
    compute_width : bool, optional
        If True, computes the width (in number of samples) of each detected peak. Default is False.
    compute_area : bool, optional
        If True, computes the area (sum over the peak region) for each detected peak. Default is False.

    Examples
    --------
    >>> import numpy as np
    >>> # Create an instance that only detects peak indices:
    >>> peak_locator = ScipyPeakLocator(height=500, distance=2, max_number_of_peaks=3)
    >>> data = np.array([[0, 800, 100, 2000, 150, 9000],
    ...                  [50, 1000, 200, 3000, 4000, 100]])
    >>> result = peak_locator(data)
    >>> print(result["peak_index"])
    [[ 1.  3.  5.]
     [ 2.  3.  4.]]
    >>> # Create an instance that also computes peak width and area:
    >>> peak_locator_metrics = ScipyPeakLocator(height=500, distance=2, max_number_of_peaks=3, compute_width=True, compute_area=True)
    >>> result = peak_locator_metrics(data)
    >>> print("Peak Indices:\n", result["peak_index"])
    >>> print("Widths:\n", result["width"])
    >>> print("Areas:\n", result["area"])
    """

    def __init__(self, height: float = 2000, distance: int = 1, width: float = None, prominence: float = None,
                 max_number_of_peaks: int = 5, padding_value: object = -1,
                 compute_width: bool = False, compute_area: bool = False):
        self.height = height
        self.distance = distance
        self.width = width
        self.prominence = prominence
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value
        self.compute_width = compute_width
        self.compute_area = compute_area

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects peaks in each row of a 2D NumPy array using SciPy's find_peaks.
        Optionally computes the width and area for each detected peak.

        For each row, the function applies find_peaks with the specified constraints.
        If compute_width or compute_area is enabled, the peak_widths function is used
        (with rel_height=0.5) to determine the width boundaries. The area is computed by summing
        the row values between the left and right boundaries.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate dataset for peak detection.

        Returns
        -------
        dict
            A dictionary with the key "peak_index" containing a 2D array of shape (n_rows, 1)
            with the detected peak indices (padded with padding_value if fewer than max_number_of_peaks
            are detected). Additionally, if compute_width is True, the key "width" is included;
            if compute_area is True, the key "area" is included.

        Raises
        ------
        AssertionError
            If the input array is not 2-dimensional.
        """
        assert array.ndim == 2, "Input array must be 2D."
        num_rows = array.shape[0]

        peak_indices_list = []
        widths_list = [] if self.compute_width else None
        areas_list = [] if self.compute_area else None

        for i in range(num_rows):
            row = array[i]
            # Use find_peaks with the specified constraints.
            peaks, properties = find_peaks(
                row,
                height=self.height,
                distance=self.distance,
                width=self.width,
                prominence=self.prominence
            )

            # If additional metrics are requested, compute them using peak_widths.
            if self.compute_width or self.compute_area:
                # peak_widths returns: widths, left_ips, right_ips, prominences
                widths_result = peak_widths(row, peaks, rel_height=0.5)
                computed_widths = widths_result[0]  # widths in number of samples
                left_ips = widths_result[1]
                right_ips = widths_result[2]

            # Collect metrics for the current row.
            row_peak_indices = list(peaks)
            row_widths = list(computed_widths) if self.compute_width else None
            row_areas = []
            if self.compute_area:
                for j, peak in enumerate(peaks):
                    left = int(np.floor(left_ips[j]))
                    right = int(np.ceil(right_ips[j]))
                    row_areas.append(np.sum(row[left:right+1]))

            # Pad the results up to max_number_of_peaks.
            pad_val = self.padding_value
            num_found = len(row_peak_indices)
            padded_peak_indices = np.full(self.max_number_of_peaks, pad_val, dtype=float)
            padded_peak_indices[:min(num_found, self.max_number_of_peaks)] = row_peak_indices[:self.max_number_of_peaks]
            peak_indices_list.append(padded_peak_indices)

            if self.compute_width:
                padded_widths = np.full(self.max_number_of_peaks, np.nan, dtype=float)
                padded_widths[:min(num_found, self.max_number_of_peaks)] = np.array(row_widths)[:self.max_number_of_peaks]
                widths_list.append(padded_widths)
            if self.compute_area:
                padded_areas = np.full(self.max_number_of_peaks, np.nan, dtype=float)
                padded_areas[:min(num_found, self.max_number_of_peaks)] = np.array(row_areas)[:self.max_number_of_peaks]
                areas_list.append(padded_areas)

        # Combine per-row results into arrays.
        peak_indices_array = np.vstack(peak_indices_list)
        result = {"peak_index": peak_indices_array}
        if self.compute_width:
            result["width"] = np.vstack(widths_list)
        if self.compute_area:
            result["area"] = np.vstack(areas_list)
        return result
