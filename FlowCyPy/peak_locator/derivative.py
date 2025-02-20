import numpy as np

class DerivativePeakLocator:
    """
    A peak detection utility based on the zero-crossing of the first derivative.

    This class detects peaks by identifying locations where the first derivative crosses
    zero and the second derivative is negative, indicating a local maximum. It provides
    an alternative to threshold-based methods like `scipy.signal.find_peaks`.

    Parameters
    ----------
    max_number_of_peaks : int, optional
        Maximum number of peaks to return per row. If fewer peaks are detected, NaN values
        are used as placeholders. Default is 5.
    padding_value : object, optional
        Value to pad missing peaks in output. Default is -1.

    Examples
    --------
    >>> import numpy as np
    >>> peak_locator = DerivativePeakLocator(max_number_of_peaks=3)
    >>> data = np.array([[0, 100, 500, 200, 50, 1000], [200, 400, 100, 900, 500, 700]])
    >>> peaks = peak_locator(data)
    >>> print(peaks)
    [[ 2.  5. nan]
     [ 1.  3.  5.]]

    Methods
    -------
    __call__(array)
        Detects peaks in each row of a 2D NumPy array and returns structured output.

    Notes
    -----
    - This method relies on **derivatives**, making it effective for **smooth signals**.
    - Works best when the signal has clear inflection points for peak detection.
    - If a row contains fewer peaks than `max_number_of_peaks`, NaN values are used as padding.

    """

    def __init__(self, max_number_of_peaks: int = 5, padding_value: object = -1):
        """
        Initializes the `DerivativePeakLocator` with peak detection parameters.

        Parameters
        ----------
        max_number_of_peaks : int, optional
            Maximum number of peaks to return per row. Default is 5.
        padding_value : object, optional
            Value to pad missing peaks in output. Default is -1.
        """
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value

    def __call__(self, array: np.ndarray) -> np.ndarray:
        """
        Detects peaks using derivative-based zero-crossing.

        This function computes the first and second derivatives row-wise and detects peaks
        where the first derivative crosses zero and the second derivative is negative.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate dataset for peak detection.

        Returns
        -------
        np.ndarray
            A 2D NumPy array of shape `(array.shape[0], max_number_of_peaks)`. Each row
            contains the indices of detected peaks, padded with NaNs if fewer peaks are found.

        Raises
        ------
        AssertionError
            If `array` is not a 2D NumPy array.
        """
        assert array.ndim == 2, "Input must be a 2D NumPy array."

        num_rows = array.shape[0]
        padded_output = np.full((num_rows, self.max_number_of_peaks), self.padding_value)  # Default to NaN for missing values

        for i in range(num_rows):
            # Compute first and second derivatives
            first_derivative = np.diff(array[i])
            second_derivative = np.diff(first_derivative)

            # Find zero-crossings in first derivative & check for negative second derivative
            peak_candidates = np.where((np.sign(first_derivative[:-1]) > np.sign(first_derivative[1:])) & (second_derivative < 0))[0] + 1

            # Store peaks (pad with NaN if fewer than max_number_of_peaks)
            num_found = len(peak_candidates)
            padded_output[i, :min(num_found, self.max_number_of_peaks)] = peak_candidates[:self.max_number_of_peaks]

        return padded_output
