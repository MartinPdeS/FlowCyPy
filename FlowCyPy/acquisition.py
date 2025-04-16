from typing import List
import warnings
import pandas as pd
from FlowCyPy import units
from FlowCyPy.dataframe_subclass import AcquisitionDataFrame, TriggerDataFrame
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.binary.interface_triggering_system import TriggeringSystem # type: ignore
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
        return [element for element in self.analog.columns if element != 'Time']

    @property
    def signal_digitizer(self) -> object:
        return self.cytometer.signal_digitizer

    def run_triggering(self,
            threshold: units.Quantity,
            trigger_detector_name: str,
            pre_buffer: int = 64,
            post_buffer: int = 64,
            max_triggers: int = -1,
            min_window_duration: units.Quantity = None,
            lower_threshold: units.Quantity = None,
            debounce_enabled: bool = True,
            scheme: str = 'dynamic') -> TriggerDataFrame:
        """
        Execute triggered acquisition analysis on signal data.

        This method processes the analog signal data by identifying segments where the
        signal exceeds a given threshold using a designated detector. It then extracts
        these segments with additional pre- and post-trigger buffers. The analysis can
        operate in either a "fixed-window" or "dynamic" mode depending on the `scheme`
        parameter, providing flexibility for different signal characteristics.

        Parameters
        ----------
        threshold : units.Quantity
            The signal threshold value. Only signal values exceeding this threshold are
            considered as trigger events.
        trigger_detector_name : str
            The name of the detector whose signal is used to detect trigger events.
        pre_buffer : int, optional
            The number of data points to include before the trigger event in each
            extracted segment. Default is 64.
        post_buffer : int, optional
            The number of data points to include after the trigger event in each
            extracted segment. Default is 64.
        max_triggers : int, optional
            The maximum number of trigger events to process. If set to -1, all detected
            trigger events are processed. Default is -1.
        min_window_duration : units.Quantity, optional
            The minimum duration for which the signal must remain above the threshold
            to be considered a valid trigger. This duration is converted into a number of
            samples based on the sampling rate. If set to None, no minimum duration check is applied.
        lower_threshold : units.Quantity, optional
            An optional lower threshold for ending a trigger event. If not provided, the
            same value as `threshold` is used.
        debounce_enabled : bool, optional
            If True, the algorithm requires that the signal remains above the threshold
            for at least `min_window_duration` samples (if specified) to validate a trigger.
            If False, this debounce check is skipped. Default is True.
        scheme : str, optional
            The triggering scheme to use. Options include:
            - 'fixed-window': Uses fixed pre_buffer and post_buffer lengths.
            - 'dynamic': Uses a dynamic window that extends until the signal falls
                below the threshold (or lower_threshold if specified).
            Default is 'dynamic'.

        Returns
        -------
        TriggeredAcquisitions
            An object that contains the extracted signal segments, their corresponding
            time values, detector names, and segment IDs packaged in a specialized
            DataFrame.

        Raises
        ------
        ValueError
            If the specified `trigger_detector_name` is not found in the dataset.
        RuntimeError
            If no time array is provided (via add_time) and none is available for the
            trigger detector.

        Warns
        -----
        UserWarning
            If no trigger events are detected (i.e., no signal segments meet the threshold
            criteria), a warning is issued and None is returned.

        Notes
        -----
        - In dynamic mode, each extracted segment includes:
            pre_buffer points before the trigger event,
            all points where the signal is above the threshold (or remains above lower_threshold),
            and post_buffer points after the signal falls below the threshold.
        This results in a segment length of pre_buffer + width + post_buffer - 1.
        - The method converts input signal and time values from physical units to raw
        numerical values based on their respective units before passing them to the C++
        triggering algorithm for fast processing. After processing, the numerical arrays
        are converted back into PintArray objects with the original units restored.
        - This method automatically invokes additional processing (e.g., peak detection)
        on the triggered segments via `self.detect_peaks` (if applicable) after the
        acquisition analysis.
        """
        # Ensure the trigger detector exists
        if trigger_detector_name not in self.detector_names:
            raise ValueError(f"Detector '{trigger_detector_name}' not found in dataset.")

        # Prepare detector-specific signal & time mappings for C++ function
        self.analog['Time'] = self.analog['Time'].pint.to('second')
        for detector_name in self.detector_names:
            self.analog[detector_name] = self.analog[detector_name].pint.to('volt')

        lower_threshold = (lower_threshold or threshold).to('volt').magnitude

        min_window_duration = int(
            (min_window_duration * self.signal_digitizer.sampling_rate).to('dimensionless').magnitude if min_window_duration is not None else -1
        )

        # Call the C++ function for fast triggering detection
        triggering_system = TriggeringSystem(
            trigger_detector_name=trigger_detector_name,
            threshold=threshold.to('volt').magnitude,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
            lower_threshold=lower_threshold,
            min_window_duration=min_window_duration,
            debounce_enabled=debounce_enabled
        )

        triggering_system.add_time(self.analog['Time'].pint.quantity.magnitude)

        for detector_name in self.detector_names:
            signal = self.analog[detector_name].pint.to('volt').values.quantity.magnitude
            triggering_system.add_signal(detector_name, signal)

        triggering_system.run(algorithm=scheme)

        if len(triggering_system.get_signals(trigger_detector_name)) == 0:
            warnings.warn(
                f"No signal met the trigger criteria. Try adjusting the threshold. "
                f"Signal min-max: {self.analog[trigger_detector_name].min().to_compact()}, {self.analog[trigger_detector_name].max().to_compact()}",
                UserWarning
            )

            return None

        df = pd.DataFrame(
            columns=['Time', 'SegmentID', *self.analog.detector_names]
        )

        for d in self.cytometer.detectors:
            df[d.name] = pint_pandas.PintArray(triggering_system.get_signals(d.name), 'volt')

        df['Time'] = pint_pandas.PintArray(triggering_system.get_times(d.name), 'second')
        df['SegmentID'] = triggering_system.get_segments_ID(d.name)

        df = df.set_index('SegmentID')

        # Create a specialized DataFrame class
        df = TriggerDataFrame(df, plot_type='analog')

        # Copy metadata attributes
        df.attrs['bit_depth'] = self.analog.attrs.get('bit_depth', None)
        df.attrs['saturation_levels'] = self.analog.attrs.get('saturation_levels', None)
        df.attrs['scatterer_dataframe'] = self.analog.attrs.get('scatterer_dataframe', None)
        df.attrs['threshold'] = {'detector': trigger_detector_name, 'value': threshold}

        # Wrap inside a TriggeredAcquisitions object
        triggered_acquisition = TriggeredAcquisitions(parent=self, dataframe=df)
        triggered_acquisition.scatterer = self.scatterer

        return triggered_acquisition


    def get_digital_signal(self) -> AcquisitionDataFrame:
        digital_df = pd.DataFrame(
            index=self.analog.index,
            columns=self.analog.columns,
            data=dict(Time=self.analog.Time),
        )

        for detector_name in self.analog.detector_names:
            analog_signal = self.analog[detector_name]
            digitized_signal, _ = self.signal_digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return AcquisitionDataFrame(digital_df, plot_type='digital', scatterer_dataframe=self.scatterer)