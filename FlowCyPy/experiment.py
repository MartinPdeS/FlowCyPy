import logging
from typing import Optional, Union, List
from MPSPlots.styles import mps
import pandas as pd
from FlowCyPy.units import Quantity
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
from dataclasses import dataclass


class ContinuousAcquisition:
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

    def __init__(self, run_time: Quantity, scatterer_dataframe: pd.DataFrame, detector_dataframe: pd.DataFrame):
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
        self.run_time = run_time
        self.scatterer_dataframe = scatterer_dataframe
        self.detector_dataframe = detector_dataframe
        self.plot = self.PlotInterface(self)
        self.logger = self.LoggerInterface(self)

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

        def __init__(self, experiment: "Experiment"):
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
                for population in self.experiment.scatterer_dataframe.groupby("Population")
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
            df = self.experiment.detector_dataframe
            table_data = [
                self._get_detector_stats(detector_name, df.xs(detector_name, level="Detector"))
                for detector_name in df.index.levels[0]
            ]
            headers = [
                "Detector",
                "Number of Events",
                "First Event Time",
                "Last Event Time",
                "Avg Time Between Events",
                "Min Time Between Events",
                "Mean Event Rate",
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
            num_events = len(group["Time"])
            first_event_time = group["Time"].min()
            last_event_time = group["Time"].max()

            if num_events > 1:
                time_diffs = group["Time"].diff().dropna()
                avg_time_between_events = time_diffs.mean()
                min_time_between_events = time_diffs.min()
            else:
                avg_time_between_events = "N/A"
                min_time_between_events = "N/A"

            mean_event_rate = num_events / self.experiment.run_time

            return [
                detector_name,
                num_events,
                first_event_time,
                last_event_time,
                avg_time_between_events,
                min_time_between_events,
                mean_event_rate,
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

        def __init__(self, experiment: "Experiment"):
            self.experiment = experiment

        def signals(self, figure_size: tuple = (10, 6), add_peak_locator: bool = False, show: bool = True) -> None:
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
            df = self.experiment.detector_dataframe
            n_detectors = len(df.index.levels[0])

            time_units = df.Time.max().to_compact().units

            with plt.style.context(mps):
                fig, axes = plt.subplots(
                    ncols=1,
                    nrows=n_detectors + 1,
                    figsize=figure_size,
                    sharex=True,
                    gridspec_kw={"height_ratios": [1] * n_detectors + [0.4]}
                )

            for ax, (name, group) in zip(axes[:-1], df.groupby("Detector")):
                ax.step(group["Time"].pint.to(time_units), group["DigitizedSignal"], label="Digitized Signal")
                ax.set_ylabel(name)

            scatter_df = self.experiment.scatterer_dataframe
            palette = plt.get_cmap("Set2")

            for idx, (population_name, group) in enumerate(scatter_df.groupby("Population")):
                x = group["Time"]

                axes[-1].vlines(
                    x=x.pint.to(time_units),
                    ymin=0,
                    ymax=1,
                    transform=axes[-1].get_xaxis_transform(),
                    color=palette(idx % 8),
                    linestyle="--",
                    lw=1.5,
                    label=population_name
                )
                axes[-1].set_xlabel(f"Time [{time_units}]")
                axes[-1].get_yaxis().set_visible(False)

            if show:
                plt.show()

        def coupling_distribution(self, log_scale: bool = False, show: bool = True, equal_limits: bool = False, save_path: str = None) -> None:
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
            df = self.experiment.scatterer_dataframe
            detector_names = self.experiment.detector_dataframe.index.levels[0]

            with plt.style.context(mps):
                joint_plot = sns.jointplot(
                    data=df,
                    x=f"detector: {detector_names[0]}",
                    y=f"detector: {detector_names[1]}",
                    hue="Population",
                    alpha=0.8
                )

            if log_scale:
                joint_plot.ax_joint.set_xscale("log")
                joint_plot.ax_joint.set_yscale("log")

            if equal_limits:
                x_data = df[f"detector: {detector_names[0]}"]
                y_data = df[f"detector: {detector_names[1]}"]
                min_limit = min(x_data.min(), y_data.min())
                max_limit = max(x_data.max(), y_data.max())
                joint_plot.ax_joint.set_xlim(min_limit, max_limit)
                joint_plot.ax_joint.set_ylim(min_limit, max_limit)

            if save_path:
                joint_plot.figure.savefig(save_path, dpi=300, bbox_inches="tight")
                logging.info(f"Plot saved to {save_path}")

            if show:
                plt.show()

        def scatterer(self, show: bool = True, alpha: float = 0.8, bandwidth_adjust: float = 1, log_scale: bool = False, color_palette: Optional[Union[str, dict]] = None) -> None:
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
            log_scale : bool, optional
                If `True`, applies a logarithmic scale to both axes of the joint plot and their marginal distributions. Default is `False`.
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
            df = self.experiment.scatterer_dataframe

            df_reset = df.reset_index()

            if len(df_reset) == 1:
                return

            x_unit = df_reset['Size'].pint.units

            with plt.style.context(mps):
                g = sns.jointplot(
                    data=df_reset,
                    x='Size',
                    y='RefractiveIndex',
                    hue='Population',
                    palette=color_palette,
                    kind='scatter',
                    alpha=alpha,
                    marginal_kws=dict(bw_adjust=bandwidth_adjust)
                )

            g.ax_joint.set_xlabel(f"Size [{x_unit}]")

            if log_scale:
                g.ax_joint.set_xscale('log')
                g.ax_joint.set_yscale('log')
                g.ax_marg_x.set_xscale('log')
                g.ax_marg_y.set_yscale('log')

            plt.tight_layout()

            if show:
                plt.show()




@dataclass
class TriggeredAcquisition:
    """
    A class for analyzing triggered signal acquisition data.

    Attributes
    ----------
    data : pd.DataFrame
        Multi-index DataFrame with detector and segment as levels,
        containing time and signal columns.
    """
    data: pd.DataFrame

    def plot(self, num_segments: int = 5) -> None:
        """
        Plots the first few segments of signal data for each detector using subplots.

        Parameters
        ----------
        num_segments : int, optional
            Number of segments to plot for each detector, by default 5.
        """
        # Get unique detectors
        detectors = self.data.index.get_level_values('Detector').unique()
        num_detectors = len(detectors)

        with plt.style.context(mps):
            # Create subplots
            fig, axes = plt.subplots(
                num_detectors, 1,
                figsize=(10, 3 * num_detectors),
                sharex=True, sharey=True,
                constrained_layout=True
            )

        # Ensure axes is iterable for single detector case
        if num_detectors == 1:
            axes = [axes]

        # Plot each detector
        for ax, detector_name in zip(axes, detectors):
            detector_data = self.data.loc[detector_name]

            for segment_id, segment_data in detector_data.groupby(level='SegmentID'):
                if segment_id >= num_segments:
                    break
                ax.step(segment_data['Time'], segment_data['Signal'], label=f"Segment {segment_id}")

            # Add title and grid
            ax.grid(True)
            ax.legend()

        # Global plot adjustments
        fig.suptitle("Triggered Signal Segments", fontsize=16, y=1.02)
        axes[-1].set_xlabel("Time", fontsize=12)
        for ax in axes:
            ax.set_ylabel(f"Signal {detector_name}", fontsize=12)

        plt.tight_layout()
        plt.show()

    def compute_statistics(self) -> pd.DataFrame:
        """
        Computes basic statistics (mean, std, min, max) for each segment.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the statistics for each detector and segment.
        """
        stats = self.data.groupby(level=['Detector', 'SegmentID'])['Signal'].agg(['mean', 'std', 'min', 'max'])
        return stats

    def log_summary(self) -> None:
        """
        Prints a summary of the data to the console.

        Prints:
        - Number of detectors.
        - Number of segments.
        - Segment statistics (mean, std, min, max).
        """
        num_detectors = self.data.index.get_level_values('Detector').nunique()
        num_segments = len(self.data.index.get_level_values('SegmentID').unique())

        print("Triggered Acquisition Analysis Summary")
        print("--------------------------------------")
        print(f"Number of Detectors: {num_detectors}")
        print(f"Number of Segments: {num_segments}\n")

        print("Segment Statistics:")
        stats = self.compute_statistics()
        print(stats)

