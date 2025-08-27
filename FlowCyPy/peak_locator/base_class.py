from abc import ABC

import pandas as pd

from FlowCyPy.sub_frames.peaks import PeakDataFrame


class BasePeakLocator(ABC):
    """
    A base class to handle common functionality for peak detection,
    including area calculation under peaks.
    """

    def run(self, signal_dataframe: pd.DataFrame) -> PeakDataFrame:
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
        detector_names = signal_dataframe.detector_names
        segment_ids = signal_dataframe.index.get_level_values("SegmentID").unique()

        multi_index = pd.MultiIndex.from_product(
            (detector_names, segment_ids, range(self.max_number_of_peaks)),
            names=["Detector", "SegmentID", "PeakID"],
        )

        df = pd.DataFrame(columns=["Height", "Width", "Area"], index=multi_index)

        df.sort_index(inplace=True)

        for detector_name in detector_names:
            for segment_id, group in signal_dataframe[detector_name].groupby(
                "SegmentID"
            ):
                signal = group.values.quantity.magnitude

                peak_dict = self(signal)

                for key, value in peak_dict.items():
                    df.loc[(detector_name, segment_id), key] = value

        return PeakDataFrame(df)
