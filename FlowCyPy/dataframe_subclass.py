from typing import Optional, Union, List, Tuple, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from tabulate import tabulate

from FlowCyPy import helper, units
from MPSPlots.styles import mps


class ScattererDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with custom plotting and logging for scatterer data.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of ScattererDataFrame."""
        return ScattererDataFrame

    def plot(self, **kwargs) -> Any:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
        """
        if 'z' in kwargs:
            return self.plot_3d(**kwargs)

        if 'y' in kwargs:
            return self.plot_2d(**kwargs)

        return self.plot_1d(**kwargs)

    def get_sub_dataframe(self, *columns: str) -> Tuple[pd.DataFrame, List[Any]]:
        """
        Return a sub-dataframe of the requested columns and convert any Pint quantities.

        Parameters
        ----------
        *columns : str
            The names of the columns to extract.

        Returns
        -------
        tuple
            A tuple containing the sub-dataframe and a list of extracted units.
        """
        df = self[list(columns)].copy()
        units_list = []

        for col_name, col_data in df.items():
            # Convert to compact unit
            unit = col_data.max().to_compact().units
            df[col_name] = col_data.pint.to(unit)
            units_list.append(unit)

        return df, units_list

    @helper.plot_sns
    def plot_2d(
        self,
        x: str = 'Diameter',
        y: str = 'RefractiveIndex',
        alpha: float = 0.8,
        bandwidth_adjust: float = 1,
        color_palette: Optional[Union[str, dict]] = None
    ) -> plt.Figure:
        """
        Plot the joint distribution of scatterer sizes and refractive indices.

        Parameters
        ----------
        x : str, optional
            Column representing scatterer sizes (default: 'Diameter').
        y : str, optional
            Column representing refractive indices (default: 'RefractiveIndex').
        alpha : float, optional
            Alpha blending value for scatter points (default: 0.8).
        bandwidth_adjust : float, optional
            Bandwidth adjustment for kernel density estimate (default: 1).
        color_palette : Optional[Union[str, dict]], optional
            Seaborn color palette or mapping for hue (default: None).

        Returns
        -------
        plt.Figure
            The jointplot figure.
        """
        if len(self) == 1:
            return

        df, (x_unit, y_unit) = self.get_sub_dataframe(y, x)

        with plt.style.context(mps):
            grid = sns.jointplot(
                data=df,
                x=x,
                y=y,
                hue='Population',
                palette=color_palette,
                kind='scatter',
                alpha=alpha,
                marginal_kws={'bw_adjust': bandwidth_adjust}
            )

        grid.figure.suptitle("Scatterer Sampling Distribution")
        grid.ax_joint.set_xlabel(f"{x} [{x_unit}]")
        grid.ax_joint.set_ylabel(f"{y} [{y_unit}]")
        return grid

    @helper.plot_3d
    def plot_3d(
        self,
        ax: plt.Axes,
        x: str = 'Diameter',
        y: str = 'RefractiveIndex',
        z: str = 'Density',
        hue: str = 'Population',
        alpha: float = 0.8
    ) -> plt.Figure:
        """
        Visualize a 3D scatter plot of scatterer properties.

        Parameters
        ----------
        ax : plt.Axes
            A matplotlib 3D axis to plot on.
        x : str, optional
            Column for the x-axis (default: 'Diameter').
        y : str, optional
            Column for the y-axis (default: 'RefractiveIndex').
        z : str, optional
            Column for the z-axis (default: 'Density').
        hue : str, optional
            Column used for grouping/coloring (default: 'Population').
        alpha : float, optional
            Transparency for scatter points (default: 0.8).

        Returns
        -------
        plt.Figure
            The figure containing the 3D scatter plot.
        """
        if len(self) <= 1:
            return

        df, (x_unit, y_unit, z_unit) = self.get_sub_dataframe(x, y, z)

        for population, group in df.groupby(hue):
            x_data = group[x].values.quantity.magnitude
            y_data = group[y].values.quantity.magnitude
            z_data = group[z].values.quantity.magnitude
            ax.scatter(x_data, y_data, z_data, label=population, alpha=alpha)

        ax.set_xlabel(f"{x} [{x_unit}]", labelpad=20)
        ax.set_ylabel(f"{y} [{y_unit}]", labelpad=20)
        ax.set_zlabel(f"{z} [{z_unit}]", labelpad=20)
        ax.set_title("Scatterer Sampling Distribution")
        return ax.figure

    def log(self, table_format: str = "grid") -> None:
        """
        Log detailed information about scatterer populations.

        Parameters
        ----------
        table_format : str, optional
            Format for the displayed table (default: 'grid').
        """
        logging.info("\n=== Scatterer Population Properties ===")

        general_table_data = [
            self._get_population_properties(population)
            for population in self.groupby("Population")
        ]
        headers = [
            "Name",
            "Refractive Index",
            "Medium Refractive Index",
            "Diameter",
            "Particle Count",
            "Number of Events",
            "Min Time Between Events",
            "Avg Time Between Events",
        ]
        formatted_table = tabulate(general_table_data, headers=headers, tablefmt=table_format, floatfmt=".4f")
        logging.info("\n" + formatted_table)

    def _get_population_properties(self, population_group: Tuple[Any, pd.DataFrame]) -> List[Union[str, float]]:
        """
        Extract key properties for a scatterer population.

        Parameters
        ----------
        population_group : tuple
            Tuple with the population name and its corresponding DataFrame.

        Returns
        -------
        list
            List of population properties.
        """
        population_name, population_df = population_group

        name = population_name
        refractive_index = f"{population_df['RefractiveIndex'].mean():~P}"
        medium_refractive_index = f"{self.attrs['run_time']:~P}"  # Update as needed
        size = f"{population_df['Diameter'].mean():~P}"
        particle_count = len(population_df)
        num_events = particle_count

        min_delta_time = population_df["Time"].diff().abs().min()
        avg_delta_time = population_df["Time"].diff().mean()

        return [
            name,
            refractive_index,
            medium_refractive_index,
            size,
            particle_count,
            num_events,
            min_delta_time,
            avg_delta_time,
        ]

    @helper.plot_sns
    def plot_1d(
        self,
        x: str = 'Diameter',
        kde: bool = False,
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn.

        Parameters
        ----------
        column : str, optional
            The column name to plot (default: 'Diameter').
        kde : bool, optional
            Whether to overlay a KDE curve (default: False).
        bins : Optional[int], optional
            Number of bins for the histogram (default: None, which lets Seaborn decide).
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        if len(self) == 1:
            return

        df, [unit] = self.get_sub_dataframe(x)

        with plt.style.context(mps):
            fig, ax = plt.subplots(figsize=(7, 5))
            sns.histplot(data=df, x=x, kde=kde, bins=bins, color=color, hue='Population')
            ax.set_xlabel(f"{x} [{unit}]")
            ax.set_title(f"Distribution of {x}")
            plt.tight_layout()

        return fig


class ClassifierDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame for classifying peaks.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of ClassifierDataFrame."""
        return ClassifierDataFrame

    @helper.plot_sns
    def plot(self, feature: str, x: str, y: str) -> plt.Figure:
        """
        Visualize the classification of peaks using a scatter plot.

        Parameters
        ----------
        feature : str
            Feature to classify (e.g., 'Height', 'Width', 'Area').
        x_detector : str
            Detector used for the x-axis.
        y_detector : str
            Detector used for the y-axis.

        Raises
        ------
        ValueError
            If the 'Label' column is missing.

        Returns
        -------
        plt.Figure
            The figure with the classification plot.
        """
        if 'Label' not in self.columns:
            raise ValueError(
                "Missing 'Label' column. Run `classify_dataset` before plotting."
            )

        with plt.style.context(mps):
            temp = self.pint.dequantify().sort_index(axis=1)
            grid = sns.jointplot(
                x=temp[(feature, x)].values.squeeze(),
                y=temp[(feature, y)].values.squeeze(),
                hue=temp['Label'].values.squeeze()
            )
        grid.figure.suptitle('Event classification')
        return grid


class PeakDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame for handling peak data with custom plotting.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of PeakDataFrame."""
        return PeakDataFrame

    def plot(self, **kwargs) -> Any:
        """
        Dispatch plot method to 2D or 3D based on kwargs.
        """
        if 'z' in kwargs:
            return self.plot_3d(**kwargs)
        return self.plot_2d(**kwargs)

    def get_sub_dataframe(self, columns: List[str], rows: List[str]) -> Tuple[pd.DataFrame, List[Any]]:
        """
        Extract sub-dataframe for given rows and columns with Pint unit conversion.

        Parameters
        ----------
        columns : list
            List of column names.
        rows : list
            List of row identifiers.

        Returns
        -------
        tuple
            A tuple with the sub-dataframe and a list of units.
        """
        df = self.loc[rows, columns].copy()
        unit_list = []

        for col_name, col_data in df.items():
            if not hasattr(col_data, 'pint'):
                df[col_name] = col_data
                unit_list.append('None')
            else:
                unit = col_data.max().to_compact().units
                if unit.dimensionality == units.bit_bins.dimensionality:
                    unit = units.bit_bins
                # df.loc[:, col_name] = col_data.pint.to(unit)
                df[col_name] = col_data.pint.to(unit)
                unit_list.append(unit)

        return df, unit_list

    @helper.plot_sns
    def plot_2d(self, x: str, y: str, feature: str = 'Height', bandwidth_adjust: float = 0.8) -> plt.Figure:
        """
        Plot the joint KDE distribution of a feature between two detectors.

        Parameters
        ----------
        x : str
            Detector for the x-axis.
        y : str
            Detector for the y-axis.
        feature : str, optional
            Feature column (default: 'Height').
        bandwidth_adjust : float, optional
            KDE bandwidth adjustment (default: 0.8).

        Returns
        -------
        plt.Figure
            The joint KDE plot figure.
        """
        df, feature_units = self.get_sub_dataframe(columns=[feature], rows=[x, y])
        feature_unit = feature_units[0]

        with plt.style.context(mps):
            grid = sns.jointplot(
                x=df.loc[x, feature],
                y=df.loc[y, feature],
                kind='kde',
                fill=True,
                cmap="Blues",
                joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
            )

        grid.figure.suptitle("Peaks properties")
        grid.ax_joint.scatter(
            df.loc[x, feature],
            df.loc[y, feature],
            color='C1',
            alpha=0.6
        )
        grid.set_axis_labels(f"{x}: {feature} [{feature_unit}]", f"{y}: {feature} [{feature_unit}]", fontsize=12)
        return grid

    @helper.plot_3d
    def plot_3d(self, x: str, y: str, z: str, feature: str = 'Height', ax: Optional[plt.Axes] = None) -> plt.Figure:
        """
        Create a 3D scatter plot of a feature across three detectors.

        Parameters
        ----------
        x : str
            Detector for the x-axis.
        y : str
            Detector for the y-axis.
        z : str
            Detector for the z-axis.
        feature : str, optional
            Feature column (default: 'Height').
        ax : matplotlib.axes._subplots.Axes3DSubplot, optional
            A 3D axis to plot on. If None, a new figure and 3D axis are created.

        Returns
        -------
        plt.Figure
            The 3D scatter plot figure.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        else:
            fig = ax.figure

        x_series = self.loc[x, feature]
        y_series = self.loc[y, feature]
        z_series = self.loc[z, feature]

        x_data = x_series.values.quantity.magnitude
        y_data = y_series.values.quantity.magnitude
        z_data = z_series.values.quantity.magnitude

        ax.scatter(x_data, y_data, z_data, color='C1', alpha=0.6, marker='o')
        ax.set_xlabel(f"{feature} ({x})", labelpad=20)
        ax.set_ylabel(f"{feature} ({y})", labelpad=20)
        ax.set_zlabel(f"{feature} ({z})", labelpad=20)
        ax.set_title("Peaks Properties")
        ax.grid(True)
        return fig


class BaseAcquisitionDataFrame(pd.DataFrame):
    """
    Base class for acquisition data frames with common plotting and logging functionalities.
    """

    @property
    def _constructor(self) -> type:
        return self.__class__

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return self.index.get_level_values('Detector').unique().to_list()

    def plot(self, show: bool = True, filter_population: Union[str, List[str]] = None, **kwargs) -> None:
        """
        Generalized plotting for acquisition data.

        Parameters
        ----------
        show : bool, optional
            Whether to display the plot (default: True).
        filter_population : Union[str, List[str]], optional
            Population filter for events.
        """
        n_plots = len(self.detector_names) + 1  # One extra plot for events
        figure_size = kwargs.get("figure_size", (10, 6))
        time_units = self["Time"].max().to_compact().units
        signal_units = self["Signal"].max().to_compact().units

        with plt.style.context(mps):
            fig, axes_array = plt.subplots(
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                gridspec_kw={'height_ratios': [1] * (n_plots - 1) + [0.5]}
            )

        for ax in axes_array:
            ax.yaxis.tick_right()
            # ax.yaxis.set_label_position("right", rotation=180)

        axes = {name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
        self._plot_detector_data(axes=axes, time_units=time_units, signal_units=signal_units)

        if filter_population is None:
            filter_population = self.attrs['scatterer_dataframe'].index.get_level_values('Population').unique()

        helper.add_event_to_ax(
            self.attrs['scatterer_dataframe'],
            ax=axes['scatterer'],
            time_units=time_units,
            show_populations=filter_population
        )
        axes['scatterer'].set_xlabel(f"Time [{time_units}]")

        if kwargs.get("save_filename"):
            fig.savefig(fname=kwargs["save_filename"])
        if show:
            plt.show()

    def plot_combined(self, dataframes: List["BaseAcquisitionDataFrame"], show: bool = True, **kwargs) -> None:
        """
        Plot multiple acquisition data frames together.

        Parameters
        ----------
        dataframes : list
            List of acquisition data frames.
        show : bool, optional
            Whether to display the plot (default: True).
        """
        n_plots = len(self.detector_names) + 1  # One extra plot for events
        figure_size = kwargs.get("figure_size", (10, 6))

        with plt.style.context(mps):
            fig, axes_array = plt.subplots(
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                gridspec_kw={'height_ratios': [1] * (n_plots - 1) + [0.5]}
            )

        axes = {name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
        axes_twin = {name: ax.twinx() for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
        time_units = dataframes[0]["Time"].max().to_compact().units  # Assumes same time unit across frames

        dataframes[0]._plot_detector_data(axes=axes, time_units=time_units)
        dataframes[1]._plot_detector_data(axes=axes_twin, time_units=time_units)

        scatterer_df = dataframes[0].attrs['scatterer_dataframe']
        helper.add_event_to_ax(scatterer_df, ax=axes['scatterer'], time_units=time_units, show_populations=None)
        axes['scatterer'].set_xlabel(f"Time [{time_units}]")

        if kwargs.get("save_filename"):
            fig.savefig(fname=kwargs["save_filename"])
        if show:
            plt.show()

    def _plot_detector_data(
        self,
        axes: dict,
        detector_name: Optional[str] = None,
        group: Optional[pd.DataFrame] = None,
        time_units: units.Quantity = None,
        signal_units: Optional[units.Quantity] = None
    ) -> None:
        """
        Plot logic for individual detectors; to be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses must implement _plot_detector_data method.")

    def log(self, table_format: str = "grid", include_totals: bool = True) -> None:
        """
        Log acquisition statistics.

        Parameters
        ----------
        table_format : str, optional
            Table display format (default: 'grid').
        include_totals : bool, optional
            Whether to include totals in the log (default: True).
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
            logging.info(f"\nTotal number of events across all detectors: {total_points}")

    def _get_log_headers(self) -> List[str]:
        """Return headers for the log table; can be overridden in subclasses."""
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

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List[Any]:
        """
        Compute statistics for a detector.

        Parameters
        ----------
        detector_name : str
            The detector name.
        group : pd.DataFrame
            The group of data for the detector.

        Returns
        -------
        list
            List of statistics for the detector.
        """
        if group.empty:
            return [detector_name, 0, None, None, None, None, None, None, None]

        num_points = len(group["Time"])
        first_time = group["Time"].min()
        last_time = group["Time"].max()
        time_diffs = group["Time"].diff().dropna()
        mean_delta = time_diffs.mean() if not time_diffs.empty else None
        max_signal = group["Signal"].max()
        min_signal = group["Signal"].min()
        mean_signal = group["Signal"].mean()
        std_signal = group["Signal"].std()

        return [
            detector_name,
            num_points,
            first_time,
            last_time,
            mean_delta,
            max_signal,
            min_signal,
            mean_signal,
            std_signal,
        ]


class AnalogAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for continuous (analog) acquisition data.
    """

    def __init__(self, dataframe: pd.DataFrame, **attributes: dict):
        super().__init__(dataframe)

        self.attrs.update(attributes)


    def _plot_detector_data(
        self,
        axes: dict,
        time_units: units.Quantity,
        signal_units: Optional[units.Quantity] = None
    ) -> None:
        """
        Plot analog signal data for each detector.
        """
        for detector_name, group in self.groupby('Detector'):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            _signal_units = signal_units or group["Signal"].max().to_compact().units
            signal = group["Signal"].pint.to(_signal_units)
            ax.plot(time_data, signal, label='Analog Signal', linestyle='-', color='black')
            ax.set_ylim(self.attrs['saturation_levels'][detector_name])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]', labelpad=20)

    def log(self, table_format: str = "grid", include_totals: bool = True) -> None:
        """
        Log statistics for analog acquisition.
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


class DigitizedAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for digitized acquisition data.
    """

    def _plot_detector_data(
        self,
        axes: dict,
        time_units: units.Quantity,
        signal_units: Optional[units.Quantity] = None
    ) -> None:
        """
        Plot digitized signal data for each detector.
        """
        for detector_name, group in self.groupby('Detector'):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            _signal_units = signal_units or group["Signal"].max().to_compact().units
            ax.step(time_data, group["Signal"], where='mid', label='Digitized Signal')
            ax.set_ylim(self.attrs['saturation_levels'][detector_name])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]', labelpad=20)


class TriggeredAnalogAcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for triggered analog acquisition data.
    """

    def _plot_detector_data(
        self,
        axes: dict,
        time_units: units.Quantity,
        signal_units: Optional[units.Quantity] = None
    ) -> None:
        """
        Plot triggered analog signal data for each detector.
        """
        for (detector_name, _), group in self.groupby(['Detector', 'SegmentID']):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            _signal_units = signal_units or group["Signal"].max().to_compact().units
            analog_signal = group["Signal"].pint.to(_signal_units)
            ax.plot(time_data, analog_signal, linestyle='-')
            ax.set_ylim(self.attrs['saturation_levels'][detector_name])
            ax.set_ylabel(f'{detector_name} [{_signal_units}]', labelpad=20)

            if detector_name == self.attrs['threshold']['detector']:
                _, labels = ax.get_legend_handles_labels()
                if 'Threshold' not in labels:
                    ax.axhline(
                        y=self.attrs['threshold']['value'].to(_signal_units),
                        label='Threshold',
                        linestyle='--',
                        color='black',
                        linewidth=1
                    )
                ax.legend(loc='upper right')

    def _get_log_headers(self) -> List[str]:
        """Return headers for triggered analog acquisition logs."""
        return [
            "Detector",
            "Number of Acquisition",
            "First Event Time",
            "Last Event Time",
            "Time Between Events",
        ]

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List[Any]:
        """
        Compute statistics for triggered analog acquisition.
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
    DataFrame subclass for triggered digital acquisition data.
    """

    def _plot_detector_data(
        self,
        axes: dict,
        time_units: units.Quantity,
        signal_units: Optional[units.Quantity] = None
    ) -> None:
        """
        Plot triggered digital signal data for each detector.
        """
        for (detector_name, _), group in self.groupby(['Detector', 'SegmentID']):
            ax = axes[detector_name]
            ax.set_ylabel(detector_name)
            time_data = group["Time"].pint.to(time_units)
            ax.step(time_data, group["Signal"], where='mid')
            ax.set_ylim(self.attrs['saturation_levels'][detector_name])
            ax.set_ylabel(f'{detector_name} [{group["Signal"].pint.units}]', labelpad=20)

    def _get_log_headers(self) -> List[str]:
        """Return headers for triggered digital acquisition logs."""
        return [
            "Detector",
            "Number of Acquisition",
            "First Event Time",
            "Last Event Time",
            "Time Between Events",
        ]

    def _get_detector_stats(self, detector_name: str, group: pd.DataFrame) -> List[Any]:
        """
        Compute statistics for triggered digital acquisition.
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
