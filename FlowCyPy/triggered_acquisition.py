import pandas as pd
from FlowCyPy import units
from scipy.signal import find_peaks
from FlowCyPy.filters import bessel_lowpass_filter, dc_highpass_filter
from FlowCyPy import dataframe_subclass
from FlowCyPy.helper import validate_units
from FlowCyPy import dataframe_subclass
import pint_pandas

class TriggeredAcquisitions:
    """
    A class for handling and processing triggered acquisition data,
    including peak detection and signal filtering.
    """

    def __init__(self, parent, dataframe: pd.DataFrame):
        """
        Initializes the TriggeredAcquisitions instance.

        Parameters
        ----------
        parent : object
            Parent object containing cytometer and detector metadata.
        dataframe : pd.DataFrame
            Dataframe containing the acquired signals.
        """
        self.analog = dataframe.sort_index()
        self.parent = parent

    @property
    def signal_digitizer(self) -> object:
        return self.parent.signal_digitizer

    def get_detector(self, name: str):
        """
        Retrieves a detector instance by name.

        Parameters
        ----------
        name : str
            Name of the detector to retrieve.

        Returns
        -------
        object or None
            Detector object if found, otherwise None.
        """
        for detector in self.parent.cytometer.detectors:
            if detector.name == name:
                return detector

    def detect_peaks(self, peak_detection_func) -> None:
        """
        Detects peaks for each segment using a custom peak detection function and stores results
        in a MultiIndex DataFrame with the original units restored.

        Parameters
        ----------
        peak_detection_func : function
            A function that takes in a 2D NumPy array of shape (num_arrays, length_of_array)
            and returns a 2D NumPy array (num_arrays, pad_width) containing detected peak indices.

        Returns
        -------
        PeakDataFrame
            MultiIndex DataFrame with index (Detector, SegmentID, PeakNumber)
            and columns ['Time', 'Height'], including their original units.
        """
        # Extract detector names and segment IDs
        detector_segment_groups = self.digital.groupby(level=['Detector', 'SegmentID'])

        # Get the original units from the 'Signal' and 'Time' columns
        signal_units = self.digital['Signal'].pint.units
        time_units = self.digital['Time'].pint.units

        peak_entries = []

        for (detector_name, segment_id), group in detector_segment_groups:
            # Convert signal and time to NumPy arrays without units
            signal_array = group['Signal'].pint.magnitude.to_numpy().reshape(1, -1)  # Extract numerical values
            time_array = group['Time'].pint.magnitude.to_numpy().reshape(1, -1)  # Extract numerical values

            # Apply the peak detection function
            detected_peak_indices = peak_detection_func(signal_array)  # Shape: (1, pad_width)

            # Flatten indices and remove NaNs
            valid_indices = detected_peak_indices.flatten()
            valid_indices = valid_indices[~np.isnan(valid_indices)].astype(int)

            # Extract signal heights and time points at detected peak indices
            peak_heights = signal_array[0, valid_indices]  # Numeric values
            peak_times = time_array[0, valid_indices]  # Numeric values

            # Store results in a structured format
            for peak_number, (peak_time, peak_height) in enumerate(zip(peak_times, peak_heights)):
                peak_entries.append([detector_name, segment_id, peak_number, peak_time, peak_height])

        # Convert peak entries to a MultiIndex DataFrame
        peaks = dataframe_subclass.PeakDataFrame(peak_entries, columns=['Detector', 'SegmentID', 'PeakNumber', 'Time', 'Height'])

        # Correct way to restore units
        peaks['Time'] = pint_pandas.PintArray(peaks['Time'].to_numpy(), dtype=time_units)
        peaks['Height'] = pint_pandas.PintArray(peaks['Height'].to_numpy(), dtype=signal_units)

        # Set the MultiIndex
        peaks.set_index(['Detector', 'SegmentID', 'PeakNumber'], inplace=True)

        return peaks



    def _apply_lowpass_filter(self, cutoff_freq: units.Quantity, order: int = 4) -> None:
        """
        Applies a Bessel low-pass filter to the signal data in-place.

        Parameters
        ----------
        cutoff_freq : units.Quantity
            The cutoff frequency for the low-pass filter (must have frequency units).
        order : int, optional
            The order of the Bessel filter, default is 4.

        Raises
        ------
        ValueError
            If cutoff frequency is missing or exceeds Nyquist frequency.
        TypeError
            If signal data is not stored as a PintArray.
        """
        if cutoff_freq is None:
            raise ValueError("Cutoff frequency must be specified for low-pass filtering.")

        # Get sampling frequency and ensure it's in Hertz
        fs = self.parent.cytometer.signal_digitizer.sampling_freq.to("hertz")
        nyquist_freq = fs / 2

        # Validate cutoff frequency
        if cutoff_freq.to("hertz") >= nyquist_freq:
            raise ValueError(f"Cutoff frequency ({cutoff_freq}) must be below the Nyquist frequency ({nyquist_freq}).")

        # Ensure the signal column is a PintArray
        if not isinstance(self.analog["Signal"].array, pint_pandas.PintArray):
            raise TypeError("Expected 'Signal' to be a PintArray, but got a different type.")

        # Iterate through each detector-segment pair and apply filtering
        for (detector, segment_id), segment_data in self.analog.groupby(level=['Detector', 'SegmentID']):
            filtered_values = bessel_lowpass_filter(
                signal=segment_data["Signal"].pint.quantity.magnitude,
                cutoff=cutoff_freq,
                sampling_rate=fs,
                order=order
            )

            self.analog.loc[(detector, segment_id), "Signal"] = filtered_values

    def _apply_highpass_filter(self, cutoff_freq: units.Quantity, order: int = 4) -> None:
        """
        Applies a DC high-pass filter to the signal data in-place.

        Parameters
        ----------
        cutoff_freq : units.Quantity
            The cutoff frequency for the high-pass filter (must have frequency units).
        order : int, optional
            The order of the high-pass filter, default is 4.

        Raises
        ------
        ValueError
            If cutoff frequency is missing or exceeds Nyquist frequency.
        TypeError
            If signal data is not stored as a PintArray.
        """
        if cutoff_freq is None:
            raise ValueError("Cutoff frequency must be specified for high-pass filtering.")

        # Get sampling frequency and ensure it's in Hertz
        fs = self.parent.cytometer.signal_digitizer.sampling_freq.to("hertz")
        nyquist_freq = fs / 2

        # Validate cutoff frequency
        if cutoff_freq.to("hertz") >= nyquist_freq:
            raise ValueError(f"Cutoff frequency ({cutoff_freq}) must be below the Nyquist frequency ({nyquist_freq}).")

        # Ensure the signal column is a PintArray
        if not isinstance(self.analog["Signal"].array, pint_pandas.PintArray):
            raise TypeError("Expected 'Signal' to be a PintArray, but got a different type.")

        # Iterate through each detector-segment pair and apply filtering
        for (detector, segment_id), segment_data in self.analog.groupby(level=['Detector', 'SegmentID']):
            filtered_values = dc_highpass_filter(
                signal=segment_data["Signal"].pint.quantity.magnitude,
                cutoff=cutoff_freq,
                sampling_rate=fs,
                order=order
            )

            # Ensure values remain as a PintArray and keep original units
            self.analog.loc[(detector, segment_id), "Signal"] = filtered_values

    def apply_baseline_restauration(self) -> None:
        """
        Restores the baseline of the signal by subtracting the minimum value
        for both 'Signal' and 'DigitizedSignal', ensuring zero-based alignment.

        This operation is performed in-place, preserving the original units.
        """
        if self.analog.empty:
            return  # Avoid unnecessary computation if DataFrame is empty

        # Compute the per-group (detector, segment) minimum for vectorized operations
        min_signal = self.analog.groupby(level=['Detector', 'SegmentID'])["Signal"].transform("min")

        # Apply baseline restoration in a single vectorized operation
        self.analog["Signal"] -= min_signal

    @validate_units(low_cutoff=units.hertz, high_cutoff=units.hertz)
    def apply_filters(self, lowpass_cutoff: units.Quantity = None, highpass_cutoff: units.Quantity = None) -> None:
        """
        Applies low-pass and/or high-pass filters to the signal data in-place.

        Parameters
        ----------
        low_cutoff : units.Quantity, optional
            The cutoff frequency for the low-pass filter. If None, no low-pass filtering is applied.
        high_cutoff : units.Quantity, optional
            The cutoff frequency for the high-pass filter. If None, no high-pass filtering is applied.
        """
        if lowpass_cutoff is not None:
            self._apply_lowpass_filter(lowpass_cutoff)
        if highpass_cutoff is not None:
            self._apply_highpass_filter(highpass_cutoff)

    @property
    def digital(self) -> pd.DataFrame:
        dataframe = dataframe_subclass.TriggeredDigitalAcquisitionDataFrame(
            index=self.analog.index,
            data=dict(Time=self.analog.Time)
        )

        dataframe.attrs['saturation_levels'] = dict()
        dataframe.attrs['scatterer_dataframe'] = self.analog.attrs.get('scatterer_dataframe', None)

        for detector_name, group in self.analog.groupby('Detector'):
            digitized_signal, _ = self.signal_digitizer.capture_signal(signal=group['Signal'])

            dataframe.attrs['saturation_levels'][detector_name] = [0, self.signal_digitizer._bit_depth]

            # Ensure the DataFrame index is sorted before accessing elements
            dataframe = dataframe.sort_index()

            # Now perform the assignment safely
            dataframe.loc[detector_name, 'Signal'] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return dataframe


import numpy as np
from scipy.signal import find_peaks

def scipy_peak_detector(signal_matrix, pad_width=5, height=None, distance=1, width=None, prominence=None):
    """
    Uses `scipy.signal.find_peaks` to detect peaks in a 2D signal matrix.

    Parameters:
    - signal_matrix: np.ndarray of shape (num_arrays, length_of_array) with signal data.
    - pad_width: int, number of peaks to return per row (default: 5).
    - height, distance, width, prominence: Passed to `find_peaks` for peak selection.

    Returns:
    - np.ndarray of shape (num_arrays, pad_width) with detected peak indices.
    """
    num_rows = signal_matrix.shape[0]

    # Initialize padded output array
    padded_output = np.full((num_rows, pad_width), np.nan)  # Default to NaN for missing values

    # Apply `find_peaks` to each row
    for i in range(num_rows):
        peaks, _ = find_peaks(signal_matrix[i], height=height, distance=distance, width=width, prominence=prominence)

        num_found = len(peaks)
        padded_output[i, :min(num_found, pad_width)] = peaks[:pad_width]  # Assign valid peaks

    return padded_output