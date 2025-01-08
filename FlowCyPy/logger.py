import logging
from tabulate import tabulate
import pandas as pd
from typing import List, Union, Optional
from FlowCyPy import units


class EventCorrelatorLogger:
    """
    Logs key statistics and properties for the EventCorrelator class, including peak detection statistics
    for each detector and coincident event information.

    Parameters
    ----------
    correlator : EventCorrelator
        An instance of the EventCorrelator class to log statistics for.
    """

    def __init__(self, correlator: object):
        """
        Initializes the EventCorrelatorLogger with the correlator instance.

        Parameters
        ----------
        correlator : EventCorrelator
            An instance of EventCorrelator to log properties and statistics for.
        """
        # self.run_time = run_time
        self.correlator = correlator
        self.detectors = correlator.cytometer.detectors
        self.coincidence = getattr(correlator, "coincidence", None)

    def log_statistics(self, table_format: str = "grid") -> None:
        """
        Logs statistics for each detector, including number of peaks, time between peaks, and peak times.

        Parameters
        ----------
        table_format : str, optional
            The format for the table display (default is 'grid').
        """
        logging.info("\n=== Detector Statistics ===")

        table_data = [self._get_detector_stats(detector) for detector in self.detectors]
        headers = [
            "Detector",
            "Number of Peaks",
            "First Peak Time",
            "Last Peak Time",
            "Avg Time Between Peaks",
            "Min Time Between Peaks",
            'Measured Concentration'
        ]

        formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".4f")
        logging.info("\n" + formatted_table)

    def _get_detector_stats(self, detector) -> List[Union[str, int, str]]:
        """
        Computes statistics for a single detector.

        Parameters
        ----------
        detector : object
            A detector object with peak detection data.

        Returns
        -------
        list
            List of statistics: [detector name, number of peaks, first peak time, last peak time,
            average time between peaks, minimum time between peaks].
        """
        group = self.correlator.dataframe.xs(detector.name, level="Detector")
        num_events = len(group)

        if num_events > 1:
            times = group['PeakTimes'].sort_values()
            time_diffs = times.diff().dropna()
            avg_time_between_peaks = f"{time_diffs.mean().to_compact():.4~P}"
            min_time_between_peaks = f"{time_diffs.min().to_compact():.4~P}"
            # volume = self.correlator.cytometer.flow_cell.get_volume(self.run_time)
            # measured_concentration = num_events * units.particle / volume.to(units.milliliter)
        else:
            avg_time_between_peaks = "N/A"
            min_time_between_peaks = "N/A"
            measured_concentration = "N/A"

        first_peak_time = f"{group['PeakTimes'].min().to_compact():.4~P}" if num_events > 0 else "N/A"
        last_peak_time = f"{group['PeakTimes'].max().to_compact():.4~P}" if num_events > 0 else "N/A"

        return [detector.name, num_events, first_peak_time, last_peak_time, avg_time_between_peaks, min_time_between_peaks]  #, measured_concentration]

    def log_coincidence_statistics(self, table_format: str = "grid") -> None:
        """
        Logs statistics about coincident events detected between detectors.

        Parameters
        ----------
        table_format : str, optional
            The format for the table display (default is 'grid').
        """
        if self.coincidence is None or self.coincidence.empty:
            logging.warning("No coincidence events to log.")
            return

        logging.info("\n=== Coincidence Event Statistics ===")

        table_data = self._get_coincidence_stats()
        headers = ["Detector 1 Event", "Detector 2 Event", "Time Difference"]

        formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".4f")
        logging.info("\n" + formatted_table)

    def _get_coincidence_stats(self) -> List[List[Union[str, float]]]:
        """
        Extracts statistics about coincident events.

        Returns
        -------
        list
            List of coincident event statistics: [detector 1 event, detector 2 event, time difference].
        """
        coinc_df = self.coincidence.reset_index()
        time_diffs = (
            coinc_df[self.detectors[0].name, 'PeakTimes'] -
            coinc_df[self.detectors[1].name, 'PeakTimes']
        ).abs()

        return [
            [
                row[self.detectors[0].name, 'PeakTimes'],
                row[self.detectors[1].name, 'PeakTimes'],
                time_diff.to_compact()
            ]
            for row, time_diff in zip(coinc_df.itertuples(), time_diffs)
        ]
