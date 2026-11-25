"""Analysis helpers for simulated flow-cytometry acquisitions."""


from collections.abc import Iterable, Sequence
import numpy as np
import pandas as pd
from pint import Quantity
from .units import ureg


class DetectionAnalyzer:
    """Relate digital trigger windows to simulated population events.

    The analyzer uses the ground-truth event arrival time and population label
    stored in a :class:`~FlowCyPy.run_record.RunRecord`. An event is considered
    detected when its arrival time falls within a digital trigger segment.

    This measures trigger capture, not successful peak localization.
    """

    @staticmethod
    def _time_quantity(*, values: pd.Series | Quantity, unit) -> Quantity:
        """Read a time column for comparing arrivals with trigger windows.

        Parameters
        ----------
        values : pandas.Series or pint.Quantity
            One-dimensional time column.
        unit : str or pint.Unit
            Unit recorded for bare numeric values.

        Returns
        -------
        pint.Quantity
            Time array in seconds, in the original row order.
        """
        if isinstance(values, Quantity):
            return values.to("second")
        quantity = getattr(values.array, "quantity", None)
        if quantity is not None:
            return quantity.to("second")
        if pd.api.types.is_numeric_dtype(values.dtype):
            return ureg.Quantity(values.to_numpy(dtype=float), unit).to("second")

        # Older event tables can contain individual quantities in different units.
        return ureg.Quantity.from_sequence(
            [
                value
                if isinstance(value, Quantity)
                else ureg.Quantity(float(value), unit)
                for value in values
            ],
            units="second",
        )

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
        trigger_times = self._time_quantity(values=digital_table["Time"], unit=digital_unit)
        event_times = self._time_quantity(
            values=events["Time"], unit=events.attrs.get("units", {}).get("Time", "second")
        )
        detected = np.zeros(len(events), dtype=bool)
        trigger_ids = np.full(len(events), -1, dtype=int)

        segments = digital_table.groupby(segment_column, observed=True)
        for segment_id, positions in segments.indices.items():
            times = trigger_times[positions]
            times = times[~np.isnan(times)]
            if not times.size:
                continue
            start = times.min()
            stop = times.max()
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

        selected_names = None if population_names is None else list(population_names)
        rows = []
        for condition, run_record in zip(condition_names, run_records):
            events = self.annotate(run_record)
            selected = selected_names
            if selected is None:
                selected = sorted(events["Population"].dropna().unique())
            for population in selected:
                statistics = self.population_statistics(events=events, population_name=population)
                rows.append({"Condition": condition, **statistics})
        return pd.DataFrame(rows)

    @staticmethod
    def population_statistics(*, events: pd.DataFrame, population_name: str) -> dict:
        """Compute detection and coincidence statistics from annotated events.

        Parameters
        ----------
        events : pandas.DataFrame
            Annotated arrivals for all populations in one acquisition.
        population_name : str
            Population whose statistics are requested.

        Returns
        -------
        dict
            Event counts, efficiency, standard error and coincidence metrics.
        """
        if "Population" not in events:
            raise KeyError("Event data do not contain a 'Population' column.")

        population_events = events[events["Population"] == population_name]
        simulated_events = len(population_events)
        detected_events = int(population_events["Detected"].sum())

        detected = events[
            events["Detected"] & events["TriggerID"].notna()
        ]
        segment_sizes = detected.groupby("TriggerID").size()
        coincident_segments = set(segment_sizes[segment_sizes >= 2].index)
        population_trigger_ids = set(
            population_events.loc[
                population_events["Detected"], "TriggerID"
            ].dropna()
        )
        coincident_events = len(
            population_events[
                population_events["TriggerID"].isin(coincident_segments)
            ]
        )
        partners = {}
        for trigger_id in population_trigger_ids & coincident_segments:
            segment = detected[detected["TriggerID"] == trigger_id]
            for partner in segment["Population"]:
                if partner != population_name:
                    partners[partner] = partners.get(partner, 0) + 1

        return {
            "Population": population_name,
            "SimulatedEvents": simulated_events,
            "DetectedEvents": detected_events,
            "DetectionEfficiencyStandardError": (
                np.sqrt(
                    (detected_events / simulated_events)
                    * (1 - detected_events / simulated_events)
                    / simulated_events
                )
                if simulated_events
                else np.nan
            ),
            "DetectionEfficiency": (
                detected_events / simulated_events
                if simulated_events
                else np.nan
            ),
            "CoincidentDetectedEvents": coincident_events,
            "CoincidenceParticipationRate": (
                coincident_events / detected_events
                if detected_events
                else np.nan
            ),
            "CoincidencePartners": partners,
        }

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
