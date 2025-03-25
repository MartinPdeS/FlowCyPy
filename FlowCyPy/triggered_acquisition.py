import numpy as np
import pandas as pd
from FlowCyPy import units
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

    def detect_peaks(self, peak_algorithm) -> None:
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
        multi_index = pd.MultiIndex.from_product(
            (self.analog.index.get_level_values('Detector').unique(),
            self.analog.index.get_level_values('SegmentID').unique(),
            range(peak_algorithm.max_number_of_peaks)),
            names=["Detector", "SegmentID", "PeakID"]
        )

        df = pd.DataFrame(columns=['Height', 'Width', 'Area'], index=multi_index)

        for group_name, group in self.analog.groupby(['Detector', 'SegmentID']):
            signal = group.pint.dequantify().Signal.values.squeeze()
            time  = group.pint.dequantify().Time.values.squeeze()

            peaks_dict = peak_algorithm(signal)

            for key, value in peaks_dict.items():
                df.loc[group_name, key] = value

            df.loc[group_name, 'Time'] = np.take(time, peaks_dict['Index'])

        return dataframe_subclass.PeakDataFrame(df)


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
