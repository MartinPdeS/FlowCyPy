import logging
from typing import Optional, Union, List
from MPSPlots.styles import mps
import pandas as pd
import numpy as np
from FlowCyPy import units
from FlowCyPy.units import Quantity
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import warnings
from FlowCyPy import helper

class DataAccessor:
    def __init__(self, outer):
        self._outer = outer


class Acquisition:
    """
    Represents a flow cytometry experiment, including runtime, dataframes, logging, and visualization.

    Attributes
    ----------
    run_time : Quantity
        Total runtime of the experiment.
    scatterer_dataframe : pd.DataFrame
        DataFrame containing scatterer data, indexed by population and time.
    detector_dataframe : pd.DataFrame
        DataFrame containing detector signal data, indexed by detector and time.
    """

    def __init__(self, run_time: Quantity, cytometer: object, scatterer_dataframe: pd.DataFrame, detector_dataframe: pd.DataFrame):
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

        self.data = DataAccessor(self)
        self.plot = self.PlotInterface(self)
        self.logger = self.LoggerInterface(self)

        self.data.continuous = detector_dataframe
        self.data.scatterer = scatterer_dataframe
        self.run_time = run_time

    @property
    def n_detectors(self) -> int:
        return len(self.data.continuous.index.get_level_values('Detector').unique())

    def detect_peaks(self, multi_peak_strategy: str = 'max') -> None:
        """
        Detects peaks for each segment and stores results in a DataFrame.

        Parameters
        ----------
        multi_peak_strategy : str, optional
            Strategy for handling multiple peaks in a segment. Options are:
            - 'mean': Take the average of the peaks in the segment.
            - 'max': Take the maximum peak in the segment.
            - 'sum': Sum all peaks in the segment.
            - 'discard': Remove entries with multiple peaks.
            - 'keep': Keep all peaks without aggregation.
            Default is 'mean'.
        """
        if multi_peak_strategy not in {'max', }:
            raise ValueError("Invalid multi_peak_strategy. Choose from 'max'.")

        def process_segment(segment):
            signal = segment['DigitizedSignal'].values
            time = segment['Time'].values
            peaks, properties = find_peaks(signal, width=1)

            return pd.DataFrame({
                "SegmentID": segment.name[1],
                "Detector": segment.name[0],
                "Height": signal[peaks],
                "Time": time[peaks],
                **{k: v for k, v in properties.items()}
            })

        # Process peaks for each group
        results = self.data.triggered.groupby(level=['Detector', 'SegmentID']).apply(process_segment)
        results = results.reset_index(drop=True)

        # Check for multiple peaks and issue a warning
        peak_counts = results.groupby(['Detector', 'SegmentID']).size()
        multiple_peak_segments = peak_counts[peak_counts > 1]
        if not multiple_peak_segments.empty:
            warnings.warn(
                f"Multiple peaks detected in the following segments: {multiple_peak_segments.index.tolist()}",
                UserWarning
            )

        _temp = results.reset_index()[['Detector', 'SegmentID', 'Height']].pint.dequantify().droplevel('unit', axis=1)

        self.data.peaks = (
            results.reset_index()
            .loc[_temp.groupby(['Detector', 'SegmentID'])['Height'].idxmax()]
            .set_index(['Detector', 'SegmentID'])
        )

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
        if trigger_detector_name not in self.data.continuous.index.get_level_values('Detector').unique():
            raise ValueError(f"Detector '{trigger_detector_name}' not found.")

        signal = self.data.continuous.xs(trigger_detector_name)['Signal']
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
            max_triggers: int = None) -> None:
        """
        Executes the triggered acquisition analysis.

        Parameters
        ----------
        threshold : units.Quantity
            Trigger threshold value.
        trigger_detector_name : str, optional
            Detector used for triggering, by default None.
        custom_trigger : np.ndarray, optional
            Custom trigger array, by default None.
        pre_buffer : int, optional
            Points before trigger, by default 64.
        post_buffer : int, optional
            Points after trigger, by default 64.
        max_triggers : int, optional
            Maximum number of triggers to process, by default None.
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
        for detector_name in self.data.continuous.index.get_level_values('Detector').unique():
            detector_data = self.data.continuous.xs(detector_name)
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
            self.data.triggered = pd.concat(segments).set_index(['Detector', 'SegmentID'])
        else:
            warnings.warn(
                f"No signal were triggered during the run time, try changing the threshold. Signal min-max value is: {self.data.continuous['Signal'].min().to_compact()}, {self.data.continuous['Signal'].max().to_compact()}",
                UserWarning
            )

        self.detect_peaks()

    def classify_dataset(self, classifier: object, features: List[str], detectors: list[str]) -> None:
        self.data.peaks = self.data.peaks.unstack('Detector')
        self.classifier = classifier

        self.classifier.run(
            dataframe=self.data.peaks,
            features=features,
            detectors=detectors
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
                for population in self.experiment.data.scatterer.groupby("Population")
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
            df = self.experiment.data.continuous
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


    class PlotInterface:
        """
        A nested class for handling visualization and plotting.

        Methods
        -------
        signals(figure_size=(10, 6), add_peak_locator=False, show=True)
            Visualizes raw signals for detector channels and scatterer distributions.
        coupling_distribution(log_scale=False, show=True, equal_limits=False, save_path=None)
            Plots the density distribution of optical coupling between two detector channels.
        """

        def __init__(self, acquisition: object):
            self.acquisition = acquisition

        def signals(self, figure_size: tuple = (10, 6), show: bool = True) -> None:
            """
            Visualizes raw signals for all detector channels and the scatterer distribution.

            Parameters
            ----------
            figure_size : tuple, optional
                Size of the plot (default: (10, 6)).
            add_peak_locator : bool, optional
                Adds peak location markers to the signals if True (default: False).
            show : bool, optional
                Displays the plot immediately if True (default: True).
            """
            n_plots = self.acquisition.n_detectors + 1

            time_units = self.acquisition.data.continuous.Time.max().to_compact().units

            with plt.style.context(mps):
                fig, axes = plt.subplots(
                    ncols=1,
                    nrows=n_plots,
                    figsize=figure_size,
                    sharex=True,
                    height_ratios=[1] * (n_plots - 1) + [0.5],
                )

            for ax, (detector_name, group) in zip(axes[:-1], self.acquisition.data.continuous.groupby("Detector")):
                detector = self.get_detector(detector_name)

                ax.step(group["Time"].pint.to(time_units), group["DigitizedSignal"], label="Digitized Signal", where='mid')
                ax.set_ylabel(detector_name)
                ax.set_ylim([0, self.acquisition.cytometer.signal_digitizer._bit_depth])

                ax2 = ax.twinx()
                ax2_x = self.acquisition.data.continuous.loc[detector_name, 'Time']
                ax2_y = self.acquisition.data.continuous.loc[detector_name, 'Signal']
                ax2_y_units = ax2_y.max().to_compact().units
                ax2.plot(
                    ax2_x.pint.to(time_units),
                    ax2_y.pint.to(ax2_y_units),
                    color='black',
                    linewidth=1,
                    linestyle='-',
                    label='Continuous signal',
                    zorder=0,
                )

                ax2.set_ylim(detector._saturation_levels)

            self._add_event_to_ax(ax=axes[-1], time_units=time_units)

            axes[-1].set_xlabel(f"Time [{time_units}]")
            if show:
                plt.show()

        def _add_event_to_ax(self, ax: plt.Axes, time_units: units.Quantity, palette: str = 'tab10') -> None:
            unique_populations = self.acquisition.data.scatterer.index.get_level_values('Population').unique()
            color_mapping = dict(zip(unique_populations, sns.color_palette(palette, len(unique_populations))))

            for population_name, group in self.acquisition.data.scatterer.groupby('Population'):
                x = group.Time.pint.to(time_units)
                color = color_mapping[population_name]
                ax.vlines(x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), label=population_name, color=color)

            ax.tick_params(axis='y', left=False, labelleft=False)

            ax.get_yaxis().set_visible(False)
            ax.set_xlabel(f"Time [{time_units}]")

            ax.legend()

        @helper.plot_sns
        def coupling_distribution(self, x_detector: str, y_detector: str, equal_limits: bool = False) -> None:
            """
            Plots the density distribution of optical coupling between two detector channels.

            Parameters
            ----------
            log_scale : bool, optional
                Applies logarithmic scaling to axes if True (default: False).
            show : bool, optional
                Displays the plot immediately if True (default: True).
            equal_limits : bool, optional
                Ensures equal axis limits if True (default: False).
            save_path : str, optional
                Saves the plot to the specified path if provided.
            """
            df = self.acquisition.data.scatterer

            x_units = df[x_detector].max().to_compact().units
            y_units = df[y_detector].max().to_compact().units
            x = df[x_detector].pint.to(x_units)
            y = df[y_detector].pint.to(y_units)

            with plt.style.context(mps):
                grid = sns.jointplot(data=df, x=x, y=y, hue="Population", alpha=0.8)

            grid.ax_joint.set_xlabel(f"Signal {x_detector} [{x_units}]")
            grid.ax_joint.set_ylabel(f"Signal {y_detector} [{y_units}]")

            grid.figure.suptitle("Theoretical coupling distribution")

            return grid

        @helper.plot_sns
        def scatterer(self, alpha: float = 0.8, bandwidth_adjust: float = 1, log_scale: bool = False, color_palette: Optional[Union[str, dict]] = None) -> None:
            """
            Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn jointplot.

            Parameters
            ----------
            ax : matplotlib.axes.Axes, optional
                Existing matplotlib axes to plot on. If `None`, a new figure and axes are created. Default is `None`.
            show : bool, optional
                If `True`, displays the plot after creation. Default is `True`.
            alpha : float, optional
                Transparency level for the scatter plot points, ranging from 0 (fully transparent) to 1 (fully opaque). Default is 0.8.
            bandwidth_adjust : float, optional
                Bandwidth adjustment factor for the kernel density estimate of the marginal distributions. Higher values produce smoother density estimates. Default is 1.
            color_palette : str or dict, optional
                The color palette to use for the hue in the scatterplot. Can be a seaborn palette name
                (e.g., 'viridis', 'coolwarm') or a dictionary mapping hue levels to specific colors. Default is None.

            Returns
            -------
            None
                This function does not return any value. It either displays the plot (if `show=True`) or simply creates it for later use.

            Notes
            -----
            This method resets the index of the internal dataframe and extracts units from the 'Size' column.
            The plot uses the specified matplotlib style (`mps`) for consistent styling.

            """
            df_reset = self.acquisition.data.scatterer.reset_index()

            if len(df_reset) == 1:
                return

            x_unit = df_reset['Size'].pint.units

            with plt.style.context(mps):
                grid = sns.jointplot(
                    data=df_reset,
                    x='Size',
                    y='RefractiveIndex',
                    hue='Population',
                    palette=color_palette,
                    kind='scatter',
                    alpha=alpha,
                    marginal_kws=dict(bw_adjust=bandwidth_adjust)
                )

            grid.figure.suptitle("Scatterer sampling distribution")

            grid.ax_joint.set_xlabel(f"Size [{x_unit}]")

            return grid

        @helper.plot_sns
        def peaks(self, x_detector: str, y_detector: str, signal: str = 'Height', bandwidth_adjust: float = 0.8) -> None:
            """
            Plot the joint KDE distribution of the specified signal between two detectors using seaborn,
            optionally overlaying scatter points.

            Parameters
            ----------
            x_detector : str
                Name of the detector to use for the x-axis.
            y_detector : str
                Name of the detector to use for the y-axis.
            signal : str, optional
                The signal column to plot, by default 'Height'.
            bandwidth_adjust : float, optional
                Bandwidth adjustment factor for KDE, by default 0.8.
            """
            # Filter to only include rows for the specified detectors
            x_data = self.acquisition.data.peaks.loc[x_detector, signal]
            y_data = self.acquisition.data.peaks.loc[y_detector, signal]

            x_units = x_data.pint.units
            y_units = y_data.pint.units

            with plt.style.context(mps):
                # Create joint KDE plot with scatter points overlay
                grid = sns.jointplot(x=x_data, y=y_data, kind='kde', fill=True, cmap="Blues",
                    joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
                )

            grid.figure.suptitle("Peaks properties")
            grid.ax_joint.scatter(x_data, y_data, color='C1', alpha=0.6)

            grid.set_axis_labels(f"{signal} ({x_detector}) [{x_units}]", f"{signal} ({y_detector}) [{y_units}]", fontsize=12)

            return grid

        def trigger(self, show: bool = True) -> None:
            """Plot detected peaks on signal segments."""
            n_plots = self.acquisition.n_detectors + 1
            with plt.style.context(mps):
                _, axes = plt.subplots(
                    nrows=n_plots,
                    ncols=1,
                    height_ratios=[1] * (n_plots - 1) + [0.5],
                    figsize=(10, 6),
                    sharex=True,
                    constrained_layout=True
                )

            time_units = self.acquisition.data.triggered['Time'].max().to_compact().units

            for ax, (detector_name, group) in zip(axes, self.acquisition.data.triggered.groupby(level=['Detector'])):
                detector = self.get_detector(detector_name)

                ax.set_ylabel(detector_name)

                for _, sub_group in group.groupby(level=['SegmentID']):
                    x = sub_group['Time'].pint.to(time_units)
                    digitized = sub_group['DigitizedSignal']
                    ax.step(x, digitized, where='mid', linewidth=2)
                    ax.set_ylim([0, self.acquisition.cytometer.signal_digitizer._bit_depth])

                ax2 = ax.twinx()
                ax2_x = self.acquisition.data.continuous.loc[detector_name, 'Time']
                ax2_y = self.acquisition.data.continuous.loc[detector_name, 'Signal']
                ax2_y_units = ax2_y.max().to_compact().units
                ax2.plot(
                    ax2_x.pint.to(time_units),
                    ax2_y.pint.to(ax2_y_units),
                    color='black',
                    linewidth=1,
                    linestyle='-',
                    label='Continuous signal',
                    zorder=0,
                )

                if detector_name == self.acquisition.trigger_detector_name:
                    ax2.axhline(y=self.acquisition.threshold.to(ax2_y_units), color='black', linestyle='--', label='Trigger')

                ax2.set_ylim(detector._saturation_levels)

                ax2.legend()


            for ax, (detector_name, group) in zip(axes, self.acquisition.data.peaks.groupby(level=['Detector'], axis=0)):
                x = group['Time'].pint.to(time_units)
                y = group['Height']
                ax.scatter(x, y, color='C1')

            self._add_event_to_ax(ax=axes[-1], time_units=time_units)

            if show:
                plt.show()

        @helper.plot_sns
        def classifier(self, feature: str, x_detector: str, y_detector: str) -> None:
            """
            Visualize the classification of peaks using a scatter plot.

            Parameters
            ----------
            feature : str
                The feature to classify (e.g., 'Height', 'Width', 'Area').
            x_detector : str
                The detector to use for the x-axis.
            y_detector : str
                The detector to use for the y-axis.

            Raises
            ------
            ValueError
                If the 'Label' column is missing in the data, suggesting that
                the `classify_dataset` method must be called first.
            """
            # Check if 'Label' exists in the dataset
            if 'Label' not in self.acquisition.data.peaks.columns:
                raise ValueError(
                    "The 'Label' column is missing. Ensure the dataset has been classified "
                    "by calling the `classify_dataset` method before using `classifier`."
                )

            # Set the plotting style
            with plt.style.context(mps):
                # Generate a scatter plot using seaborn's jointplot
                grid = sns.jointplot(
                    data=self.acquisition.data.peaks,
                    x=(feature, x_detector),
                    y=(feature, y_detector),
                    hue='Label',
                )

            grid.figure.suptitle('Event classification')

            return grid

        def get_detector(self, name: str):
            for detector in self.acquisition.cytometer.detectors:
                if detector.name == name:
                    return detector
