from typing import Optional, Union, List, Tuple, Any
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from tabulate import tabulate
import pint_pandas

from FlowCyPy import helper, units
from MPSPlots.styles import mps as plot_style


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

        return self.hist(**kwargs)

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

        df, (y_unit, x_unit) = self.get_sub_dataframe(y, x)

        with plt.style.context(plot_style):
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

    def hist(
        self,
        x: str = 'Diameter',
        kde: bool = False,
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, units.Quantity]] = None,
        show: bool = True
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        x : str, optional
            The column name to plot (default: 'Diameter').
        kde : bool, optional
            Whether to overlay a KDE curve (default: False).
        bins : Optional[int], optional
            Number of bins for the histogram (default: 'auto', letting Seaborn decide).
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).
        clip_data : Optional[Union[str, units.Quantity]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            the function removes values above the corresponding quantile (e.g., the top 20% of values).
            If a pint.Quantity is given, it removes values above that absolute value.

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        if len(self) == 1:
            return

        df, [unit] = self.get_sub_dataframe(x)

        with plt.style.context(plot_style):
            figure, ax = plt.subplots(figsize=(7, 5))

        df = df.reset_index('Population').pint.dequantify().droplevel('unit', axis=1)

        # Remove data above the clipping threshold if clip_data is provided.
        if clip_data is not None:
            if isinstance(clip_data, str) and clip_data.endswith('%'):
                # For a percentage clip, compute the quantile. E.g., "20%" removes the top 20% values.
                percent = float(clip_data.rstrip('%'))
                clip_value = df[x].quantile(1 - percent / 100)
            else:
                # Assume clip_data is a pint.Quantity; convert to the same unit.
                clip_value = clip_data.to(unit).magnitude
            df = df[df[x] <= clip_value]

        sns.histplot(data=df, x=df[x], kde=kde, bins=bins, color=color, hue=df['Population'])
        ax.set_xlabel(f"{x} [{unit}]")
        ax.set_title(f"Distribution of {x}")
        plt.tight_layout()

        if show:
            plt.show()

        return figure


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

        with plt.style.context(plot_style):
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

    def hist(
        self,
        feature: str,
        figure_size: tuple = (10, 6),
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None,
        save_filename: str = None,
        show: bool = True,
        clip_data: Optional[Union[str, units.Quantity]] = None
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        feature : str, optional
            The column name to plot (default: 'Diameter').
        figure_size : tuple, optional
            Size of the figure in inches (default: (10, 6)).
        bins : Optional[int], optional
            Number of bins for the histogram (default: 'auto', letting Seaborn decide).
        color : Optional[Union[str, dict]], optional
            Color specification for the plot (default: None).
        save_filename : str, optional
            If provided, the figure is saved to this filename.
        show : bool, optional
            If True, displays the plot immediately (default: True).
        clip_data : Optional[Union[str, units.Quantity]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            values above the corresponding quantile (e.g. the top 20% of values) are excluded.
            If a pint.Quantity is given, values above that absolute value are removed.

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        if len(self) == 1:
            return

        detector_names = self.index.get_level_values('Detector').unique()

        with plt.style.context(plot_style):
            figure, axes = plt.subplots(
                ncols=1, nrows=len(detector_names), figsize=figure_size, sharex=True
            )

        for ax, detector_name in zip(axes, detector_names):
            data = self.loc[detector_name, [feature]].sort_index()

            # Remove extreme values if clip_data is provided.
            if clip_data is not None:
                if isinstance(clip_data, str) and clip_data.endswith('%'):
                    # For a percentage, compute the quantile.
                    percent = float(clip_data.rstrip('%'))
                    clip_value = data[feature].quantile(1 - percent / 100)
                else:
                    # Assume clip_data is a pint.Quantity. Conversion can be done here if needed.
                    clip_value = clip_data.magnitude
                data = data[data[feature] <= clip_value]

            counts, bin_edges = numpy.histogram(data[feature], bins=bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            ax.bar(bin_centers, counts, width=bin_edges[1] - bin_edges[0],
                color=color, edgecolor='black')
            ax.set_ylabel(f"{detector_name}  [count]")

        if save_filename:
            figure.savefig(fname=save_filename)
        if show:
            plt.show()

        return figure

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
        df = self.loc[[x, y], [feature]].sort_index()

        with plt.style.context(plot_style):
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
        grid.set_axis_labels(f"{x}: {feature}", f"{y}: {feature}", fontsize=12)
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
    def __init__(self, dataframe: pd.DataFrame, scatterer = None, **attributes: dict):
        super().__init__(dataframe)

        self.attrs['scatterer'] = scatterer
        self.attrs.update(attributes)

    def __finalize__(self, other, method=..., **kwargs):
        """
        Finalize the DataFrame after operations, preserving scatterer attributes.
        This method ensures that the scatterer attribute is retained in the output DataFrame.
        """
        output = super().__finalize__(other, method, **kwargs)

        output.attrs['scatterer'] = self.attrs['scatterer']

        return output


    def normalize(self, signal_units: units.Quantity = None, time_units: units.Quantity = None, inplace: bool = False) -> None:
        """
        Normalize the DataFrame's signal and time columns to specified units.

        Parameters
        ----------
        signal_units : units.Quantity, optional
            The units to which the signal columns should be normalized (default: None).
        time_units : units.Quantity, optional
            The units to which the time column should be normalized (default: None).
        """
        if not inplace:
            output = self.copy()
        else:
            output = self

        for col in output.columns:
            if col == 'Time' and time_units is not None:
                output[col] = output[col].pint.to(time_units)

            elif col != 'Time' and signal_units is not None:
                output[col] = output[col].pint.to(signal_units)

        return output


    @property
    def _constructor(self) -> type:
        return self.__class__

    @property
    def scatterer(self) -> object:
        return self.attrs['scatterer']

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return [col for col in self.columns if col != 'Time']

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

        signal_units = self.loc[:, self.detector_names].to_numpy().max().to_compact().units

        with plt.style.context(plot_style):
            fig, axes_array = plt.subplots(
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                gridspec_kw={'height_ratios': [1] * (n_plots - 1) + [0.5]}
            )

            for ax in axes_array:
                ax.yaxis.tick_right()

            axes = {name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
            self._add_to_axes(axes=axes, time_units=time_units, signal_units=signal_units)

            helper.add_event_to_ax(
                self.scatterer,
                ax=axes['scatterer'],
                time_units=time_units,
                filter_population=filter_population
            )
            axes['scatterer'].set_xlabel(f"Time [{time_units}]")

            if kwargs.get("save_filename"):
                fig.savefig(fname=kwargs["save_filename"])
            if show:
                plt.show()

    def hist(
        self,
        show: bool = True,
        figure_size: tuple = (10, 6),
        save_filename: str = None,
        bins: str = 'auto',
        clip_data: Optional[Union[str, units.Quantity]] = None
    ) -> None:
        """
        Plot histograms of acquisition data for each detector, with optional removal of extreme values.

        This method generates a histogram for each detector using seaborn's histplot. It optionally removes
        the signal data above a threshold specified by `clip_data` (expressed as a pint.Quantity or a string
        like "20%", which removes the top 20% of values).

        Parameters
        ----------
        show : bool, optional
            If True, displays the plot immediately (default: True).
        figure_size : tuple, optional
            Size of the figure in inches (default: (10, 6)).
        save_filename : str, optional
            If provided, the figure is saved to this filename.
        kde : bool, optional
            If True, overlays a KDE on the histogram (default: False).
        bins : str or int, optional
            Binning strategy passed to seaborn.histplot (default: 'auto').
        clip_data : Optional[Union[str, units.Quantity]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            values above the corresponding quantile (e.g., top 20% are removed) are excluded.
            If a pint.Quantity is given, values above that absolute value are removed.

        Returns
        -------
        None
        """
        n_plots = len(self.detector_names)
        signal_units = self["Signal"].max().to_compact().units

        with plt.style.context(plot_style):
            fig, axes_array = plt.subplots(
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
            )

            axes = {name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}

            _signal_units = signal_units or self["Signal"].max().to_compact().units

            for detector_name, group in self.groupby('Detector'):
                ax = axes[detector_name]
                ax.set_ylabel(detector_name)

                # Convert signal to consistent units and get the magnitude.
                if _signal_units.dimensionality == units.bit_bins.dimensionality:
                    signal = group["Signal"].pint.magnitude
                else:
                    signal = group["Signal"].pint.to(_signal_units).pint.magnitude

                # Remove data above the clip threshold if clip_data is provided.
                if clip_data is not None:
                    if isinstance(clip_data, str) and clip_data.endswith('%'):
                        # For a percentage clip, compute the threshold quantile.
                        percent = float(clip_data.rstrip('%'))
                        clip_value = numpy.percentile(signal, 100 - percent)
                    else:
                        clip_value = clip_data.to(_signal_units).magnitude
                    # Remove values above clip_value instead of clipping them.
                    signal = signal[signal <= clip_value]

                counts, bin_edges = numpy.histogram(signal, bins=bins)

                # Compute bin centers for plotting.
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                # Plot the histogram using a bar chart.
                ax.bar(bin_centers, counts, width=bin_edges[1] - bin_edges[0], edgecolor='black')

            axes[detector_name].set_xlabel(f'Signal [{_signal_units}]')
            if save_filename:
                fig.savefig(fname=save_filename)

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

        with plt.style.context(plot_style):
            fig, axes_array = plt.subplots(
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                gridspec_kw={'height_ratios': [1] * (n_plots - 1) + [0.5]}
            )

        axes = {name: ax for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
        axes_twin = {name: ax.twinx() for name, ax in zip(self.detector_names + ['scatterer'], axes_array)}
        time_units = dataframes[0]["Time"].max().to_compact().units  # Assumes same time unit across frames

        dataframes[0]._add_to_axes(axes=axes, time_units=time_units)
        dataframes[1]._add_to_axes(axes=axes_twin, time_units=time_units)

        scatterer_df = dataframes[0].attrs['scatterer_dataframe']
        helper.add_event_to_ax(scatterer_df, ax=axes['scatterer'], time_units=time_units, show_populations=None)
        axes['scatterer'].set_xlabel(f"Time [{time_units}]")

        if kwargs.get("save_filename"):
            fig.savefig(fname=kwargs["save_filename"])
        if show:
            plt.show()


class AcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for continuous (analog) acquisition data.
    """
    def digitalize(self, digitizer: object) -> "AcquisitionDataFrame":
        digital_df = pd.DataFrame(
            index=self.index,
            columns=self.columns,
            data=dict(Time=self.Time)
        )

        for detector_name in self.detector_names:
            analog_signal = self[detector_name]
            digitized_signal, _ = digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return AcquisitionDataFrame(
            dataframe=digital_df,
            plot_type='digital',
            scatterer=self.attrs['scatterer']
        )

    def _add_to_axes(self, axes: dict, time_units: Optional[units.Quantity] = None, signal_units: Optional[units.Quantity] = None) -> None:
        """
        Plot analog signal data for each detector.
        """
        signal_units = signal_units or self[self.detector_names].max().to_compact().units
        time_units = time_units or self['Time'].max().to_compact().units

        for detector_name in self.detector_names:
            ax = axes[detector_name]

            ax.set_ylabel(f'{detector_name} [{signal_units}]', labelpad=20)

            time = self["Time"].pint.to(time_units)
            signal = self[detector_name].pint.to(signal_units)

            if self.attrs['plot_type'] == 'analog':
                ax.plot(time, signal, label='Analog Signal', linestyle='-', color='black')
            else:
                ax.step(time, signal, where='mid', color='black', label='Digitized Signal')


class TriggerDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for triggered analog acquisition data.
    """

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return [col for col in self.columns if col not in ['Time', 'SegmentID']]

    @property
    def n_segment(self) -> int:
        return len(self.index.get_level_values('SegmentID').unique())


    def digitalize(self, digitizer: object) -> "TriggerDataFrame":
        digital_df = pd.DataFrame(
            index=self.index,
            columns=self.columns,
            data=dict(Time=self.Time)
        )

        for detector_name in self.detector_names:
            analog_signal = self[detector_name]
            digitized_signal, _ = digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return TriggerDataFrame(
            dataframe=digital_df,
            plot_type='digital',
            scatterer=self.attrs['scatterer']
        )


    def _add_to_axes(self, axes: dict, time_units: Optional[units.Quantity] = None, signal_units: Optional[units.Quantity] = None) -> None:
        """
        Plot triggered analog signal data for each detector and highlight each SegmentID region
        with a distinct color.
        """
        time_units = time_units or self['Time'].max().to_compact().units
        signal_units = signal_units or self[self.detector_names].max().to_compact().units

        for detector_name in self.detector_names:
            ax = axes[detector_name]
            ax.set_ylabel(rf'{detector_name} [{signal_units}]', labelpad=20)

            for segment_id, group in self.groupby('SegmentID'):
                time = group["Time"].pint.to(time_units)
                signal = group[detector_name].pint.to(signal_units)
                start_time = time.min()
                end_time = time.max()

                color = plt.cm.tab10(int(segment_id) % 10)

                ax.axvspan(start_time, end_time, facecolor=color, alpha=0.3)

                if self.attrs['plot_type'] == 'analog':
                    ax.plot(time, signal, color='black', linestyle='-')
                else:
                    ax.step(time, signal, where='mid', color='black', linestyle='-')

                # Add threshold line and legend for the detector, if applicable.
                threshold = self.attrs.get('threshold', None)
                if threshold is not None and detector_name == threshold['detector']:
                    _, labels = ax.get_legend_handles_labels()
                    if 'Threshold' not in labels:
                        threshold = threshold['value'].to(signal_units)
                        ax.axhline(y=threshold, label='Threshold', linestyle='--', color='black', linewidth=1)

                    ax.legend(loc='upper right')
