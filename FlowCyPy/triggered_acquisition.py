import numpy as np
import pandas as pd
from FlowCyPy import units
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
        _digital_signal = self.digital

        dataframes = []

        for _, digital_signal in _digital_signal.groupby('Detector'):
            detection_matrix = digital_signal.pint.dequantify().Signal.values.reshape([-1, self.signal_length])
            time_matrix = digital_signal.pint.dequantify().Time.values.reshape([-1, self.signal_length])  # Retain pint units

            peak_indices = peak_detection_func(detection_matrix)

            # Define the number of segments and peaks
            num_segments, num_peaks = peak_indices.shape

            # Create MultiIndex tuples
            segment_indices = np.repeat(np.arange(num_segments), num_peaks)
            peak_numbers = np.tile(np.arange(1, num_peaks + 1), num_segments)

            multi_index = pd.MultiIndex.from_tuples(zip(segment_indices, peak_numbers), names=["Segment", "Peak_Number"])

            # Flatten the peak indices array for values
            flattened_peak_indices = peak_indices.ravel()

            # Create the MultiIndex DataFrame
            df_multi_index = pd.DataFrame({"Peak_Index": flattened_peak_indices}, index=multi_index)

            # Remove rows where Peak_Index is -1 (since -1 represents missing peaks)
            df_multi_index = df_multi_index[df_multi_index["Peak_Index"] != -1]

            # Extract valid peak indices from the MultiIndex DataFrame
            peak_indices_valid = df_multi_index["Peak_Index"].values.astype(int)

            # Retrieve the corresponding peak heights from detection_matrix
            peak_heights_valid = []
            peak_times_valid = []
            for (segment_id, peak_number), indices in zip(df_multi_index.index, df_multi_index.Peak_Index):
                heights = np.take(detection_matrix[segment_id], indices)
                times = np.take(time_matrix[segment_id], indices)

                peak_heights_valid.append(heights)
                peak_times_valid.append(times)

            # Assign extracted values to the DataFrame
            df_multi_index["Height"] = pint_pandas.PintArray(peak_heights_valid, digital_signal.Signal.values.units)
            df_multi_index["Time"] = pint_pandas.PintArray(peak_times_valid, digital_signal.Time.values.units)

            dataframes.append(df_multi_index)

        output = pd.concat(dataframes, keys=_digital_signal.index.get_level_values('Detector').unique(), names=['Detector'])

        # # Keep only the Peak_Number with the highest Height per (Detector, Segment)
        output = (
            output.pint.dequantify()
            .groupby(level=["Detector", "Segment"], group_keys=False).apply(lambda g: g.loc[g["Height"].idxmax()])
            .reset_index(level=["Peak_Number"], drop=True)
            .pint.quantify()
        )

        return dataframe_subclass.PeakDataFrame(output)

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
