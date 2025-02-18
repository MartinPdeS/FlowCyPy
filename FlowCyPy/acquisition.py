import warnings
import pandas as pd
from FlowCyPy import units
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.dataframe_subclass import TriggeredAcquisitionDataFrame
from FlowCyPy.binary import Interface
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
        # Ensure the trigger detector exists
        if trigger_detector_name not in self.signal.index.get_level_values('Detector').unique():
            raise ValueError(f"Detector '{trigger_detector_name}' not found in dataset.")

        # Convert threshold to plain numeric value
        threshold_value = threshold.to(self.signal['Signal'].pint.units).magnitude

        # Prepare detector-specific signal & time mappings for C++ function
        detectors_name = self.signal.index.get_level_values('Detector').unique()
        signal_units = self.signal.xs(detectors_name[0])['Signal'].pint.units
        time_units = self.signal.xs(detectors_name[0])['Time'].pint.units

        signal_map = {det: self.signal.xs(det)['Signal'].pint.to(signal_units).pint.magnitude for det in detectors_name}
        time_map = {det: self.signal.xs(det)['Time'].pint.to(time_units).pint.magnitude for det in detectors_name}

        # Call the C++ function for fast triggering detection
        times, signals, detectors, segment_ids = Interface.run_triggering(
            signal_map, time_map, threshold_value, pre_buffer, post_buffer, max_triggers or -1
        )

        # Convert back to PintArray (restore units)
        times = pint_pandas.PintArray(times, time_units)
        signals = pint_pandas.PintArray(signals, signal_units)

        # If no triggers are found, warn the user and return None
        if len(times) == 0:
            warnings.warn(
                f"No signal met the trigger criteria. Try adjusting the threshold. "
                f"Signal min-max: {self.signal['Signal'].min().to_compact()}, {self.signal['Signal'].max().to_compact()}",
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

        digitized_signal, _ = self.cytometer.signal_digitizer.capture_signal(triggered_signal['Signal'])
        digitized_signal = pint_pandas.PintArray(
            digitized_signal,
            units.bit_bins
        )

        triggered_signal['DigitizedSignal'] = digitized_signal

        # Create a specialized DataFrame class
        triggered_signal = TriggeredAcquisitionDataFrame(triggered_signal)

        # Copy metadata attributes
        triggered_signal.attrs['bit_depth'] = self.signal.attrs.get('bit_depth', None)
        triggered_signal.attrs['saturation_levels'] = self.signal.attrs.get('saturation_levels', None)
        triggered_signal.attrs['scatterer_dataframe'] = self.signal.attrs.get('scatterer_dataframe', None)
        triggered_signal.attrs['threshold'] = {'detector': trigger_detector_name, 'value': threshold}

        # Wrap inside a TriggeredAcquisitions object
        triggered_acquisition = TriggeredAcquisitions(parent=self, dataframe=triggered_signal)
        triggered_acquisition.scatterer = self.scatterer

        return triggered_acquisition


