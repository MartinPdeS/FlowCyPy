import logging
import warnings
from typing import Optional, Union, List
from MPSPlots.styles import mps
import pandas as pd
import numpy as np
from FlowCyPy import units
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
from FlowCyPy import helper
from FlowCyPy.triggered_acquisition import TriggeredAcquisitions
from FlowCyPy.dataframe_subclass import TriggeredAcquisitionDataFrame

class DataAccessor:
    def __init__(self, outer):
        self._outer = outer


class Acquisition:
    """
    Represents a flow cytometry experiment, including runtime, dataframes, logging, and visualization.

    Attributes
    ----------
    run_time : units.second
        Total runtime of the experiment.
    scatterer_dataframe : pd.DataFrame
        DataFrame containing scatterer data, indexed by population and time.
    detector_dataframe : pd.DataFrame
        DataFrame containing detector signal data, indexed by detector and time.
    """

    def __init__(self, run_time: units.second, cytometer: object, scatterer_dataframe: pd.DataFrame, detector_dataframe: pd.DataFrame):
        """
        Initializes the Experiment instance.

        Parameters
        ----------
        run_time : Quantity
            Total runtime of the experiment.
        scatterer_dataframe : pd.DataFrame
            DataFrame with scatterer data.
        detector_dataframe : pd.DataFrame
            DataFrame with detector signal data.
        """
        self.cytometer = cytometer
        self.logger = self.LoggerInterface(self)

        self.signal = detector_dataframe
        self.scatterer = scatterer_dataframe
        self.run_time = run_time

    @property
    def n_detectors(self) -> int:
        return len(self.signal.index.get_level_values('Detector').unique())

    def _get_trigger_indices(
        self,
        threshold: units.Quantity,
        trigger_detector_name: str = None,
        pre_buffer: int = 64,
        post_buffer: int = 64
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculate start and end indices for triggered segments, ensuring no retriggering
        occurs during an active buffer period.

        Parameters
        ----------
        threshold : units.Quantity
            The threshold value for triggering.
        trigger_detector_name : str, optional
            The name of the detector to use for the triggering signal.
        pre_buffer : int, optional
            Number of samples to include before the trigger point.
        post_buffer : int, optional
            Number of samples to include after the trigger point.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            The start and end indices of non-overlapping triggered segments.

        Raises
        ------
        ValueError
            If the specified detector is not found in the data.
        """
        if trigger_detector_name not in self.signal.index.get_level_values('Detector').unique():
            raise ValueError(f"Detector '{trigger_detector_name}' not found.")

        signal = self.signal.xs(trigger_detector_name)['Signal']
        trigger_signal = signal > threshold.to(signal.pint.units)

        crossings = np.where(np.diff(trigger_signal.astype(int)) == 1)[0]
        start_indices = np.clip(crossings - pre_buffer, 0, len(trigger_signal) - 1)
        end_indices = np.clip(crossings + post_buffer, 0, len(trigger_signal) - 1)

        # Suppress retriggering within an active buffer period
        suppressed_start_indices = []
        suppressed_end_indices = []

        last_end = -1
        for start, end in zip(start_indices, end_indices):
            if start > last_end:  # Ensure no overlap with the last active buffer
                suppressed_start_indices.append(start)
                suppressed_end_indices.append(end)
                last_end = end  # Update the end of the current active buffer

        return np.array(suppressed_start_indices), np.array(suppressed_end_indices)

    def run_triggering(self,
            threshold: units.Quantity,
            trigger_detector_name: str,
            pre_buffer: int = 64,
            post_buffer: int = 64,
            max_triggers: int = None) -> TriggeredAcquisitions:
        """
        Execute triggered acquisition analysis for signal data.

        This method identifies segments of signal data based on a triggering threshold
        and specified detector. It extracts segments of interest from the signal,
        including a pre-trigger buffer and post-trigger buffer.

        Parameters
        ----------
        threshold : units.Quantity
            The threshold value for triggering. Only signal values exceeding this threshold
            will be considered as trigger events.
        trigger_detector_name : str
            The name of the detector used for triggering. This determines which detector's
            signal is analyzed for trigger events.
        pre_buffer : int, optional
            The number of points to include before the trigger point in each segment.
            Default is 64.
        post_buffer : int, optional
            The number of points to include after the trigger point in each segment.
            Default is 64.
        max_triggers : int, optional
            The maximum number of triggers to process. If None, all triggers will be processed.
            Default is None.

        Raises
        ------
        ValueError
            If the specified `trigger_detector_name` is not found in the dataset.

        Warnings
        --------
        UserWarning
            If no triggers are detected for the specified threshold, the method raises a warning
            indicating that no signals met the criteria.

        Notes
        -----
        - The peak detection function `self.detect_peaks` is automatically called at the end of this method to analyze triggered segments.
        """
        self.threshold = threshold
        self.trigger_detector_name = trigger_detector_name
        start_indices, end_indices = self._get_trigger_indices(
            threshold, trigger_detector_name, pre_buffer, post_buffer
        )

        if max_triggers is not None:
            start_indices = start_indices[:max_triggers]
            end_indices = end_indices[:max_triggers]

        segments = []
        for detector_name in self.signal.index.get_level_values('Detector').unique():
            detector_data = self.signal.xs(detector_name)
            time, digitized, signal = detector_data['Time'], detector_data['DigitizedSignal'],  detector_data['Signal']


            for idx, (start, end) in enumerate(zip(start_indices, end_indices)):

                segment = pd.DataFrame({
                    'Time': time[start:end + 1],
                    'DigitizedSignal': digitized[start:end + 1],
                    'Signal': signal[start:end + 1],
                    'Detector': detector_name,
                    'SegmentID': idx
                })
                segments.append(segment)

        if len(segments) !=0:
            triggered_signal = TriggeredAcquisitionDataFrame(pd.concat(segments).set_index(['Detector', 'SegmentID']))
            triggered_signal.attrs['bit_depth'] = self.signal.attrs['bit_depth']
            triggered_signal.attrs['saturation_levels'] = self.signal.attrs['saturation_levels']
            triggered_signal.attrs['scatterer_dataframe'] = self.signal.attrs['scatterer_dataframe']

            return TriggeredAcquisitions(parent=self, dataframe=triggered_signal)
        else:
            warnings.warn(
                f"No signal were triggered during the run time, try changing the threshold. Signal min-max value is: {self.signal['Signal'].min().to_compact()}, {self.signal['Signal'].max().to_compact()}",
                UserWarning
            )

    class LoggerInterface:
        """
        A nested class for logging statistical information about the experiment.

        Methods
        -------
        scatterer()
            Logs statistics about the scatterer populations.
        detector()
            Logs statistics about the detector signals.
        """

        def __init__(self, experiment: object):
            self.experiment = experiment

        def scatterer(self, table_format: str = "grid") -> None:
            """
            Logs detailed information about scatterer populations.

            Parameters
            ----------
            table_format : str, optional
                The format for the table display (default: 'grid').
                Options include 'plain', 'github', 'grid', 'fancy_grid', etc.

            Returns
            -------
            None
                Logs scatterer population information, including refractive index, size, particle count,
                number of events, and time statistics.
            """
            logging.info("\n=== Scatterer Population Properties ===")

            # Collect general population data
            general_table_data = [
                self._get_population_properties(population)
                for population in self.experiment.scatterer.groupby("Population")
            ]
            general_headers = [
                "Name",
                "Refractive Index",
                "Medium Refractive Index",
                "Size",
                "Particle Count",
                "Number of Events",
                "Min Time Between Events",
                "Avg Time Between Events",
            ]

            formatted_general_table = tabulate(
                general_table_data, headers=general_headers, tablefmt=table_format, floatfmt=".4f"
            )
            logging.info("\n" + formatted_general_table)

        def _get_population_properties(self, population_group: tuple) -> List[Union[str, float]]:
            """
            Extracts key properties of a scatterer population for the general properties table.

            Parameters
            ----------
            population_group : tuple
                A tuple containing the population name and its corresponding DataFrame.

            Returns
            -------
            list
                List of scatterer properties: [name, refractive index, medium refractive index, size,
                particle count, number of events, min time between events, avg time between events].
            """
            population_name, population_df = population_group

            name = population_name
            refractive_index = f"{population_df['RefractiveIndex'].mean():~P}"
            medium_refractive_index = f"{self.experiment.run_time:~P}"  # Replace with actual medium refractive index if stored elsewhere
            size = f"{population_df['Size'].mean():~P}"
            particle_count = len(population_df)
            num_events = particle_count

            min_delta_position = population_df["Time"].diff().abs().min()
            avg_delta_position = population_df["Time"].diff().mean()

            return [
                name,
                refractive_index,
                medium_refractive_index,
                size,
                particle_count,
                num_events,
                min_delta_position,
                avg_delta_position,
            ]

        def detector(self, table_format: str = "grid", include_totals: bool = True) -> None:
            """
            Logs statistics about detector signals.

            Parameters
            ----------
            table_format : str, optional
                The format for the table display (default: 'grid').
                Options include 'plain', 'github', 'grid', 'fancy_grid', etc.
            include_totals : bool, optional
                If True, logs the total number of events across all detectors (default: True).

            Returns
            -------
            None
                Logs details about detector signals, including event counts,
                timing statistics, and mean event rates.
            """
            logging.info("\n=== Detector Signal Statistics ===")

            # Compute statistics for each detector
            df = self.experiment.signal
            table_data = [
                self._get_detector_stats(detector_name, df.xs(detector_name, level="Detector"))
                for detector_name in df.index.levels[0]
            ]
            headers = [
                "Detector",
                "Number of Acquisition",
                "First Event Time",
                "Last Event Time",
                "Time Between Events",
            ]

            formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".3f")
            logging.info("\n" + formatted_table)

            if include_totals:
                total_events = sum(stat[1] for stat in table_data)
                logging.info(f"\nTotal number of events detected across all detectors: {total_events}")

        def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> list:
            """
            Computes statistics for a detector.

            Parameters
            ----------
            detector_name : str
                Name of the detector.
            group : pd.DataFrame
                DataFrame containing the detector data.

            Returns
            -------
            list
                List of computed statistics: [detector_name, num_events, first_event_time,
                last_event_time, avg_time_between_events, min_time_between_events, mean_event_rate].
            """
            num_acquisition = len(group["Time"])
            first_event_time = group["Time"].min()
            last_event_time = group["Time"].max()

            time_diffs = group["Time"].diff().dropna()
            time_between_events = time_diffs.mean()

            return [
                detector_name,
                num_acquisition,
                first_event_time,
                last_event_time,
                time_between_events,
            ]