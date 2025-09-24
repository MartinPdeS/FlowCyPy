#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

import pandas as pd
from TypedUnit import Time

from FlowCyPy.sub_frames.acquisition import AcquisitionDataFrame


class RunRecord:
    """
    A class to store the results of a flow cytometer run.
    This class holds various attributes related to the results of a flow cytometer simulation run,
    including the run time, detected peaks, analog signals, triggered analog signals, and event data.

    Attributes
    ----------
    run_time : Time
        The duration of the acquisition in seconds.
    peaks : Optional[pd.DataFrame]
        A DataFrame containing the detected peaks and their features.
    analog : Optional[AcquisitionDataFrame]
        A structured DataFrame representing the multi-detector analog voltage signals.
    triggered_analog : Optional[AcquisitionDataFrame]
        A structured DataFrame representing the triggered segments of the analog voltage signals.
    events : Optional[pd.DataFrame]
        A DataFrame containing event data for the scatterers.
    """

    analog: Optional[AcquisitionDataFrame] = None
    triggered_analog: Optional[AcquisitionDataFrame] = None
    events: Optional[pd.DataFrame] = None

    def __init__(self, run_time: Time):
        self.run_time = run_time

    def compute_statistics(self) -> None:
        """
        Computes and prints basic statistics about the run record.

        This method calculates and prints the number of detected peaks, the number of events,
        and the duration of the run time. It provides a quick overview of the run record's contents.
        """
        self.number_of_scatterer_sent = (
            len(self.events) if self.events is not None else 0
        )
        self.number_of_events_detected = len(self.triggered_analog.groupby("SegmentID"))
        self.rate_of_scatterer = self.number_of_scatterer_sent / self.run_time
