from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence, Union
import warnings

import numpy as np
import pandas as pd
import pint
import pint_pandas

from FlowCyPy import units
from FlowCyPy.dataframe_subclass import TriggerDataFrame
from FlowCyPy.binary.interface_triggering_system import TriggeringSystem as cpp_binding  # type: ignore

# ---------------------------------------------------------------------------
# Helpers / types
# ---------------------------------------------------------------------------

class Scheme(str, Enum):
    """
    Triggering windows available in the C++ backend.
    """

    FIXED = "fixed-window"
    DYNAMIC = "dynamic"

    def __str__(self) -> str:  # nicer repr in help()
        return self.value

@dataclass(slots=True, kw_only=True)
class TriggeringSystem:
    """Detect threshold-crossing windows and structure them into a DataFrame.

    Parameters
    ----------
    threshold
        Threshold on the *trigger* detector signal.  Must carry units.
    pre_buffer, post_buffer
        Extra samples to copy before / after the detected window.
    max_triggers
        -1 → unlimited.  Any positive value caps the number of extracted windows.
    min_window_duration
        If given, debouncing requires *continuous* above-threshold time ≥ this.
    lower_threshold
        Dynamic scheme only.  Finishes a window once the signal dips below this
        value (defaults to *threshold*).
    debounce_enabled
        Skip / apply the min-duration rule.
    scheme
        "fixed-window" or "dynamic".  Use the :class:`Scheme` enum for type
        safety, but raw strings work too.
    """

    threshold: units.Quantity | str
    digitizer: object
    pre_buffer: int = 64
    post_buffer: int = 64
    max_triggers: int = -1
    min_window_duration: Optional[units.Quantity] = None
    lower_threshold: Optional[units.Quantity] = None
    debounce_enabled: bool = True
    scheme: Union[Scheme, str] = Scheme.DYNAMIC

    # internal, filled in __post_init__
    _signal_units: pint.Unit = field(init=False, repr=False)

    # ---------------------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------------------

    def __post_init__(self) -> None:

        if self.pre_buffer < 0 or self.post_buffer < 0:
            raise ValueError("buffers must be >= 0")

        try:
            self.scheme = Scheme(self.scheme)
        except ValueError as exc:
            raise ValueError(f"Unknown scheme {self.scheme!r}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, signal_dataframe: pd.DataFrame, trigger_detector_name: str) -> TriggerDataFrame:
        """
        Extract windows where *trigger_detector_name* crosses *threshold*.

        Returns
        -------
        TriggeredAcquisitions | None
            None when no window matches the criteria (a warning is emitted).
        """
        detectors: Sequence[str] = list(signal_dataframe.detector_names)
        if trigger_detector_name not in detectors:
            raise ValueError(f"Detector {trigger_detector_name!r} not found in frame")

        self._signal_units = signal_dataframe[trigger_detector_name].pint.units

        if isinstance(self.threshold, str):  # MAD-based method
            number_of_sigma = float(self.threshold.strip('sigma'))
            signal = signal_dataframe[trigger_detector_name].pint.quantity.magnitude
            median_val = np.median(signal)
            mad = np.median(np.abs(signal - median_val))
            sigma_mad = mad / 0.6745

            self.threshold = (median_val + number_of_sigma * sigma_mad) * self._signal_units

        df_norm = self._normalize_units(signal_dataframe, detectors)
        cpp_sys = self._build_cpp_trigger(
            lower_thr_default=self.threshold,
            trigger_detector_name=trigger_detector_name,
        )

        # feed time + all detector signals
        cpp_sys.add_time(df_norm["Time"].values)
        for det in detectors:
            cpp_sys.add_signal(det, df_norm[det].values)

        cpp_sys.run(algorithm=str(self.scheme))

        if len(cpp_sys.get_signals(trigger_detector_name)) == 0:
            self._warn_no_hits(signal_dataframe, trigger_detector_name)
            return None

        out_df = self._assemble_dataframe(cpp_sys, detectors)

        out_df.attrs['scatterer'] = signal_dataframe.scatterer

        return out_df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize_units(self, df: pd.DataFrame, detectors: Sequence[str]) -> pd.DataFrame:
        """Return a *copy* of *df* whose Time + each detector share one unit set."""

        dfc = df.copy()
        dfc["Time"] = df["Time"].pint.to("second").pint.magnitude
        for det in detectors:
            dfc[det] = df[det].pint.to(self._signal_units).pint.magnitude
        return dfc

    def _build_cpp_trigger(self, lower_thr_default: units.Quantity, trigger_detector_name: str) -> cpp_binding:
        """
        Instantiate and configure the fast C++ backend.
        """
        lower_thr = (self.lower_threshold or lower_thr_default).to(self._signal_units).magnitude

        min_win_samples = (
            int((self.min_window_duration * self.digitizer.sampling_rate).to("dimensionless").m)
            if self.min_window_duration is not None
            else -1
        )

        return cpp_binding(
            trigger_detector_name=trigger_detector_name,
            threshold=self.threshold.to(self._signal_units).magnitude,
            pre_buffer=self.pre_buffer,
            post_buffer=self.post_buffer,
            max_triggers=self.max_triggers,
            lower_threshold=lower_thr,
            min_window_duration=min_win_samples,
            debounce_enabled=self.debounce_enabled,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _warn_no_hits(df: pd.DataFrame, det: str) -> None:  # pragma: no cover
        warnings.warn(
            "No signal met the trigger criteria. Try adjusting the threshold. "
            f"Signal min/max: {df[det].min().to_compact()}, {df[det].max().to_compact()}",
            UserWarning,
            stacklevel=2,
        )

    def _assemble_dataframe(self, cpp_sys: cpp_binding, detectors: Sequence[str]) -> TriggerDataFrame:
        """
        Transform raw numpy outputs from C++ into a typed TriggerDataFrame.
        """

        data = {
            "SegmentID": cpp_sys.get_segments_ID(detectors[0]),
            "Time": pint_pandas.PintArray(cpp_sys.get_times(detectors[0]), "second"),
        }
        for det in detectors:
            sig_np = cpp_sys.get_signals(det)
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
