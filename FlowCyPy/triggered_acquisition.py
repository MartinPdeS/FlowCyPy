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
        in a MultiIndex DataFrame with original units restored.

        The custom peak detection function must accept a 2D NumPy array of shape (num_segments, signal_length)
        and return a dictionary with the following key:
            - "peak_index": 2D array (num_segments, num_peaks) of detected peak indices.
        Optionally, the dictionary may also contain:
            - "width": 2D array (num_segments, num_peaks) of computed peak widths.
            - "area": 2D array (num_segments, num_peaks) of computed peak areas.

        The resulting DataFrame uses a MultiIndex (Detector, Segment, Peak_Number) and contains the following columns:
            - "Peak_Index", "Time", "Height"
        and, if computed, "Width" and "Area".

        Parameters
        ----------
        peak_detection_func : function
            A function that takes a 2D NumPy array (num_segments, signal_length) and returns a dictionary
            with peak metrics.

        Returns
        -------
        PeakDataFrame
            A MultiIndex DataFrame (Detector, Segment, Peak_Number) with the computed metrics and original units restored.
        """
        digital_signal = self.digital
        df_list = []

        for detector, group in digital_signal.groupby('Detector'):
            # Dequantify and reshape signal and time matrices.
            signal_matrix = group.pint.dequantify().Signal.values.reshape([-1, self.signal_length])
            time_matrix = group.pint.dequantify().Time.values.reshape([-1, self.signal_length])

            # Run the custom peak detection function.
            peaks = peak_detection_func(signal_matrix)
            num_segments, num_peaks = peaks["peak_index"].shape

            # Build a MultiIndex for (Segment, Peak_Number)
            segments = np.repeat(np.arange(num_segments), num_peaks)
            peak_numbers = np.tile(np.arange(1, num_peaks + 1), num_segments)
            multi_index = pd.MultiIndex.from_tuples(zip(segments, peak_numbers), names=["Segment", "Peak_Number"])

            # Flatten the peak indices.
            flat_peak_idx = peaks["peak_index"].ravel()

            # Create the DataFrame with mandatory column "Peak_Index"
            df = pd.DataFrame({"Peak_Index": flat_peak_idx}, index=multi_index)

            # Conditionally add "Width" and "Area" if they exist in peaks.
            if "width" in peaks:
                flat_width = peaks["width"].ravel()
                df["Width"] = flat_width
            if "area" in peaks:
                flat_area = peaks["area"].ravel()
                df["Area"] = flat_area

            # Remove rows where Peak_Index is -1 (invalid/missing peaks).
            df = df[df["Peak_Index"] != -1]

            # Extract corresponding peak heights and times.
            peak_heights = []
            peak_times = []
            for (segment, _), idx in df["Peak_Index"].items():
                idx = int(idx)
                peak_heights.append(np.take(signal_matrix[segment], idx))
                peak_times.append(np.take(time_matrix[segment], idx))
            df["Height"] = pint_pandas.PintArray(peak_heights, group.Signal.values.units)
            df["Time"] = pint_pandas.PintArray(peak_times, group.Time.values.units)

            # Record the detector name.
            df["Detector"] = detector
            df.reset_index(inplace=True)
            df.set_index(["Detector", "Segment", "Peak_Number"], inplace=True)

            df_list.append(df)

        # Concatenate results from all detectors.
        combined_df = pd.concat(df_list, axis=0)

        # Optionally, keep only the peak with the highest Height per (Detector, Segment).
        final_df = (
            combined_df.pint.dequantify()
            .groupby(level=["Detector", "Segment"], group_keys=False)
            .apply(lambda g: g.loc[g["Height"].idxmax()])
            .reset_index(level=["Peak_Number"], drop=True)
            .pint.quantify()
        )

        return dataframe_subclass.PeakDataFrame(final_df)



    # def detect_peaks(self, peak_detection_func) -> pd.DataFrame:
    #     """
    #     Detects peaks for each segment using a custom peak detection function and stores results
    #     in a MultiIndex DataFrame with the original units restored.

    #     Parameters
    #     ----------
    #     peak_detection_func : function
    #         A function that takes in a 2D NumPy array of shape (num_arrays, length_of_array)
    #         and returns a 2D NumPy array (num_arrays, pad_width) containing detected peak indices.

    #     Returns
    #     -------
    #     PeakDataFrame
    #         MultiIndex DataFrame with index (Detector, SegmentID, PeakNumber)
    #         and columns ['Time', 'Height'], including their original units.
    #     """
    #     _digital_signal = self.digital

    #     dataframes = []

    #     for _, digital_signal in _digital_signal.groupby('Detector'):
    #         detection_matrix = digital_signal.pint.dequantify().Signal.values.reshape([-1, self.signal_length])
    #         time_matrix = digital_signal.pint.dequantify().Time.values.reshape([-1, self.signal_length])  # Retain pint units

    #         peak_dict = peak_detection_func(detection_matrix)

    #         # Define the number of segments and peaks
    #         num_segments, num_peaks = peak_dict['peak_index'].shape

    #         # Create MultiIndex tuples
    #         segment_indices = np.repeat(np.arange(num_segments), num_peaks)
    #         peak_numbers = np.tile(np.arange(1, num_peaks + 1), num_segments)

    #         multi_index = pd.MultiIndex.from_tuples(zip(segment_indices, peak_numbers), names=["Segment", "Peak_Number"])

    #         # Flatten the peak indices array for values
    #         flattened_peak_indices = peak_dict['peak_index'].ravel()

    #         # Create the MultiIndex DataFrame
    #         df_multi_index = pd.DataFrame({"Peak_Index": flattened_peak_indices}, index=multi_index)

    #         # Remove rows where Peak_Index is -1 (since -1 represents missing peaks)
    #         df_multi_index = df_multi_index[df_multi_index["Peak_Index"] != -1]

    #         # Extract valid peak indices from the MultiIndex DataFrame
    #         peak_indices_valid = df_multi_index["Peak_Index"].values.astype(int)

    #         # Retrieve the corresponding peak heights from detection_matrix
    #         peak_heights_valid = []
    #         peak_times_valid = []
    #         for (segment_id, peak_number), indices in zip(df_multi_index.index, df_multi_index.Peak_Index):
    #             heights = np.take(detection_matrix[segment_id], indices)
    #             times = np.take(time_matrix[segment_id], indices)

    #             peak_heights_valid.append(heights)
    #             peak_times_valid.append(times)

    #         # Assign extracted values to the DataFrame
    #         df_multi_index["Height"] = pint_pandas.PintArray(peak_heights_valid, digital_signal.Signal.values.units)
    #         df_multi_index["Time"] = pint_pandas.PintArray(peak_times_valid, digital_signal.Time.values.units)

    #         dataframes.append(df_multi_index)

    #     output = pd.concat(dataframes, keys=_digital_signal.index.get_level_values('Detector').unique(), names=['Detector'])

    #     # # Keep only the Peak_Number with the highest Height per (Detector, Segment)
    #     output = (
    #         output.pint.dequantify()
    #         .groupby(level=["Detector", "Segment"], group_keys=False).apply(lambda g: g.loc[g["Height"].idxmax()])
    #         .reset_index(level=["Peak_Number"], drop=True)
    #         .pint.quantify()
    #     )

    #     return dataframe_subclass.PeakDataFrame(output)

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
