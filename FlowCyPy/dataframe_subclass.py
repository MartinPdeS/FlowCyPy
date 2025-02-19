from typing import Optional, Union, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from FlowCyPy import helper
from MPSPlots.styles import mps
from FlowCyPy import units
import logging
from tabulate import tabulate


class ScattererDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """

    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return ScattererDataFrame


    @helper.plot_sns
    def plot(self, x: str = 'Size', y: str = 'RefractiveIndex', alpha: float = 0.8, bandwidth_adjust: float = 1, color_palette: Optional[Union[str, dict]] = None) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn jointplot,
        automatically extracting units from Pint arrays.
        """
        df_reset = self.reset_index()

        if len(df_reset) == 1:
            return

        # Extract units if the column contains Pint Quantities
        df_reset[x] = df_reset[x].pint.to(df_reset[x].max().to_compact().units)
        df_reset[y] = df_reset[y].pint.to(df_reset[y].max().to_compact().units)
        x_unit = getattr(df_reset[x], "pint", None)
        y_unit = getattr(df_reset[y], "pint", None)

        x_label = f"{x} [{x_unit.units}]" if x_unit else x
        y_label = f"{y} [{y_unit.units}]" if y_unit else y

        with plt.style.context(mps):
            grid = sns.jointplot(
                data=df_reset,
                x=x,
                y=y,
                hue='Population',
                palette=color_palette,
                kind='scatter',
                alpha=alpha,
                marginal_kws=dict(bw_adjust=bandwidth_adjust)
            )

        grid.figure.suptitle("Scatterer Sampling Distribution")

        # Set axis labels with extracted units
        grid.ax_joint.set_xlabel(x_label)
        grid.ax_joint.set_ylabel(y_label)

        return grid

    def log(self, table_format: str = "grid") -> None:
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
            for population in self.groupby("Population")
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
        medium_refractive_index = f"{self.attrs['run_time']:~P}"  # Replace with actual medium refractive index if stored elsewhere
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

class ClassifierDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return ClassifierDataFrame

    @helper.plot_sns
    def plot(self, feature: str, x_detector: str, y_detector: str) -> None:
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
        if 'Label' not in self.columns:
            raise ValueError(
                "The 'Label' column is missing. Ensure the dataset has been classified "
                "by calling the `classify_dataset` method before using `classifier`."
            )

        # Set the plotting style
        with plt.style.context(mps):
            grid = sns.jointplot(
                data=self,
                x=(feature, x_detector),
                y=(feature, y_detector),
                hue='Label',
            )

        grid.figure.suptitle('Event classification')

        return grid


class PeakDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return PeakDataFrame

    @helper.plot_sns
    def plot(self, x_detector: str, y_detector: str, feature: str = 'Height', bandwidth_adjust: float = 0.8) -> None:
        """
        Plot the joint KDE distribution of the specified signal between two detectors using seaborn,
        optionally overlaying scatter points.

        Parameters
        ----------
        x_detector : str
            Name of the detector to use for the x-axis.
        y_detector : str
            Name of the detector to use for the y-axis.
        feature : str, optional
            The signal column to plot, by default 'Height'.
        bandwidth_adjust : float, optional
            Bandwidth adjustment factor for KDE, by default 0.8.
        """
        # Filter to only include rows for the specified detectors
        x_data = self.loc[x_detector, feature]
        y_data = self.loc[y_detector, feature]

        # x_units = x_data.max().to_compact().units
        # y_units = y_data.max().to_compact().units
        x_units = x_data.pint.units
        y_units = y_data.pint.units

        with plt.style.context(mps):
            # Create joint KDE plot with scatter points overlay
            grid = sns.jointplot(
                x=x_data,#.pint.to(x_units),
                y=y_data,#.pint.to(y_units),
                kind='kde',
                fill=True,
                cmap="Blues",
                joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
            )

        grid.figure.suptitle("Peaks properties")
        grid.ax_joint.scatter(x_data, y_data, color='C1', alpha=0.6)

        grid.set_axis_labels(f"{feature} ({x_detector}) [{x_units}]", f"{feature} ({y_detector}) [{y_units}]", fontsize=12)

        return grid


