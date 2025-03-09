from typing import List
import warnings
import pandas as pd
from FlowCyPy import units
from FlowCyPy import dataframe_subclass
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.binary.triggering_system import TriggeringSystem # type: ignore
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
            max_triggers: int = None,
            scheme: str = 'fixed-window') -> TriggeredAcquisitions:
        """
        Execute triggered acquisition analysis on signal data.

        This method identifies segments of a signal that exceed a specified threshold
        using a designated detector, then extracts those segments with additional
        pre- and post-trigger buffers. The analysis can operate in either "fixed-window"
        or "dynamic" mode based on the `scheme` parameter.

        Parameters
        ----------
        threshold : units.Quantity
            The signal threshold value. Only signal values that exceed this threshold
            are considered as trigger events.
        trigger_detector_name : str
            The name of the detector whose signal is used for detecting trigger events.
        pre_buffer : int, optional
            The number of data points to include before the trigger point in each extracted segment.
            Default is 64.
        post_buffer : int, optional
            The number of data points to include after the trigger point in each extracted segment.
            Default is 64.
        max_triggers : int, optional
            The maximum number of trigger events to process. If set to None, all detected
            trigger events are processed. Default is None.
        scheme : str, optional
            The triggering scheme to use. Use 'fixed-window' for a fixed-length window based on the
            pre_buffer and post_buffer parameters, or 'dynamic' for a window that extends dynamically
            until the signal falls below the threshold. Default is 'fixed-window'.

        Returns
        -------
        TriggeredAcquisitions
            An object containing the extracted signal segments, associated time values,
            detector names, and segment IDs.

        Raises
        ------
        ValueError
            If the specified `trigger_detector_name` is not present in the dataset.

        Warns
        -----
        UserWarning
            If no triggers are detected (i.e., no signal segments meet the threshold criteria),
            a warning is issued and empty arrays are returned.

        Notes
        -----
            - In dynamic mode, the extracted segment includes:
            pre_buffer points before the trigger, all points where the signal is above threshold,
            and post_buffer points after the signal falls below the threshold, yielding a segment length
            of pre_buffer + width + post_buffer - 1.
            - The method automatically invokes `self.detect_peaks` at the end of the analysis to further
            process the triggered segments.
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
        triggering_system = TriggeringSystem(
            scheme=scheme,
            signal_map=signal_map,
            time_map=time_map,
            trigger_detector_name=trigger_detector_name,
            threshold=threshold_value,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers or -1
            )

        times, signals, detectors, segment_ids = triggering_system.run()

        # Convert back to PintArray (restore units)
        times = pint_pandas.PintArray(times, time_units)
        signals = pint_pandas.PintArray(signals, signal_units)

        # If no triggers are found, warn the user and return None
        if len(times) == 0:
            # raise ValueError(
            #     # f"{self.analog['Signal'].pint.to(self.analog['Signal'].max().to_compact().units)}"
            #     # f"{self.analog.Signal.__repr__()}"
            #     f"No signal met the trigger criteria. Try adjusting the threshold. "
            #     f"Signal min-max: {self.analog['Signal'].min().to_compact()}, {self.analog['Signal'].max().to_compact()}",
            # )
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