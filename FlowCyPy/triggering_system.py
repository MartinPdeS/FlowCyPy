# -*- coding: utf-8 -*-

from typing import Optional
import warnings

import numpy as np
import pandas as pd
import pint_pandas

from FlowCyPy import units
from FlowCyPy.sub_frames.acquisition import TriggerDataFrame
from FlowCyPy.binary.interface_triggering_system import FIXEDWINDOW, DYNAMICWINDOW, DOUBLETHRESHOLD


class BaseTrigger:
    def init_data(self, dataframe):
        dataframe.normalize_units(time_units=units.second, signal_units=units.volt)

        # feed time + all detector signals
        self._cpp_add_time(dataframe["Time"].pint.quantity.magnitude)

        for detector_name in dataframe.detector_names:
            self._cpp_add_signal(detector_name, dataframe[detector_name].pint.quantity.magnitude)

    def _parse_threshold(self, threshold: units.Quantity | str, signal_dataframe: pd.DataFrame) -> units.Quantity:
        """
        Parse the threshold value and return it in the correct units.
        If the threshold is a string ending with "sigma", it calculates the threshold
        based on the median and MAD of the signal in the specified trigger detector.
        If the threshold is a Quantity, it returns it directly.

        Raises
        ------
        ValueError
            If the threshold string format is unknown.
        TypeError
            If the threshold is neither a string nor a Quantity.
        """
        if isinstance(threshold, str):
            if threshold.endswith("sigma"):
                number_of_sigma = float(threshold.strip('sigma'))
                signal = signal_dataframe[self.trigger_detector_name].pint.quantity.magnitude
                median_val = np.median(signal)
                mad = np.median(np.abs(signal - median_val))
                sigma_mad = mad / 0.6745
                return (median_val + number_of_sigma * sigma_mad) * signal_dataframe.signal_units
            else:
                raise ValueError(f"Unknown threshold format: {threshold!r}")

        elif isinstance(threshold, units.Quantity):
            return threshold
        else:
            raise TypeError(f"Unsupported threshold type: {type(threshold)}")

    def _assemble_dataframe(self, dataframe: pd.DataFrame) -> TriggerDataFrame:
        """
        Assemble the output DataFrame from the C++ backend results.
        It retrieves the segment IDs, times, and signals for each detector,
        and constructs a tidy DataFrame with the appropriate units.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the trigger windows with segment IDs, times, and signals.
        """

        if len(self.trigger.get_segmented_signal(self.trigger_detector_name)) == 0:
            warnings.warn(f"No signal met the trigger criteria. Try adjusting the threshold. Signal min/max: {dataframe[self.trigger_detector_name].min().to_compact()}, {dataframe[self.trigger_detector_name].max().to_compact()}", UserWarning)
            self._warn_no_hits(dataframe, self.trigger_detector_name)
            return None

        detectors = dataframe.detector_names

        data = dict(
            SegmentID=self.trigger.segment_ids,
            Time=pint_pandas.PintArray(self.trigger.segmented_time, "second"),
        )

        for detetector_name in detectors:
            data[detetector_name] = pint_pandas.PintArray(
                self.trigger.get_segmented_signal(detetector_name),
                dataframe.signal_units
            )

        tidy = pd.DataFrame(data).set_index("SegmentID")

        tidy = TriggerDataFrame(tidy, plot_type="analog")

        tidy.normalize_units(signal_units='max', time_units='max')

        meta_data = dict(
            threshold={"detector": self.trigger_detector_name, "value": self.threshold},
        )

        # metadata passthrough
        tidy.attrs.update(meta_data)

        return tidy


class FixedWindow(FIXEDWINDOW, BaseTrigger):
    """
    Fixed window triggering scheme.
    """

    def __init__(self,
        trigger_detector_name: str,
        threshold: units.Quantity | str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:

        """
        Initialize the FixedWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        trigger_detector_name : str
            Name of the detector to use for triggering.
        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.threshold = threshold

    def run(self, dataframe: pd.DataFrame) -> TriggerDataFrame:
        """
        Run the fixed window triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.init_data(dataframe)

        _threshold = self._parse_threshold(self.threshold, dataframe)

        self._cpp_run(
            threshold=_threshold.to(dataframe.signal_units).magnitude,
        )

        out_df = self._assemble_dataframe(dataframe)

        out_df.attrs['scatterer'] = dataframe.scatterer

        return out_df


class DynamicWindow(DYNAMICWINDOW, BaseTrigger):
    """
    Dynamic window triggering scheme.
    """
    def __init__(self,
        trigger_detector_name: str,
        threshold: units.Quantity | str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:
        """
        Initialize the DynamicWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        trigger_detector_name : str
            Name of the detector to use for triggering.
        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.threshold = threshold


    def run(self, dataframe: pd.DataFrame) -> TriggerDataFrame:
        """
        Run the dynamic window triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.init_data(dataframe)

        _threshold = self._parse_threshold(self.threshold, dataframe)

        self._cpp_run(
            threshold=_threshold.to(dataframe.signal_units).magnitude,
        )

        output = self._assemble_dataframe(dataframe)

        output.attrs['scatterer'] = dataframe.scatterer

        return output


class DoubleThreshold(DOUBLETHRESHOLD, BaseTrigger):
    """
    Double threshold triggering scheme.
    """

    def __init__(self,
        trigger_detector_name: str,
        upper_threshold: units.Quantity | str,
        lower_threshold: Optional[units.Quantity] = np.nan * units.volt,
        min_window_duration: Optional[units.Quantity] = None,
        debounce_enabled: bool = True,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:

        """
        Initialize the DoubleThreshold triggering scheme with the specified parameters.


        Parameters
        ----------
        trigger_detector_name : str
            Name of the detector to use for triggering.
        upper_threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.
        lower_threshold : Optional[units.Quantity], optional
            Lower threshold for dynamic scheme to finish a window (default is np.nan * units.volt).
        debounce_enabled : bool, optional
            Whether to apply debouncing logic (default is True).
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.debounce_enabled = debounce_enabled
        self.min_window_duration = min_window_duration
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold

    def run(self, dataframe: pd.DataFrame) -> TriggerDataFrame:
        """
        Run the double threshold triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.init_data(dataframe)

        _upper_threshold = self._parse_threshold(self.upper_threshold, dataframe)
        _lower_threshold = self._parse_threshold(self.lower_threshold, dataframe)

        ds = dataframe['Time'][1]-dataframe['Time'][0]
        sampling_rate = (1 / ds)

        min_win_samples = (
            int((self.min_window_duration * sampling_rate).to("dimensionless").m) if self.min_window_duration is not None else -1
        )

        self._cpp_run(
            threshold=_upper_threshold.to(dataframe.signal_units).magnitude,
            lower_threshold=_lower_threshold.to(dataframe.signal_units).magnitude,
            min_window_duration=min_win_samples,
            debounce_enabled=self.debounce_enabled,
        )

        out_df = self._assemble_dataframe(dataframe)

        out_df.attrs['scatterer'] = dataframe.scatterer

        return out_df
