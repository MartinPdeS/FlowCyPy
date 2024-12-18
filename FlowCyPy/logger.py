import logging
from tabulate import tabulate
import pandas as pd
from typing import List, Union, Optional
from FlowCyPy.units import particle, milliliter


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
            measured_concentration = num_events * particle / self.correlator.cytometer.scatterer.flow_cell.volume.to(milliliter)
        else:
            avg_time_between_peaks = "N/A"
            min_time_between_peaks = "N/A"
            measured_concentration = "N/A"

        first_peak_time = f"{group['PeakTimes'].min().to_compact():.4~P}" if num_events > 0 else "N/A"
        last_peak_time = f"{group['PeakTimes'].max().to_compact():.4~P}" if num_events > 0 else "N/A"

        return [detector.name, num_events, first_peak_time, last_peak_time, avg_time_between_peaks, min_time_between_peaks, measured_concentration]

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


class ScattererLogger:
    """
    Logs key properties of scatterers in formatted tables.

    Parameters
    ----------
    scatterers : list
        List of scatterer instances to log properties for.
    """

    def __init__(self, scatterers: List[object]):
        """
        Initializes the ScattererLogger with the scatterers to log.

        Parameters
        ----------
        scatterers : list
            List of scatterer objects.
        """
        self.scatterers = scatterers

    def log_properties(self, table_format: str = "grid") -> None:
        """
        Logs properties of scatterers in formatted tables.

        Parameters
        ----------
        table_format : str, optional
            The format for the table display (default is 'grid').
            Options include 'plain', 'github', 'grid', 'fancy_grid', etc., as supported by tabulate.
        """
        logging.info("\n=== Scatterer Properties Summary ===")

        # First table: General properties
        general_table_data = [self._get_population_properties(population) for population in self.scatterers.populations]
        general_headers = [
            "Name",
            "Refractive Index",
            "Medium Refractive Index",
            "Size",
            "Particle Count",
            "Number of Events",
            "Min Time Between Events",
            "Avg Time Between Events"
        ]
        formatted_general_table = tabulate(general_table_data, headers=general_headers, tablefmt=table_format, floatfmt=".4f")
        logging.info("\n" + formatted_general_table)

    def _get_population_properties(self, population: object) -> List[Union[str, float]]:
        """
        Extracts key properties of a scatterer for the general properties table.

        Parameters
        ----------
        population : object
            A scatterer object with properties such as name, refractive index, size, etc.

        Returns
        -------
        list
            List of scatterer properties: [name, refractive index, size, concentration, number of events].
        """
        name = population.name
        refractive_index = f"{population.refractive_index}"
        medium_refractive_index = f"{self.scatterers.medium_refractive_index}"
        size = f"{population.size}"
        concentration = f"{population.particle_count}"
        num_events = population.n_events

        min_delta_position = abs(population.dataframe['Time'].diff()).min().to_compact()
        avg_delta_position = population.dataframe['Time'].diff().mean().to_compact()

        return [name, refractive_index, medium_refractive_index, size, concentration, num_events, avg_delta_position, min_delta_position]


class SimulationLogger:
    """
    Logs key statistics about the simulated pulse events for each detector.
    Provides an organized summary of simulation events, including total events,
    average time between events, first and last event times, and minimum time between events.

    Parameters
    ----------
    cytometer : object
        The cytometer instance which containes info on detected pulse.
    """

    def __init__(self, cytometer: object):
        self.cytometer = cytometer
        self.detectors = cytometer.detectors
        self.pulse_dataframe = cytometer.pulse_dataframe

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
        headers = [
            "Detector",
            "Number of Events",
            "Saturated",
            "First Event Time",
            "Last Event Time",
            "Avg Time Between Events",
            "Min Time Between Events",
            "Mean event rate"
        ]

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
            avg_time_between_events, min_time_between_events, mean_detection_rate]
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

        mean_event_rate = (num_events / self.cytometer.scatterer.flow_cell.run_time).to('Hz')

        return [
            detector.name,
            num_events,
            detector.is_saturated,  # Was the detector saturated at some point
            first_event_time,
            last_event_time,
            avg_time_between_events,
            min_time_between_events,
            mean_event_rate
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
