import numpy as np

class DeepPeakLocator:
    """
    A peak detection utility leveraging deep learning models for robust peak identification.

    This class utilizes a trained deep learning model from the `DeepPeak` framework to detect
    peak regions in a 2D NumPy array. The model predicts **regions of interest (ROIs)**, and
    the final peak locations are extracted by finding the middle index of each ROI.

    Unlike traditional peak detection methods that rely on local maxima or thresholding, this
    approach leverages neural network-based feature extraction to enhance robustness against
    noise, variations in signal shape, and overlapping peaks.

    Parameters
    ----------
    model_name : str
        The name of the trained model to load from `DeepPeak`. This should correspond to a
        `.keras` file located in the `DeepPeak` weights directory.
    uncertainty : float, optional
        The confidence threshold for peak detection. Only predictions above this threshold
        are retained. Default is `0.9`.
    n_samples : int, optional
        The number of samples per segment the model evaluates for predictions. Default is `30`.
    padding_value : object, optional
        The value used to fill missing peaks when fewer than expected are detected. Default is `-1`.

    Examples
    --------
    >>> import numpy as np
    >>> peak_locator = DeepPeakLocator(model_name="peak_detection_model", uncertainty=0.85)
    >>> data = np.random.rand(10, 128)  # Simulated signal matrix (10 signals, 128 samples each)
    >>> peak_indices = peak_locator(data)
    >>> print(peak_indices)
    [[ 10  50  90  -1  -1]
     [ 20  70  100 -1  -1]
     [ 30  55  85 110 -1]]

    Notes
    -----
    - This method requires `DeepPeak` and TensorFlow to be installed.
    - The deep learning model must be trained and available in the `DeepPeak` weights directory.
    - The method extracts peak regions, and the final peak locations are computed by selecting
      the center index of each detected **Region of Interest (ROI)**.
    - This method is particularly useful for detecting peaks in complex, noisy signals where
      traditional thresholding or derivative-based techniques fail.

    Methods
    -------
    __call__(array)
        Detects peaks in a 2D NumPy array using the deep learning model.
    """

    def __init__(self, model_name: str, uncertainty: float = 0.9, n_samples: int = 30, padding_value: object = -1, max_number_of_peaks: int = 5):
        """
        Initializes the DeepPeakLocator with the specified model and detection parameters.

        Parameters
        ----------
        model_name : str
            Name of the trained deep learning model (without file extension).
        uncertainty : float, optional
            Confidence threshold for peak detection. Default is `0.9`.
        n_samples : int, optional
            Number of samples per segment analyzed by the model. Default is `30`.
        padding_value : object, optional
            Value used to pad missing peaks when fewer than expected are detected. Default is `-1`.
        """
        self.model_name = model_name
        self.uncertainty = uncertainty
        self.padding_value = padding_value
        self.n_samples = n_samples
        self.max_number_of_peaks = max_number_of_peaks

    def __call__(self, array: np.ndarray) -> np.ndarray:
        """
        Detects peaks in a 2D NumPy array using a trained deep learning model.

        This method loads a pre-trained deep learning model from `DeepPeak`, applies it to the
        input signal array, and extracts peak locations from the predicted **Regions of Interest (ROIs)**.

        Parameters
        ----------
        array : np.ndarray
            A 2D NumPy array where each row represents a separate signal for peak detection.

        Returns
        -------
        np.ndarray
            A 2D NumPy array of shape `(num_rows, max_number_of_peaks)`, where each row contains
            the detected peak indices, padded with `padding_value` if fewer peaks are found.

        Raises
        ------
        ImportError
            If `DeepPeak` or TensorFlow is not installed.
        FileNotFoundError
            If the specified model file does not exist in the `DeepPeak` weights directory.
        AssertionError
            If the input array is not 2D.

        Examples
        --------
        >>> import numpy as np
        >>> peak_locator = DeepPeakLocator(model_name="peak_detection_model", uncertainty=0.9)
        >>> data = np.random.rand(10, 128)
        >>> peak_indices = peak_locator(data)
        >>> print(peak_indices)
        [[ 10  50  90  -1  -1]
         [ 20  70  100 -1  -1]]

        Notes
        -----
        - The model predicts **Regions of Interest (ROIs)**, and the final peak locations are computed
          by selecting the middle index of each detected ROI.
        - This method is particularly useful for detecting peaks in complex, noisy signals where
          traditional thresholding or derivative-based techniques fail.
        """
        try:
            from DeepPeak.directories import weights_path
            from DeepPeak.utils.ROI import find_middle_indices
            from DeepPeak.models import filter_predictions
            from tensorflow import keras
        except ImportError as e:
            raise ImportError("DeepPeak and TensorFlow are required for this method.") from e

        # Load trained deep learning model
        model_path = weights_path / f'{self.model_name}.keras'
        try:
            roi_model = keras.models.load_model(model_path)
        except Exception as e:
            raise FileNotFoundError(f"Model file '{model_path}' not found.") from e

        # Predict peak regions using the deep learning model
        predictions, _ = filter_predictions(
            signals=array,
            model=roi_model,
            n_samples=self.n_samples,
            threshold=self.uncertainty
        )

        # Ensure predictions are at least 2D for consistency
        predictions = np.atleast_2d(predictions)

        # Extract middle indices of detected peak regions
        indices = find_middle_indices(
            ROIs=predictions,
            pad_width=self.max_number_of_peaks,
            fill_value=self.padding_value
        )

        return indices
