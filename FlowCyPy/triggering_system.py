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
    def init_data(self):
        # feed time + all detector signals
        self._cpp_add_time(self.dataframe["Time"].pint.quantity.magnitude)

        for detector_name in self.dataframe.detector_names:
            self._cpp_add_signal(detector_name, self.dataframe[detector_name].pint.quantity.magnitude)

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
                return (median_val + number_of_sigma * sigma_mad) * self.dataframe.signal_units
            else:
                raise ValueError(f"Unknown threshold format: {threshold!r}")

        elif isinstance(threshold, units.Quantity):
            return threshold
        else:
            raise TypeError(f"Unsupported threshold type: {type(threshold)}")

    def _assemble_dataframe(self) -> TriggerDataFrame:
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
            warnings.warn(f"No signal met the trigger criteria. Try adjusting the threshold. Signal min/max: {self.dataframe[self.trigger_detector_name].min().to_compact()}, {self.dataframe[self.trigger_detector_name].max().to_compact()}", UserWarning)
            self._warn_no_hits(self.dataframe, self.trigger_detector_name)
            return None

        detectors = self.dataframe.detector_names

        data = dict(
            SegmentID=self.trigger.segment_ids,
            Time=pint_pandas.PintArray(self.trigger.segmented_time, "second"),
        )

        for detetector_name in detectors:
            data[detetector_name] = pint_pandas.PintArray(
                self.trigger.get_segmented_signal(detetector_name),
                self.dataframe.signal_units
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
        digitizer: object,
        dataframe: pd.DataFrame,
        trigger_detector_name: str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:

        """
        Initialize the FixedWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        digitizer : object
            The digitizer object used for sampling.
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.
        trigger_detector_name : str
            Name of the detector to use for triggering.
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        self.digitizer = digitizer
        self.dataframe = dataframe
        self.dataframe.normalize_units(time_units=units.second, signal_units=units.volt)

        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.init_data()

    def run(self, threshold: units.Quantity | str) -> TriggerDataFrame:
        """
        Run the fixed window triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.threshold = self._parse_threshold(threshold, self.dataframe)

        self._cpp_run(
            threshold=self.threshold.to(self.dataframe.signal_units).magnitude,
        )

        out_df = self._assemble_dataframe()

        out_df.attrs['scatterer'] = self.dataframe.scatterer

        return out_df


class DynamicWindow(DYNAMICWINDOW, BaseTrigger):
    """
    Dynamic window triggering scheme.
    """
    def __init__(self,
        digitizer: object,
        dataframe: pd.DataFrame,
        trigger_detector_name: str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:
        """
        Initialize the DynamicWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        digitizer : object
            The digitizer object used for sampling.
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.
        trigger_detector_name : str
            Name of the detector to use for triggering.
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        self.digitizer = digitizer
        self.dataframe = dataframe
        self.dataframe.normalize_units(time_units=units.second, signal_units=units.volt)

        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.init_data()


    def run(self, threshold: units.Quantity | str) -> TriggerDataFrame:
        """
        Run the dynamic window triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.threshold = self._parse_threshold(threshold, self.dataframe)

        self._cpp_run(
            threshold=self.threshold.to(self.dataframe.signal_units).magnitude,
        )

        output = self._assemble_dataframe()

        output.attrs['scatterer'] = self.dataframe.scatterer

        return output


class DoubleThreshold(DOUBLETHRESHOLD, BaseTrigger):
    """
    Double threshold triggering scheme.
    """

    def __init__(self,
        digitizer: object,
        dataframe: pd.DataFrame,
        trigger_detector_name: str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:

        """
        Initialize the DoubleThreshold triggering scheme with the specified parameters.
        Parameters
        ----------
        digitizer : object
            The digitizer object used for sampling.
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.
        trigger_detector_name : str
            Name of the detector to use for triggering.
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        """
        self.digitizer = digitizer
        self.dataframe = dataframe
        self.dataframe.normalize_units(time_units=units.second, signal_units=units.volt)

        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )

        self.init_data()

    def run(self,
        threshold: units.Quantity | str,
        lower_threshold: Optional[units.Quantity] = np.nan * units.volt,
        min_window_duration=None,
        debounce_enabled: bool = True,

    ) -> TriggerDataFrame:
        """
        Run the double threshold triggering algorithm on the provided DataFrame.

        Parameters
        ----------
        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.
        lower_threshold : Optional[units.Quantity], optional
            Lower threshold for dynamic scheme to finish a window (default is np.nan * units.volt).
        debounce_enabled : bool, optional
            Whether to apply debouncing logic (default is True).
        scheme : Union[Scheme, str], optional
            Triggering scheme to use, either a Scheme enum or a string (default is Scheme.SIMPLE).

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.
        """
        self.threshold = self._parse_threshold(threshold, self.dataframe)

        min_win_samples = (
            int((min_window_duration * self.digitizer.sampling_rate).to("dimensionless").m) if min_window_duration is not None else -1
        )

        self._cpp_run(
            threshold=self.threshold.to(self.dataframe.signal_units).magnitude,
            lower_threshold=lower_threshold.to(self.dataframe.signal_units).magnitude,
            min_window_duration=min_win_samples,
            debounce_enabled=debounce_enabled,
        )

        out_df = self._assemble_dataframe()

        out_df.attrs['scatterer'] = self.dataframe.scatterer

        return out_df
