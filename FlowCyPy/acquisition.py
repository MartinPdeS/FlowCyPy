import warnings
import pandas as pd
import numpy as np
from FlowCyPy import units
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.dataframe_subclass import TriggeredAcquisitionDataFrame
from FlowCyPy.binary.Interface import get_trigger_indices

class Acquisition:
    """
    Represents a flow cytometry experiment, including runtime, dataframes, logging, and visualization.

    Attributes
    ----------
    run_time : units.second
        Total runtime of the experiment.
    scatterer_dataframe : pd.DataFrame
        DataFrame containing scatterer data, indexed by population and time.
    detector_dataframe : pd.DataFrame
        DataFrame containing detector signal data, indexed by detector and time.
    """

    def __init__(self, run_time: units.second, cytometer: object, scatterer_dataframe: pd.DataFrame, detector_dataframe: pd.DataFrame):
        """
        Initializes the Experiment instance.

        Parameters
        ----------
        run_time : Quantity
            Total runtime of the experiment.
        scatterer_dataframe : pd.DataFrame
            DataFrame with scatterer data.
        detector_dataframe : pd.DataFrame
            DataFrame with detector signal data.
        """
        self.cytometer = cytometer
        self.signal = detector_dataframe
        self.scatterer = scatterer_dataframe
        self.run_time = run_time

    @property
    def n_detectors(self) -> int:
        return len(self.signal.index.get_level_values('Detector').unique())

    def run_triggering(self,
            threshold: units.Quantity,
            trigger_detector_name: str,
            pre_buffer: int = 64,
            post_buffer: int = 64,
            max_triggers: int = None) -> TriggeredAcquisitions:
        """
        Execute triggered acquisition analysis for signal data.

        This method identifies segments of signal data based on a triggering threshold
        and specified detector. It extracts segments of interest from the signal,
        including a pre-trigger buffer and post-trigger buffer.

        Parameters
        ----------
        threshold : units.Quantity
            The threshold value for triggering. Only signal values exceeding this threshold
            will be considered as trigger events.
        trigger_detector_name : str
            The name of the detector used for triggering. This determines which detector's
            signal is analyzed for trigger events.
        pre_buffer : int, optional
            The number of points to include before the trigger point in each segment.
            Default is 64.
        post_buffer : int, optional
            The number of points to include after the trigger point in each segment.
            Default is 64.
        max_triggers : int, optional
            The maximum number of triggers to process. If None, all triggers will be processed.
            Default is None.

        Raises
        ------
        ValueError
            If the specified `trigger_detector_name` is not found in the dataset.

        Warnings
        --------
        UserWarning
            If no triggers are detected for the specified threshold, the method raises a warning
            indicating that no signals met the criteria.

        Notes
        -----
        - The peak detection function `self.detect_peaks` is automatically called at the end of this method to analyze triggered segments.
        """
        start_indices, end_indices = get_trigger_indices(
            threshold, trigger_detector_name, pre_buffer, post_buffer
        )

        if max_triggers is not None:
            start_indices = start_indices[:max_triggers]
            end_indices = end_indices[:max_triggers]

        segments = []
        for detector_name in self.signal.index.get_level_values('Detector').unique():
            detector_data = self.signal.xs(detector_name)
            time, digitized, signal = detector_data['Time'], detector_data['DigitizedSignal'],  detector_data['Signal']


            for idx, (start, end) in enumerate(zip(start_indices, end_indices)):

                segment = pd.DataFrame({
                    'Time': time[start:end + 1],
                    'DigitizedSignal': digitized[start:end + 1],
                    'Signal': signal[start:end + 1],
                    'Detector': detector_name,
                    'SegmentID': idx
                })
                segments.append(segment)

        if len(segments) !=0:
            triggered_signal = TriggeredAcquisitionDataFrame(pd.concat(segments).set_index(['Detector', 'SegmentID']))
            triggered_signal.attrs['bit_depth'] = self.signal.attrs['bit_depth']
            triggered_signal.attrs['saturation_levels'] = self.signal.attrs['saturation_levels']
            triggered_signal.attrs['scatterer_dataframe'] = self.signal.attrs['scatterer_dataframe']
            triggered_signal.attrs['threshold'] = {'detector': trigger_detector_name, 'value': threshold}

            triggered_acquisition = TriggeredAcquisitions(parent=self, dataframe=triggered_signal)
            triggered_acquisition.scatterer = self.scatterer

            return triggered_acquisition
        else:
            warnings.warn(
                f"No signal were triggered during the run time, try changing the threshold. Signal min-max value is: {self.signal['Signal'].min().to_compact()}, {self.signal['Signal'].max().to_compact()}",
                UserWarning
            )

