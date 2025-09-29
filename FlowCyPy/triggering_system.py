# -*- coding: utf-8 -*-

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import pint_pandas
import matplotlib.pyplot as plt
from TypedUnit import AnyUnit, Time, ureg

from FlowCyPy.binary.interface_triggering_system import (
    DOUBLETHRESHOLD,
    DYNAMICWINDOW,
    FIXEDWINDOW,
)
from FlowCyPy.sub_frames.acquisition import TriggerDataFrame


class BaseTrigger:
    def init_data(self, dataframe):
        dataframe.normalize_units(time_units=ureg.second, signal_units=ureg.volt)

        # feed time + all detector signals
        self._cpp_add_time(dataframe["Time"].pint.quantity.magnitude)

        for detector_name in dataframe.detector_names:
            self._cpp_add_signal(
                detector_name, dataframe[detector_name].pint.quantity.magnitude
            )

    def _parse_threshold(
        self, threshold: AnyUnit | str, signal_dataframe: pd.DataFrame
    ) -> AnyUnit:
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
                number_of_sigma = float(threshold.strip("sigma"))
                signal = signal_dataframe[
                    self.trigger_detector_name
                ].pint.quantity.magnitude
                median_val = np.median(signal)
                mad = np.median(np.abs(signal - median_val))
                sigma_mad = mad / 0.6745
                return (
                    median_val + number_of_sigma * sigma_mad
                ) * signal_dataframe.signal_units
            else:
                raise ValueError(f"Unknown threshold format: {threshold!r}")

        elif isinstance(threshold, AnyUnit):
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
            warnings.warn(
                f"No signal met the trigger criteria. Try adjusting the threshold. Signal min/max: {dataframe[self.trigger_detector_name].min().to_compact()}, {dataframe[self.trigger_detector_name].max().to_compact()}",
                UserWarning,
            )

        detectors = dataframe.detector_names

        data = dict(
            SegmentID=self.trigger.segment_ids,
            Time=pint_pandas.PintArray(self.trigger.segmented_time, "second"),
        )

        for detetector_name in detectors:
            data[detetector_name] = pint_pandas.PintArray(
                self.trigger.get_segmented_signal(detetector_name),
                dataframe.signal_units,
            )

        tidy = pd.DataFrame(data).set_index("SegmentID")

        tidy = TriggerDataFrame(tidy)

        tidy.normalize_units(signal_units="max", time_units="max")

        return tidy


class FixedWindow(FIXEDWINDOW, BaseTrigger):
    """
    Fixed window triggering scheme.
    """

    def __init__(
        self,
        trigger_detector_name: str,
        threshold: AnyUnit | str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64,
    ) -> None:
        """
        Initialize the FixedWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        trigger_detector_name : str
            Name of the detector to use for triggering.
        threshold : AnyUnit | str
            Threshold for triggering, can be a string like "3sigma" or a AnyUnit.
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

        self.threshold_absolute = self._parse_threshold(self.threshold, dataframe)

        self._cpp_run(
            threshold=self.threshold_absolute.to(dataframe.signal_units).magnitude,
        )

        out_df = self._assemble_dataframe(dataframe)

        return out_df

    def _add_to_ax(self, ax: plt.Axes, signal_units: ureg.Quantity) -> None:
        """Add a horizontal line to the provided Axes representing the threshold."""
        if not hasattr(self, "threshold_absolute"):
            raise AttributeError("Threshold has not been set. Run the trigger first.")

        ax.axhline(
            self.threshold_absolute.to(signal_units).magnitude,
            color="black",
            linestyle="--",
            linewidth=1,
            label=f"Threshold: {self.threshold_absolute.to_compact():.2f}",
        )
        ax.legend()


class DynamicWindow(DYNAMICWINDOW, BaseTrigger):
    """
    Dynamic window triggering scheme.
    """

    def __init__(
        self,
        trigger_detector_name: str,
        threshold: AnyUnit | str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64,
    ) -> None:
        """
        Initialize the DynamicWindow triggering scheme with the specified parameters.

        Parameters
        ----------
        trigger_detector_name : str
            Name of the detector to use for triggering.
        threshold : AnyUnit | str
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

        self.threshold_absolute = self._parse_threshold(self.threshold, dataframe)

        self._cpp_run(
            threshold=self.threshold_absolute.to(dataframe.signal_units).magnitude,
        )

        output = self._assemble_dataframe(dataframe)

        return output

    def _add_to_ax(self, ax: plt.Axes, signal_units: ureg.Quantity) -> None:
        """Add a horizontal line to the provided Axes representing the threshold."""
        if not hasattr(self, "threshold_absolute"):
            raise AttributeError("Threshold has not been set. Run the trigger first.")

        ax.axhline(
            self.threshold_absolute.to(signal_units).magnitude,
            color="black",
            linestyle="--",
            linewidth=1,
            label=f"Threshold: {self.threshold_absolute.to_compact():.2f}",
        )
        ax.legend()


class DoubleThreshold(DOUBLETHRESHOLD, BaseTrigger):
    """
    Double threshold triggering scheme.
    """

    def __init__(
        self,
        trigger_detector_name: str,
        upper_threshold: AnyUnit | str,
        lower_threshold: Optional[AnyUnit] = np.nan * ureg.volt,
        min_window_duration: Optional[Time] = None,
        debounce_enabled: bool = True,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64,
    ) -> None:
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

        ds = dataframe["Time"][1] - dataframe["Time"][0]
        sampling_rate = 1 / ds

        min_win_samples = (
            int((self.min_window_duration * sampling_rate).to("dimensionless").m)
            if self.min_window_duration is not None
            else -1
        )

        self._cpp_run(
            threshold=_upper_threshold.to(dataframe.signal_units).magnitude,
            lower_threshold=_lower_threshold.to(dataframe.signal_units).magnitude,
            min_window_duration=min_win_samples,
            debounce_enabled=self.debounce_enabled,
        )

        out_df = self._assemble_dataframe(dataframe)

        return out_df

    def _add_to_ax(self, ax: plt.Axes, signal_units: ureg.Quantity) -> None:
        """Add horizontal lines to the provided Axes representing the thresholds."""
        if not hasattr(self, "upper_threshold"):
            raise AttributeError("Thresholds have not been set. Run the trigger first.")

        ax.axhline(
            self.upper_threshold.to(signal_units).magnitude,
            color="C0",
            linestyle="--",
            linewidth=1,
            label=f"Upper Threshold: {self.upper_threshold.to_compact():.2f}",
        )
        if not np.isnan(self.lower_threshold.magnitude):
            ax.axhline(
                self.lower_threshold.to(signal_units).magnitude,
                color="C1",
                linestyle="--",
                linewidth=1,
                label=f"Lower Threshold: {self.lower_threshold.to_compact():.2f}",
            )
        ax.legend()
