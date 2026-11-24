
import numpy as np
import pandas as pd
import pytest
from TypedUnit import ureg

from FlowCyPy.analysis import DetectionAnalyzer
from FlowCyPy.run_record import RunRecord, SignalRecord


def make_run_record(event_times, populations, trigger_times=None):
    events = pd.DataFrame({
        "Population": populations,
        "Time": event_times,
    })

    class EventCollection:
        def get_concatenated_dataframe(self):
            return events

    if trigger_times is None:
        digital = None
    else:
        digital = pd.DataFrame(
            {"Time": trigger_times},
            index=pd.Index([0] * len(trigger_times), name="SegmentID"),
        )
        digital.attrs["units"] = {"Time": ureg.second}

    return RunRecord(
        run_time=1 * ureg.second,
        event_collection=EventCollection(),
        signal=SignalRecord(digital=digital),
    )


def test_detection_analyzer_marks_events_inside_trigger_windows():
    record = make_run_record(
        event_times=[0.1, 0.5, 0.9],
        populations=["EVs", "EVs", "LPs"],
        trigger_times=[0.0, 0.2],
    )

    result = DetectionAnalyzer().annotate(record)

    assert result["Detected"].tolist() == [True, False, False]
    assert result.loc[0, "TriggerID"] == 0


def test_detection_analyzer_handles_no_triggers():
    record = make_run_record(
        event_times=[0.1, 0.5],
        populations=["EVs", "LPs"],
    )

    result = DetectionAnalyzer().annotate(record)

    assert not result["Detected"].any()


def test_detection_analyzer_summary_counts_by_population():
    record = make_run_record(
        event_times=[0.1, 0.5, 0.9],
        populations=["EVs", "EVs", "LPs"],
        trigger_times=[0.0, 0.2],
    )

    summary = DetectionAnalyzer().summary(
        [record],
        condition_names=["condition"],
    )

    ev_row = summary[summary["Population"] == "EVs"].iloc[0]
    assert ev_row["SimulatedEvents"] == 2
    assert ev_row["DetectedEvents"] == 1
    assert np.isclose(ev_row["DetectionEfficiency"], 0.5)


def test_run_record_exposes_population_detection_statistics():
    record = make_run_record(
        event_times=[0.1, 0.5, 0.9],
        populations=["EVs", "EVs", "LPs"],
        trigger_times=[0.0, 0.2],
    )

    statistics = record.detection_statistics("EVs")

    assert statistics["SimulatedEvents"] == 2
    assert statistics["DetectedEvents"] == 1
    assert np.isclose(statistics["DetectionEfficiency"], 0.5)
    assert np.isclose(
        statistics["DetectionEfficiencyStandardError"],
        0.3535533905932738,
    )
    assert statistics["CoincidentDetectedEvents"] == 0
    assert statistics["CoincidencePartners"] == {}


def test_run_record_computes_multi_coincidence_statistics():
    record = make_run_record(
        event_times=[0.1, 0.15, 0.9],
        populations=["EVs", "LPs", "EVs"],
        trigger_times=[0.0, 0.2],
    )

    statistics = record.coincidence_statistics()

    assert statistics["TriggerSegments"] == 1
    assert statistics["DetectedEvents"] == 2
    assert statistics["CoincidentSegments"] == 1
    assert statistics["PopulationCombinations"] == {"EVs+LPs": 1}

    ev_statistics = record.detection_statistics("EVs")
    assert ev_statistics["CoincidentDetectedEvents"] == 1
    assert ev_statistics["CoincidencePartners"] == {"LPs": 1}


def test_coincidence_statistics_counts_all_trigger_segments():
    """Count empty, single-event, and coincident windows in one acquisition."""
    record = make_run_record(
        event_times=[0.1, 0.15, 0.5, 0.95],
        populations=["EVs", "LPs", "EVs", "LPs"],
    )
    record.signal.digital = pd.DataFrame(
        {
            "segment_id": [10, 10, 20, 20, 30, 30],
            "Time": [0.0, 0.2, 0.4, 0.6, 0.7, 0.9],
        }
    )

    statistics = record.coincidence_statistics()

    assert statistics["TotalTriggerSegments"] == 3
    assert statistics["EmptySegments"] == 1
    assert statistics["SingleEventSegments"] == 1
    assert statistics["CoincidentSegments"] == 1
    assert statistics["DetectedEvents"] == 3
    assert statistics["TriggerSegments"] == 2
    assert statistics["CoincidenceRate"] == 0.5


@pytest.mark.parametrize(
    ("trigger_times", "expected_segment_count"),
    [(None, 0), ([], 0), ([0.0, 0.2], 1)],
)
def test_coincidence_statistics_handles_no_simulated_arrivals(
    trigger_times, expected_segment_count
):
    """Keep any trigger windows in acquisitions without simulated events."""
    record = make_run_record(
        event_times=[], populations=[], trigger_times=trigger_times
    )

    statistics = record.coincidence_statistics()

    assert statistics["TotalTriggerSegments"] == expected_segment_count
    assert statistics["EmptySegments"] == expected_segment_count
    assert statistics["SingleEventSegments"] == 0
    assert statistics["CoincidentSegments"] == 0
    assert statistics["DetectedEvents"] == 0
    assert np.isnan(statistics["CoincidenceRate"])
