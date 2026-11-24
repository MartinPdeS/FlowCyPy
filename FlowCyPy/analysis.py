"""Analysis helpers for simulated flow-cytometry acquisitions."""


from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from .units import ureg


class DetectionAnalyzer:
    """Relate digital trigger windows to simulated population events.

    The analyzer uses the ground-truth event arrival time and population label
    stored in a :class:`~FlowCyPy.run_record.RunRecord`. An event is considered
    detected when its arrival time falls within a digital trigger segment.

    This measures trigger capture, not successful peak localization.
    """

    @staticmethod
    def _to_seconds(values, unit=None) -> np.ndarray:
        """Convert quantities or numeric values to seconds."""
        if hasattr(values, "pint"):
            return np.asarray(values.pint.to("second").magnitude, dtype=float)

        if hasattr(values, "to") and hasattr(values, "magnitude"):
            return np.asarray(values.to("second").magnitude, dtype=float)

        raw_values = list(values) if hasattr(values, "__iter__") else [values]
        seconds = []
        for value in raw_values:
            if hasattr(value, "to") and hasattr(value, "magnitude"):
                seconds.append(value.to("second").magnitude)
            elif unit is not None:
                unit_value = ureg(unit) if isinstance(unit, str) else unit
                seconds.append((value * unit_value).to("second").magnitude)
            else:
                seconds.append(value)
        return np.asarray(seconds, dtype=float)

    @staticmethod
    def _event_dataframe(run_record) -> pd.DataFrame:
        """Return the simulated event table with population labels exposed."""
        return (
            run_record.event_collection
            .get_concatenated_dataframe()
            .reset_index()
        )

    @staticmethod
    def _segment_column(*, digital: pd.DataFrame) -> str | None:
        """Return the label used for trigger segment identifiers."""
        for label in ("SegmentID", "segment_id"):
            if label in digital.columns or label in digital.index.names:
                return label
        return None

    def annotate(self, run_record) -> pd.DataFrame:
        """Annotate events with ``Detected`` and ``TriggerID`` columns.

        Events without a matching trigger segment are retained and marked
        ``Detected=False``. Runs without any digital triggers are supported.

        An event is detected when its simulated arrival time satisfies
        ``segment_start <= event_time <= segment_stop`` for a digital trigger
        segment. If an event falls into more than one segment, the first
        matching segment in the digital table is assigned.
        """
        events = self._event_dataframe(run_record).copy()
        events["Detected"] = False
        events["TriggerID"] = pd.Series(
            pd.NA, index=events.index, dtype="Int64"
        )

        digital = run_record.signal.digital
        if digital is None or "Time" not in events or len(events) == 0:
            return events

        segment_column = self._segment_column(digital=digital)
        if segment_column is None:
            return events

        digital_table = digital.reset_index()
        digital_unit = digital.attrs.get("units", {}).get("Time", "second")
        digital_table["_time_s"] = self._to_seconds(
            digital_table["Time"], unit=digital_unit
        )
        event_times = self._to_seconds(events["Time"])
        detected = np.zeros(len(events), dtype=bool)
        trigger_ids = np.full(len(events), -1, dtype=int)

        for segment_id, segment in digital_table.groupby(segment_column, observed=True):
            start = segment["_time_s"].min()
            stop = segment["_time_s"].max()
            matches = (
                (event_times >= start)
                & (event_times <= stop)
                & ~detected
            )
            detected[matches] = True
            trigger_ids[matches] = int(segment_id)

        events["Detected"] = detected
        events.loc[detected, "TriggerID"] = trigger_ids[detected]
        return events

    def summary(
        self,
        run_records: Sequence,
        population_names: Iterable[str] | None = None,
        condition_names: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Return simulated counts, detected counts, and efficiencies.

        ``SimulatedEvents`` counts events of the selected population in the
        event collection after the SEC cutoff. ``DetectedEvents`` counts those
        events whose arrival times overlap a digital trigger segment.
        ``DetectionEfficiency`` is calculated as:

        ``DetectedEvents / SimulatedEvents``
        """
        if condition_names is None:
            condition_names = [
                f"Run {index}" for index in range(len(run_records))
            ]
        if len(condition_names) != len(run_records):
            raise ValueError("condition_names must match run_records.")

        rows = []
        for condition, run_record in zip(condition_names, run_records):
            events = self.annotate(run_record)
            available = sorted(events["Population"].dropna().unique())
            selected = list(population_names) if population_names else available
            for population in selected:
                statistics = run_record.detection_statistics(population)
                rows.append({"Condition": condition, **statistics})
        return pd.DataFrame(rows)

    def coincidence_statistics(self, run_record) -> dict:
        """Count trigger segments by the number of assigned simulated arrivals.

        Parameters
        ----------
        run_record : RunRecord
            Acquisition containing simulated arrivals and digital segments.

        Returns
        -------
        dict
            Segment counts, assigned arrival counts, coincidence rate among
            occupied segments, and population combinations.

        Notes
        -----
        Counts follow :meth:`annotate`, including its first-match rule for
        overlapping windows. They describe window occupancy. Peak
        localization is evaluated separately.
        """
        events = self.annotate(run_record)
        detected = events[
            events["Detected"] & events["TriggerID"].notna()
        ]

        by_segment = detected.groupby("TriggerID", dropna=True)
        segment_sizes = by_segment.size()
        coincident_segments = segment_sizes[segment_sizes >= 2]
        combinations = {}

        for _, segment in by_segment:
            if len(segment) < 2:
                continue
            populations = "+".join(sorted(segment["Population"].astype(str)))
            combinations[populations] = combinations.get(populations, 0) + 1

        digital = run_record.signal.digital
        total_trigger_segments = 0
        if digital is not None:
            segment_column = self._segment_column(digital=digital)
            if segment_column is not None:
                total_trigger_segments = digital.groupby(
                    segment_column, observed=True
                ).ngroups

        trigger_segments = len(segment_sizes)
        return {
            "TriggerSegments": trigger_segments,
            "TotalTriggerSegments": total_trigger_segments,
            "EmptySegments": total_trigger_segments - trigger_segments,
            "SingleEventSegments": int((segment_sizes == 1).sum()),
            "DetectedEvents": len(detected),
            "CoincidentSegments": len(coincident_segments),
            "CoincidenceRate": (
                len(coincident_segments) / trigger_segments
                if trigger_segments else np.nan
            ),
            "PopulationCombinations": combinations,
        }
