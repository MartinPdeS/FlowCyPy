import numpy as np
from scipy.signal import find_peaks

class ScipyPeakLocator:
    """
    A peak detection utility for identifying and extracting prominent peaks in 2D numerical arrays.

    This class provides a callable object that detects peaks in each row of a 2D NumPy array.
    It utilizes `scipy.signal.find_peaks` for peak detection and allows customization of
    peak height, distance, width, and prominence to refine peak selection. The detected
    peaks are returned in a structured format with NaN padding for missing values.

    Parameters
    ----------
    height : float, optional
        Minimum height a peak must have to be detected. Default is 2000.
    distance : int, optional
        Minimum horizontal distance between detected peaks. Default is 1.
    width : float, optional
        Minimum width of detected peaks. If None, width is not considered. Default is None.
    prominence : float, optional
        Minimum prominence of detected peaks. If None, prominence is not considered. Default is None.
    max_number_of_peaks : int, optional
        Maximum number of peaks to return per row. If fewer peaks are detected, NaN values
        are used as placeholders. Default is 5.

    Examples
    --------
    >>> import numpy as np
    >>> from scipy.signal import find_peaks
    >>> peak_locator = DefaultPeakLocator(height=1000, distance=2, max_number_of_peaks=3)
    >>> data = np.array([[0, 2000, 100, 5000, 200, 10000], [100, 50, 2000, 4000, 5000, 100]])
    >>> peaks = peak_locator(data)
    >>> print(peaks)
    [[ 1.  3.  5.]
     [ 2.  3.  4.]]

    Methods
    -------
    __call__(array)
        Detects peaks in each row of a 2D NumPy array and returns a structured output.

    Notes
    -----
    - The function expects a **2D NumPy array** as input.
    - If a row contains fewer peaks than `max_number_of_peaks`, NaN values are used as padding.
    - Uses `scipy.signal.find_peaks`, which applies thresholding techniques for peak detection.
    - The number of peaks found per row depends on the provided constraints (`height`, `distance`, etc.).

    """

    def __init__(self, height: float = 2000, distance: int = 1, width: float = None, prominence: float = None, max_number_of_peaks: int = 5, padding_value: object = -1):
        """
        Initializes the DefaultPeakLocator with configurable peak detection parameters.

        Parameters
        ----------
        height : float, optional
            Minimum height a peak must have to be detected. Default is 2000.
        distance : int, optional
            Minimum horizontal distance between detected peaks. Default is 1.
        width : float, optional
            Minimum width of detected peaks. If None, width is not considered. Default is None.
        prominence : float, optional
            Minimum prominence of detected peaks. If None, prominence is not considered. Default is None.
        max_number_of_peaks : int, optional
            Maximum number of peaks to return per row. If fewer peaks are detected, NaN values
            are used as placeholders. Default is 5.
        """
        self.height = height
        self.distance = distance
        self.width = width
        self.prominence = prominence
        self.max_number_of_peaks = max_number_of_peaks
        self.padding_value = padding_value

    def __call__(self, array: np.ndarray) -> np.ndarray:
        """
        Detects peaks in a 2D NumPy array.

        This function applies `scipy.signal.find_peaks` row-wise to detect peaks based
        on the specified height, distance, width, and prominence constraints. It returns
        a structured NumPy array where each row contains the detected peak indices,
        padded with NaN values if fewer than `max_number_of_peaks` peaks are found.

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

        Examples
        --------
        >>> import numpy as np
        >>> peak_locator = DefaultPeakLocator(height=500, distance=2, max_number_of_peaks=3)
        >>> data = np.array([[0, 800, 100, 2000, 150, 9000], [50, 1000, 200, 3000, 4000, 100]])
        >>> peaks = peak_locator(data)
        >>> print(peaks)
        [[ 1.  3.  5.]
         [ 1.  3.  4.]]
        """
        assert array.ndim == 2, "Array must be of dimension 2."

        num_rows = array.shape[0]
        padded_output = np.full((num_rows, self.max_number_of_peaks), self.padding_value)  # Default to NaN for missing values

        for i in range(num_rows):
            peaks, _ = find_peaks(
                array[i],
                height=self.height.magnitude,
                distance=self.distance,
                width=self.width,
                prominence=self.prominence
            )

            num_found = len(peaks)
            padded_output[i, :min(num_found, self.max_number_of_peaks)] = peaks[:self.max_number_of_peaks]  # Assign valid peaks

        return padded_output
