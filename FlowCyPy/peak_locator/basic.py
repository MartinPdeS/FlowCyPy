import numpy as np

class BasicPeakLocator:
    """
    A peak detection utility that identifies the maximum value in each row of a 2D array.

    This class provides a callable object that detects the index of the maximum value in each
    row of a 2D NumPy array. Unlike methods that rely on thresholding or derivative-based techniques,
    this locator simply returns the index corresponding to the highest value in each row. The result
    is a 2D array with one peak index per row, padded with a specified value if necessary.

    Parameters
    ----------
    padding_value : object, optional
        Value used to pad the output if a row contains no data. Default is -1.

    Examples
    --------
    >>> import numpy as np
    >>> data = np.array([
    ...     [0, 800, 100, 2000, 150, 9000],
    ...     [50, 1000, 200, 3000, 4000, 100]
    ... ])
    >>> peak_locator = MaxPeakLocator(padding_value=-1)
    >>> peaks = peak_locator(data)
    >>> print(peaks)
    [[5.]
     [4.]]

    Methods
    -------
    __call__(array)
        Returns a 2D array where each row contains the index of the maximum value in the corresponding
        row of the input array.

    Notes
    -----
    - The function expects a 2D NumPy array as input.
    - If a row is empty (i.e. has zero columns), the padding value is returned.
    """

    def __init__(self, padding_value: object = -1):
        """
        Initializes the MaxPeakLocator with a specified padding value.

        Parameters
        ----------
        padding_value : object, optional
            Value used to pad missing peaks. Default is -1.
        """
        self.padding_value = padding_value

    def __call__(self, array: np.ndarray) -> np.ndarray:
        """
        Detects the index of the maximum value in each row of a 2D NumPy array.

        This function computes the index of the maximum value for each row in the input array.
        The output is a 2D NumPy array of shape (number_of_rows, 1). If a row is empty, the
        padding value is returned.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate dataset for peak detection.

        Returns
        -------
        np.ndarray
            A 2D NumPy array of shape (array.shape[0], 1) where each entry contains the index of the
            maximum value in the corresponding row. Rows with no data are filled with the padding value.

        Raises
        ------
        AssertionError
            If the input array is not 2-dimensional.

        Examples
        --------
        >>> import numpy as np
        >>> data = np.array([
        ...     [0, 800, 100, 2000, 150, 9000],
        ...     [50, 1000, 200, 3000, 4000, 100]
        ... ])
        >>> peak_locator = MaxPeakLocator(padding_value=-1)
        >>> peaks = peak_locator(data)
        >>> print(peaks)
        [[5.]
         [4.]]
        """
        assert array.ndim == 2, "Input array must be 2D."
        num_rows = array.shape[0]
        output = np.full((num_rows, 1), self.padding_value, dtype=float)

        for i in range(num_rows):
            if array.shape[1] == 0:
                continue
            max_idx = np.argmax(array[i])
            output[i, 0] = max_idx

        return output
