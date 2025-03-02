from typing import List
import warnings
import pandas as pd
from FlowCyPy import units
from FlowCyPy import dataframe_subclass
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.binary import triggering_system
import pint_pandas

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
        self.analog = detector_dataframe
        self.scatterer = scatterer_dataframe
        self.run_time = run_time

    @property
    def n_detectors(self) -> int:
        return len(self.detector_names)

    @property
    def detector_names(self) -> List[str]:
        return self.analog.index.get_level_values('Detector').unique()

    @property
    def signal_digitizer(self) -> object:
        return self.cytometer.signal_digitizer

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
        # Ensure the trigger detector exists
        if trigger_detector_name not in self.detector_names:
            raise ValueError(f"Detector '{trigger_detector_name}' not found in dataset.")

        signal_length = pre_buffer + post_buffer

        # Convert threshold to plain numeric value
        threshold_value = threshold.to(self.analog['Signal'].pint.units).magnitude

        # Prepare detector-specific signal & time mappings for C++ function
        signal_units = self.analog.xs(self.detector_names[0])['Signal'].pint.units
        time_units = self.analog.xs(self.detector_names[0])['Time'].pint.units

        signal_map = {det: self.analog.xs(det)['Signal'].pint.to(signal_units).pint.magnitude.to_numpy(copy=False) for det in self.detector_names}
        time_map = {det: self.analog.xs(det)['Time'].pint.to(time_units).pint.magnitude.to_numpy(copy=False) for det in self.detector_names}

        # Call the C++ function for fast triggering detection
        times, signals, detectors, segment_ids = triggering_system.run(
            signal_map=signal_map,
            time_map=time_map,
            trigger_detector_name=trigger_detector_name,
            threshold=threshold_value,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers or -1
        )

        # Convert back to PintArray (restore units)
        times = pint_pandas.PintArray(times, time_units)
        signals = pint_pandas.PintArray(signals, signal_units)

        # If no triggers are found, warn the user and return None
        if len(times) == 0:
            warnings.warn(
                f"No signal met the trigger criteria. Try adjusting the threshold. "
                f"Signal min-max: {self.analog['Signal'].min().to_compact()}, {self.analog['Signal'].max().to_compact()}",
                UserWarning
            )
            return None

        # Convert NumPy arrays to Pandas DataFrame
        triggered_signal = pd.DataFrame({
            "Time": times,
            "Signal": signals,
            "Detector": detectors,
            "SegmentID": segment_ids
        }).set_index(['Detector', 'SegmentID'])

        # Create a specialized DataFrame class
        triggered_signal = dataframe_subclass.TriggeredAnalogAcquisitionDataFrame(triggered_signal)

        # Copy metadata attributes
        triggered_signal.attrs['bit_depth'] = self.analog.attrs.get('bit_depth', None)
        triggered_signal.attrs['saturation_levels'] = self.analog.attrs.get('saturation_levels', None)
        triggered_signal.attrs['scatterer_dataframe'] = self.analog.attrs.get('scatterer_dataframe', None)
        triggered_signal.attrs['threshold'] = {'detector': trigger_detector_name, 'value': threshold}

        # Wrap inside a TriggeredAcquisitions object
        triggered_acquisition = TriggeredAcquisitions(parent=self, dataframe=triggered_signal)
        triggered_acquisition.scatterer = self.scatterer
        triggered_acquisition.signal_length = signal_length

        return triggered_acquisition


    @property
    def digital(self) -> pd.DataFrame:
        dataframe = dataframe_subclass.DigitizedAcquisitionDataFrame(
            index=self.analog.index,
            data=dict(Time=self.analog.Time)
        )

        dataframe.attrs['saturation_levels'] = dict()
        dataframe.attrs['scatterer_dataframe'] = self.analog.attrs.get('scatterer_dataframe', None)

        for detector_name, group in self.analog.groupby('Detector'):
            digitized_signal, _ = self.signal_digitizer.capture_signal(signal=group['Signal'])

            dataframe.attrs['saturation_levels'][detector_name] = [0, self.signal_digitizer.bit_depth]

            dataframe.loc[detector_name, 'Signal'] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return dataframe