class BaseAcquisitionDataFrame(pd.DataFrame):
    """
    A base class for acquisition data frames, providing common plotting and logging functionalities.
    """
    @property
    def _constructor(self):
        return self.__class__

    @property
    def detector_names(self) -> List[str]:
        return self.index.get_level_values('Detector').unique().to_list()

    def plot(self, show: bool = True, filter_population: Union[str, List[str]] = None, **kwargs) -> None:
        """
        Generalized plotting function for acquisition data.
        """
        n_plots = len(self.index.get_level_values('Detector').unique()) + 1  # One extra plot for events
        figure_size = kwargs.get("figure_size", (10, 6))

        time_units = self["Time"].max().to_compact().units
        signal_units = self["Signal"].max().to_compact().units

        with plt.style.context(mps):
            fig, axes = plt.subplots(
                ncols=1,
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                height_ratios=[1] * (n_plots - 1) + [0.5]
            )

        axes = {
            name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes)
        }

        self._plot_detector_data(axes=axes, time_units=time_units, signal_units=signal_units)

        # Handle `filter_population` default case
        if filter_population is None:
            filter_population = self.attrs['scatterer_dataframe'].index.get_level_values('Population').unique()

        helper.add_event_to_ax(self.attrs['scatterer_dataframe'], ax=axes['scatterer'], time_units=time_units, show_populations=filter_population)
        axes['scatterer'].set_xlabel(f"Time [{time_units}]")

        if kwargs.get("save_filename"):
            fig.savefig(fname=kwargs["save_filename"])
        if show:
            plt.show()

    def plot_combined(self, dataframes: List["BaseAcquisitionDataFrame"], show: bool = True, **kwargs):
        """
        Plots multiple acquisition dataframes together, ensuring at most two plots per axis.
        """
        n_plots = len(self.detector_names) + 1  # One extra plot for events
        figure_size = kwargs.get("figure_size", (10, 6))

        with plt.style.context(mps):
            fig, _axes = plt.subplots(
                ncols=1,
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                height_ratios=[1] * (n_plots - 1) + [0.5]
            )

        axes = {
            name: ax for name, ax in zip(self.detector_names + ['scatterer'], _axes)
        }

        axes_twin = {
            name: ax.twinx() for name, ax in zip(self.detector_names + ['scatterer'], _axes)
        }

        time_units = dataframes[0]["Time"].max().to_compact().units  # Assume same time unit for all

        dataframes[0]._plot_detector_data(axes=axes, time_units=time_units)
        dataframes[1]._plot_detector_data(axes=axes_twin, time_units=time_units)

        # Add event markers to the last subplot
        scatterer_df = dataframes[0].attrs['scatterer_dataframe']
        helper.add_event_to_ax(scatterer_df, ax=axes['scatterer'], time_units=time_units, show_populations=None)
        axes['scatterer'].set_xlabel(f"Time [{time_units}]")

        if kwargs.get("save_filename"):
            fig.savefig(fname=kwargs["save_filename"])
        if show:
            plt.show()

    def _plot_detector_data(self, ax, detector_name: str, group: pd.DataFrame, time_units: units.Quantity, signal_units: units.Quantity = None) -> None:
        """
        Handles the plotting logic for an individual detector. To be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _plot_detector_data method.")

    def log(self, table_format: str = "grid", include_totals: bool = True) -> None:
        """
        Generalized logging function for acquisition statistics.
        """
        logging.info(f"\n=== {self.__class__.__name__} Statistics ===")

        if self.empty:
            logging.warning("No data available for detectors.")
            return

        table_data = [
            self._get_detector_stats(detector_name, self.xs(detector_name, level="Detector"))
            for detector_name in self.index.get_level_values("Detector").unique()
        ]

        headers = self._get_log_headers()
        formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".3f")
        logging.info("\n" + formatted_table)

        if include_totals:
            total_points = sum(stat[1] for stat in table_data)
            logging.info(f"\nTotal number of events detected across all detectors: {total_points}")

    def _get_log_headers(self) -> List[str]:
        """
        Returns headers for the log table. Override in subclasses if needed.
        """
        return [
            "Detector",
            "Num Points",
            "First Time",
            "Last Time",
            "Mean Δ Time",
            "Max Signal",
            "Min Signal",
            "Mean Signal",
            "STD Signal",
        ]

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List:
        """
        Computes statistics for a detector. Override in subclasses if needed.
        """
        if group.empty:
            return [detector_name, 0, None, None, None, None, None, None, None]

        num_points = len(group["Time"])
        first_time = group["Time"].min()
        last_time = group["Time"].max()

        time_diffs = group["Time"].diff().dropna()
        mean_time_between_acquisitions = time_diffs.mean() if not time_diffs.empty else None

        max_signal = group["Signal"].max()
        min_signal = group["Signal"].min()
        mean_signal = group["Signal"].mean()
        std_signal = group["Signal"].std()

        return [
            detector_name,
            num_points,
            first_time,
            last_time,
            mean_time_between_acquisitions,
            max_signal,
            min_signal,
            mean_signal,
            std_signal,
        ]

class AnalogAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    A subclass of BaseAcquisitionDataFrame for continuous acquisition.
    """
    def _plot_detector_data(self, axes, time_units: units.Quantity, signal_units: units.Quantity = None) -> None:
        """
        Handles the plotting logic for an individual detector.
        """
        for detector_name, group in self.groupby('Detector'):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            if signal_units is None:
                _signal_units = group["Signal"].max().to_compact().units
            else:
                _signal_units = signal_units

            signal = group["Signal"].pint.to(_signal_units)

            ax.plot(time_data, signal, label='Analog Signal', linestyle='-')
            ax.set_ylim([*self.attrs['saturation_levels'][detector_name]])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]')

    def log(self, table_format: str = "grid", include_totals: bool = True) -> None:
        """
        Generalized logging function for acquisition statistics.
        """
        logging.info(f"\n=== {self.__class__.__name__} Statistics ===")

        if self.empty:
            logging.warning("No data available for detectors.")
            return

        table_data = [
            self._get_detector_stats(detector_name, self.xs(detector_name, level="Detector"))
            for detector_name in self.index.get_level_values("Detector").unique()
        ]

        headers = self._get_log_headers()
        formatted_table = tabulate(table_data, headers=headers, tablefmt=table_format, floatfmt=".3f")
        logging.info("\n" + formatted_table)

    def _get_log_headers(self) -> List[str]:
        """
        Returns headers for the log table. Override in subclasses if needed.
        """
        return [
            "Detector",
            "Num Points",
            "First Time",
            "Last Time",
            "Mean Δ Time",
            "Max Signal",
            "Min Signal",
            "Mean Signal",
            "STD Signal",
        ]

class DigitizedAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    A subclass of BaseAcquisitionDataFrame for continuous acquisition.
    """
    def _plot_detector_data(self, axes, time_units: units.Quantity, signal_units: units.Quantity = None) -> None:
        """
        Handles the plotting logic for an individual detector.
        """
        for detector_name, group in self.groupby('Detector'):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            if signal_units is None:
                _signal_units = group["Signal"].max().to_compact().units
            else:
                _signal_units = signal_units

            signal = group["Signal"]

            ax.step(time_data, signal, where='mid', label='Digitized Signal')
            ax.set_ylim([*self.attrs['saturation_levels'][detector_name]])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]')

class TriggeredAnalogAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    A subclass of BaseAcquisitionDataFrame for triggered acquisition.
    """
    def _plot_detector_data(self, axes, time_units: units.Quantity, signal_units: units.Quantity = None) -> None:
        """
        Handles the plotting logic for an individual detector.
        """
        for (detector_name, _), group in self.groupby(['Detector', 'SegmentID']):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            if signal_units is None:
                _signal_units = group["Signal"].max().to_compact().units
            else:
                _signal_units = signal_units

            analog_signal = group["Signal"].pint.to(_signal_units)

            ax.plot(time_data, analog_signal, linestyle='-')
            ax.set_ylim([*self.attrs['saturation_levels'][detector_name]])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]')

            if detector_name == self.attrs['threshold']['detector']:
                handles, labels = ax.get_legend_handles_labels()
                ax.axhline(y=self.attrs['threshold']['value'].to(_signal_units), label='Threshold' if 'Threshold' not in labels else None, linestyle='--', color='black', linewidth=1)
                ax.legend(loc='upper right')

    def _get_log_headers(self) -> List[str]:
        """
        Returns headers specific to triggered acquisition logging.
        """
        return [
            "Detector",
            "Number of Acquisition",
            "First Event Time",
            "Last Event Time",
            "Time Between Events",
        ]

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List:
        """
        Computes statistics for triggered acquisition.
        """
        if group.empty:
            return [detector_name, 0, None, None, None]

        num_acquisition = len(group["Time"])
        first_event_time = group["Time"].min()
        last_event_time = group["Time"].max()

        time_diffs = group["Time"].diff().dropna()
        time_between_events = time_diffs.mean() if not time_diffs.empty else None

        return [
            detector_name,
            num_acquisition,
            first_event_time,
            last_event_time,
            time_between_events,
        ]

class TriggeredDigitalAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    A subclass of BaseAcquisitionDataFrame for triggered acquisition.
    """
    def _plot_detector_data(self, axes, time_units: units.Quantity, signal_units: units.Quantity = None) -> None:
        """
        Handles the plotting logic for an individual detector.
        """
        for (detector_name, seg), group in self.groupby(['Detector', 'SegmentID']):

            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            ax.step(time_data, group["Signal"], where='mid')

            ax.set_ylim([*self.attrs['saturation_levels'][detector_name]])
            ax.set_ylabel(f'{detector_name} [{group["Signal"].pint.units}]')

    def _get_log_headers(self) -> List[str]:
        """
        Returns headers specific to triggered acquisition logging.
        """
        return [
            "Detector",
            "Number of Acquisition",
            "First Event Time",
            "Last Event Time",
            "Time Between Events",
        ]

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List:
        """
        Computes statistics for triggered acquisition.
        """
        if group.empty:
            return [detector_name, 0, None, None, None]

        num_acquisition = len(group["Time"])
        first_event_time = group["Time"].min()
        last_event_time = group["Time"].max()

        time_diffs = group["Time"].diff().dropna()
        time_between_events = time_diffs.mean() if not time_diffs.empty else None

        return [
            detector_name,
            num_acquisition,
            first_event_time,
            last_event_time,
            time_between_events,
        ]
