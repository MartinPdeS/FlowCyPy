from typing import Optional, Union, List, Tuple, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy
from FlowCyPy import units
from FlowCyPy.sub_frames import utils
from FlowCyPy.units import Quantity
from pint_pandas import PintArray

class BaseSubFrame(pd.DataFrame):
    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of ScattererDataFrame."""
        return self.__class__

class ScattererDataFrame(BaseSubFrame):
    """
    A subclass of pandas DataFrame with custom plotting and logging for scatterer data.
    """
    def plot(self, x: str = None, y: str = None, z: str = None, **kwargs) -> Any:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
        """
        if x and not y and not z:
            return self.hist(x=x, **kwargs)
        if x and y and not z:
            return self.plot_2d(x=x, y=y, **kwargs)
        if x and y and z:
            return self.plot_3d(x=x, y=y, z=z, **kwargs)

        raise ValueError("At least one of 'x', 'y', or 'z' must be provided for plotting.")

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

    @utils.plot_sns
    def plot_2d(self, x: str, y: str, alpha: float = 0.8, bandwidth_adjust: float = 1, color_palette: Optional[Union[str, dict]] = None, figure_size: tuple = (6, 6)) -> plt.Figure:
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

        grid = sns.jointplot(
            data=df,
            x=x,
            y=y,
            hue='Population',
            palette=color_palette,
            kind='scatter',
            alpha=alpha,
            marginal_kws={'bw_adjust': bandwidth_adjust},
            height=figure_size[0] if figure_size else None,
        )

        grid.figure.suptitle("Scatterer Sampling Distribution")
        grid.ax_joint.set_xlabel(f"{x} [{x_unit._repr_latex_()}]")
        grid.ax_joint.set_ylabel(f"{y} [{y_unit._repr_latex_()}]")
        return grid

    @utils.plot_3d
    def plot_3d(self, ax: plt.Axes, x: str, y: str, z: str = None, hue: str = 'Population', alpha: float = 0.8) -> plt.Figure:
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

        for population, group in df.pint.dequantify().astype(float).groupby(hue):
            ax.scatter(group[x], group[y], group[z], label=population, alpha=alpha)

        ax.set_xlabel(f"{x} [{x_unit._repr_latex_()}]", labelpad=20)
        ax.set_ylabel(f"{y} [{y_unit._repr_latex_()}]", labelpad=20)
        ax.set_zlabel(f"{z} [{z_unit._repr_latex_()}]", labelpad=20)
        ax.set_title("Scatterer Sampling Distribution")
        return ax.figure

    @utils._pre_plot
    def hist(
        self,
        x: str = 'Diameter',
        kde: bool = False,
        figure_size: tuple = (10, 6),
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, units.Quantity]] = None) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        x : str, optional
            The column name to plot (default: 'Diameter').
        figure_size : tuple, optional
            Size of the figure in inches (default: (10, 6)).
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

        figure, ax = plt.subplots(nrows=1, ncols=1, figsize=figure_size)

        df = df.reset_index('Population').pint.dequantify().droplevel('unit', axis=1)

        df[x] = utils.clip_data(signal=df[[x]], clip_value=clip_data)

        sns.histplot(data=df, x=df[x], ax=ax, kde=kde, bins=bins, color=color, hue=df['Population'])
        ax.set_xlabel(f"{x} [{unit._repr_latex_()}]")
        ax.set_title(f"Distribution of {x}")

        return figure

    def _add_event_to_ax(self, ax: plt.Axes, time_units: Quantity, palette: str = 'tab10', filter_population: str | List[str] = None) -> None:
        """
        Adds vertical markers for event occurrences in the scatterer data.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to modify.
        time_units : Quantity
            Time units to use for plotting.
        palette : str, optional
            Color palette for different populations (default: 'tab10').
        filter_population : str or list of str, optional
            Populations to display. If None, all populations are shown.
        """
        # Get unique population names
        unique_populations = self.index.get_level_values('Population').unique()
        color_mapping = dict(zip(unique_populations, sns.color_palette(palette, len(unique_populations))))

        for population_name, group in self.groupby('Population'):
            if filter_population is not None and population_name not in filter_population:
                continue

            x = group.Time.pint.to(time_units)

            color = color_mapping[population_name]
            ax.vlines(x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), label=population_name, color=color)

        ax.tick_params(axis='y', left=False, labelleft=False)
        ax.get_yaxis().set_visible(False)
        ax.set_xlabel(f"Time [{time_units._repr_latex_()}]")
        ax.legend()

    def sort_population(self) -> None:
        time_unit = units.second

        original_times = self['Time'].pint.to(time_unit)

        new_times = numpy.sort(original_times.pint.quantity.magnitude)

        self['Time'] = PintArray(new_times, time_unit)

    def uniformize_events(self) -> None:
        time_unit = units.second

        original_times = self['Time'].pint.to(time_unit)

        start_time = original_times[0].magnitude

        stop_time = original_times[-1].magnitude

        total_number_of_events = len(self)

        new_times = numpy.linspace(start_time, stop_time, total_number_of_events)

        self['Time'] = PintArray(new_times, time_unit)

    def uniformize_events_with_time(self, run_time: units.Quantity = None, lower_boundary: float = 0.05, upper_boundary: float = 0.95) -> None:
        time_unit = units.second

        total_number_of_events = len(self)

        start_time = 0 * units.second

        stop_time = run_time

        duration = stop_time - start_time

        new_start_time = lower_boundary * duration
        new_stop_time = upper_boundary * duration

        new_times = numpy.linspace(
            new_start_time.to(time_unit).magnitude,
            new_stop_time.to(time_unit).magnitude,
            total_number_of_events
        )

        self['Time'] = PintArray(new_times, time_unit)

