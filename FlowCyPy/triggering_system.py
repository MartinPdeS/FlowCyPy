from enum import Enum
from typing import Optional
import warnings

import numpy as np
import pandas as pd
import pint
import pint_pandas

from FlowCyPy import units
from FlowCyPy.dataframe_subclass import TriggerDataFrame
from FlowCyPy.binary.interface_triggering_system import TRIGERRINGSYSTEM

class Scheme(str, Enum):
    """
    Triggering windows available in the C++ backend.
    """

    FIXED = "fixed-window"
    DYNAMIC = "dynamic"
    SIMPLE = "dynamic-simple"

    def __str__(self) -> str:  # nicer repr in help()
        return self.value


class TriggeringSystem(TRIGERRINGSYSTEM):
    _signal_units: pint.Unit

    def __init__(self,
        digitizer: object,
        dataframe: pd.DataFrame,
        trigger_detector_name: str,
        max_triggers: int = -1,
        pre_buffer: int = 64,
        post_buffer: int = 64) -> None:

        """
        Initialize the TriggeringSystem with the specified parameters.
        Detect threshold-crossing windows and structure them into a DataFrame.

        Parameters
        ----------
        dataframe : pd.DataFrame
            DataFrame containing the signal data with a 'Time' column and detector signals.
        trigger_detector_name : str
            Name of the detector to use for triggering.
        digitizer : object
            The digitizer object used for sampling.
        pre_buffer : int, optional
            Number of samples to include before the trigger event (default is 64).
        post_buffer : int, optional
            Number of samples to include after the trigger event (default is 64).
        max_triggers : int, optional
            Maximum number of triggers to extract. -1 means unlimited (default is -1).

        Raises
        ------
        ValueError
            If the scheme is unknown or if the threshold format is invalid.
        TypeError
            If the threshold is neither a string nor a Quantity.
        """
        self.digitizer = digitizer
        self.dataframe = dataframe

        super().__init__(
            trigger_detector_name=trigger_detector_name,
            pre_buffer=pre_buffer,
            post_buffer=post_buffer,
            max_triggers=max_triggers,
        )


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self,
        threshold: units.Quantity | str,
        min_window_duration: Optional[units.Quantity] = None,
        lower_threshold: Optional[units.Quantity] = np.nan * units.volt,
        debounce_enabled: bool = True,
        scheme: Scheme = Scheme.DYNAMIC
    ) -> TriggerDataFrame:
        """
        Run the triggering algorithm on the provided DataFrame.

        Parameters
        ----------

        threshold : units.Quantity | str
            Threshold for triggering, can be a string like "3sigma" or a Quantity.
        min_window_duration : Optional[units.Quantity], optional
            Minimum duration of the window to consider it valid (default is None).
        lower_threshold : Optional[units.Quantity], optional
            Lower threshold for dynamic scheme to finish a window (default is np.nan * units.volt).
        debounce_enabled : bool, optional
            Whether to apply debouncing logic (default is True).
        scheme : Union[Scheme, str], optional
            Triggering scheme to use, either a Scheme enum or a string (default is Scheme.DYNAMIC).

        Returns
        -------
        TriggerDataFrame
            A DataFrame containing the detected trigger windows.

        Raises
        ------
        ValueError
            If the scheme is unknown or if the threshold format is invalid.
        TypeError
            If the threshold is neither a string nor a Quantity.
        """
        try:
            self.scheme = Scheme(scheme)
        except ValueError as exc:
            raise ValueError(f"Unknown scheme {scheme!r}") from exc

        min_win_samples = (
            int((min_window_duration * self.digitizer.sampling_rate).to("dimensionless").m) if min_window_duration is not None else -1
        )

        self.threshold = self._parse_threshold(threshold, self.dataframe)

        df_norm = self.dataframe.normalize(signal_units="volt", time_units="second", inplace=False)
        self._signal_units = units.volt

        # feed time + all detector signals
        self._cpp_add_time(df_norm["Time"].pint.quantity.magnitude)

        for detector_name in self.dataframe.detector_names:
            self._cpp_add_signal(detector_name, df_norm[detector_name].pint.quantity.magnitude)

        self._cpp_run(
            algorithm=str(self.scheme),
            threshold=self.threshold.to("volt").magnitude,
            lower_threshold=lower_threshold.to("volt").magnitude,
            min_window_duration=min_win_samples,
            debounce_enabled=debounce_enabled,
        )

        if len(self._cpp_get_signals(self.trigger_detector_name)) == 0:
            warnings.warn(f"No signal met the trigger criteria. Try adjusting the threshold. Signal min/max: {self.dataframe[self.trigger_detector_name].min().to_compact()}, {self.dataframe[self.trigger_detector_name].max().to_compact()}", UserWarning)
            self._warn_no_hits(self.dataframe, self.trigger_detector_name)
            return None

        out_df = self._assemble_dataframe()

        out_df.attrs['scatterer'] = self.dataframe.scatterer

        return out_df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
                return (median_val + number_of_sigma * sigma_mad) * self._signal_units
            else:
                raise ValueError(f"Unknown threshold format: {threshold!r}")

        elif isinstance(threshold, units.Quantity):
            return threshold
        else:
            raise TypeError(f"Unsupported threshold type: {type(threshold)}")

    def _assemble_dataframe(self) -> TriggerDataFrame:
        """
        Transform raw numpy outputs from C++ into a typed TriggerDataFrame.
        """

        detectors = self.dataframe.detector_names

        data = {
            "SegmentID": self._cpp_get_segments_ID(detectors[0]),
            "Time": pint_pandas.PintArray(self._cpp_get_times(detectors[0]), "second"),
        }
        for det in detectors:
            sig_np = self._cpp_get_signals(det)
            data[det] = pint_pandas.PintArray(sig_np, self._signal_units)

        tidy = (
            pd.DataFrame(data)
            .set_index("SegmentID")
            .pipe(TriggerDataFrame, plot_type="analog")
        )

        # metadata passthrough
        tidy.attrs.update(
            {
                "threshold": {"detector": detectors[0], "value": self.threshold},
            }
        )

        return tidy
