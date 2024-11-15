import logging
from tabulate import tabulate
import pandas as pd
from typing import List, Union, Optional


class SimulationLogger:
    """
    Logs key statistics about the simulated pulse events for each detector.
    Provides an organized summary of simulation events, including total events,
    average time between events, first and last event times, and minimum time between events.

    Parameters
    ----------
    detectors : list
        List of detector objects, each with a 'name' attribute and relevant pulse data.
    pulse_dataframe : pd.DataFrame
        DataFrame containing the pulse event data with a 'Centers' column for each detector.
    """

    def __init__(self, detectors: List, pulse_dataframe: pd.DataFrame):
        self.detectors = detectors
        self.pulse_dataframe = pulse_dataframe

    def log_statistics(self, include_totals: bool = True, table_format: str = "grid") -> None:
        """
        Logs summary statistics for each detector in a formatted table.

        Parameters
        ----------
        include_totals : bool, optional
            If True, logs the total number of events across all detectors (default is True).
        table_format : str, optional
            The format for the table display (default is 'grid').
            Options include 'plain', 'github', 'grid', 'fancy_grid', etc., as supported by tabulate.
        """
        logging.info("\n=== Simulation Statistics Summary ===")

        table_data = [self._get_detector_stats(detector) for detector in self.detectors]
        headers = ["Detector", "Number of Events", "Saturated", "First Event Time", "Last Event Time",
                   "Avg Time Between Events", "Min Time Between Events"]

        formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".3f")
        logging.info("\n" + formatted_table)

        if include_totals:
            total_events = sum(stat[1] for stat in table_data)  # Sum of events from all detectors
            logging.info(f"\nTotal number of events detected across all detectors: {total_events}")

    def _get_detector_stats(self, detector) -> List[Union[str, int, Optional[str]]]:
        """
        Computes statistics for a single detector.

        Parameters
        ----------
        detector : object
            A detector object with 'name' and pulse event data attributes.

        Returns
        -------
        list
            List of computed statistics: [detector name, num_events, first_event_time, last_event_time,
            avg_time_between_events, min_time_between_events]
        """
        centers = self.pulse_dataframe['Centers']
        num_events = len(centers)

        if num_events > 1:
            centers_sorted = centers.sort_values()
            time_diffs = centers_sorted.diff().dropna()  # Time differences between events
            avg_time_between_events = self._format_time(time_diffs.mean())
            min_time_between_events = self._format_time(time_diffs.min())
        else:
            avg_time_between_events = "N/A"
            min_time_between_events = "N/A"

        first_event_time = self._format_time(centers.min()) if num_events > 0 else "N/A"
        last_event_time = self._format_time(centers.max()) if num_events > 0 else "N/A"

        return [
            detector.name,
            num_events,
            detector.is_saturated,  # Was the detector saturated at some point
            first_event_time,
            last_event_time,
            avg_time_between_events,
            min_time_between_events
        ]

    def _format_time(self, time_value) -> str:
        """
        Formats a time value for display, converting to compact notation if available.

        Parameters
        ----------
        time_value : pint.Quantity or pd.Timestamp or float
            The time value to format.

        Returns
        -------
        str
            The formatted time string.
        """
        try:
            return f"{time_value.to_compact():.4~P}"
        except AttributeError:
            return f"{time_value:.4f}" if pd.notnull(time_value) else "N/A"
