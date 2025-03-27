import numpy as np
from FlowCyPy.binary import peak_locator_binding

class GlobalPeakLocator:
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

    def __init__(self, padding_value: object = -1, compute_width: bool = False, compute_area: bool = False, threshold: float = 0.5, max_number_of_peaks: int = 1):
        """
        Initializes the BasicPeakLocator with a specified padding value and options
        to compute additional metrics (width and area).
        """
        self.max_number_of_peaks = max_number_of_peaks

        self.instance = peak_locator_binding.GlobalPeakLocator(
            max_number_of_peaks=max_number_of_peaks,
            padding_value=padding_value,
            compute_width=compute_width,
            compute_area=compute_area,
            threshold=threshold
        )

    def __call__(self, array: np.ndarray) -> dict:
        """
        Detects the index of the maximum value in a 1D NumPy array.
        Optionally computes the width and area of the peak.

        The function finds the index of the maximum value in the array.
        If compute_width or compute_area is enabled, it computes the boundaries where
        the data falls below a specified threshold (fraction of the maximum value)
        and uses that to compute the width (number of samples) and the area under the peak.

        Parameters
        ----------
        array : np.ndarray
            A 1D NumPy array representing the signal for peak detection.

        Returns
        -------
        dict
            A dictionary with key "peak_index" (an integer with the index of the maximum in the array)
            and, if enabled, keys "width" and/or "area" (scalars with the computed peak width and area).

        Raises
        ------
        AssertionError
            If the input array is not 1-dimensional.
        """
        return self.instance(array)
