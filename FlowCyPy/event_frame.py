from typing import Any, List, Optional, Union
import pandas as pd
import matplotlib.pyplot as plt
import MPSPlots
import seaborn as sns
import pint_pandas
from FlowCyPy.sub_frames import utils


class EventFrame:
    def __init__(self):
        self.events_list = []

    def __iter__(self):
        """
        Iterate over population events.
        """
        for events in self.events_list:
            yield events

    def __getitem__(self, type: int | str):
        """
        Get population events by index or name.

        Parameters
        ----------
        type : int | str
            Index of the population events or the name of the population.
        """
        if isinstance(type, int):
            return self.events_list[type]

        if isinstance(type, str):
            for events in self.events_list:
                if events.population.name == type:
                    return events

        raise KeyError(f"No population found with name '{type}'.")

    def __len__(self):
        """
        Get the number of population events.
        """
        return len(self.events_list)

    def _add_to_ax(
        self, ax, filter_population: List[str] = None, time_units: str = "second"
    ) -> None:
        """
        Internal method to add population events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        filter_population : List[str], optional
            List of population names to include. If None, includes all populations.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        import seaborn as sns

        palette = "tab10"
        color_mapping = dict(
            zip(
                [event.population.name for event in self],
                sns.color_palette(palette, len(self)),
            )
        )

        for events in self:
            if (
                filter_population is not None
                and events.population.name not in filter_population
            ):
                continue

            x = events.Time.pint.to(time_units).pint.quantity

            ax.vlines(
                x,
                ymin=0,
                ymax=1,
                transform=ax.get_xaxis_transform(),
                label=events.population.name,
                color=color_mapping[events.population.name],
            )

        ax.tick_params(axis="y", left=False, labelleft=False)
        ax.get_yaxis().set_visible(False)
        ax.set_xlabel(f"Time [{time_units:~P}]")
        ax.legend()

    def get_concatenated_dataframe(self) -> pd.DataFrame:
        """
        Concatenates all population event DataFrames into a single DataFrame with a MultiIndex.

        Returns
        -------
        pd.DataFrame
            A MultiIndex DataFrame containing all events from all populations. The first index level
            indicates the population name.
        """

        for population in self:
            for key in population:
                values = population[key].pint.quantity.to_reduced_units()
                population[key] = pint_pandas.PintArray(values.magnitude, values.units)

                # population[key] = population[key].pint.to_unprefixed()

        population_event = pd.concat(
            self, keys=[event.population.name for event in self], names=["Population"]
        )

        for key in population_event:
            unit = population_event[key].max().to_compact().units
            population_event[key] = population_event[key].pint.to(unit)

        return population_event

    def plot(self, x: str = None, y: str = None, z: str = None, **kwargs) -> plt.Figure:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
        """
        if x and not y and not z:
            return self.plot_hist(x=x, **kwargs)
        if x and y and not z:
            return self.plot_2d(x=x, y=y, **kwargs)
        if x and y and z:
            return self.plot_3d(x=x, y=y, z=z, **kwargs)

        raise ValueError(
            "At least one of 'x', 'y', or 'z' must be provided for plotting."
        )

    @MPSPlots.helper.post_mpl_plot
    def plot_hist(
        self,
        x: str = "Diameter",
        kde: bool = False,
        bins: Optional[int] = "auto",
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, Any]] = None,
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
        clip_data : Optional[Union[str, Any]], optional
            If provided, removes data above a threshold. If a string ending with '%' (e.g., "20%") is given,
            the function removes values above the corresponding quantile (e.g., the top 20% of values).
            If a Any is given, it removes values above that absolute value.

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        population_event = self.get_concatenated_dataframe()

        figure, ax = plt.subplots(1, 1)

        df = (
            population_event.reset_index("Population")
            .pint.dequantify()
            .droplevel("unit", axis=1)
        )

        df[x] = utils.clip_data(signal=df[[x]], clip_value=clip_data)

        sns.histplot(
            data=df,
            x=df[x],
            ax=ax,
            kde=kde,
            bins=bins,
            color=color,
            hue=df["Population"],
        )
        ax.set(
            xlabel=f"{x} [{population_event[x].pint.units:~P}]",
            title=f"Distribution of {x}",
        )

        return figure

    @MPSPlots.helper.post_mpl_plot
    def plot_2d(
        self, x: str, y: str, alpha: float = 0.8, bandwidth_adjust: float = 1.0
    ) -> plt.Figure:
        """
        Plots the scatterer sampling distribution using seaborn's jointplot.
        Parameters
        ----------
        x : str
            The column name for the x-axis.
        y : str
            The column name for the y-axis.
        alpha : float, optional
            The transparency level for the scatter points (default is 0.8).
        bandwidth_adjust : float, optional
            Adjustment factor for the bandwidth of the marginal distributions (default is 1.0).

        Returns
        -------
        plt.Figure
            The matplotlib Figure object containing the plot.
        """
        population_event = self.get_concatenated_dataframe()

        grid = sns.jointplot(
            data=population_event,
            x=x,
            y=y,
            hue="Population",
            kind="scatter",
            alpha=alpha,
            marginal_kws={"bw_adjust": bandwidth_adjust},
        )

        grid.figure.suptitle("Scatterer Sampling Distribution")
        grid.ax_joint.set_xlabel(f"{x} [{population_event[x].pint.units:~P}]")
        grid.ax_joint.set_ylabel(f"{y} [{population_event[y].pint.units:~P}]")
        return grid.figure

    @MPSPlots.helper.post_mpl_plot
    def plot_3d(
        self,
        x: str,
        y: str,
        z: str = None,
        hue: str = "Population",
        alpha: float = 0.8,
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
        population_event = self.get_concatenated_dataframe()

        figure = plt.figure()
        ax = figure.add_subplot(111, projection="3d")

        # df, (x_unit, y_unit, z_unit) = self.get_sub_dataframe(x, y, z)

        for population, group in (
            population_event.pint.dequantify().astype(float).groupby(hue)
        ):
            ax.scatter(group[x], group[y], group[z], label=population, alpha=alpha)

        ax.set_xlabel(f"{x} [{population_event[x].pint.units:~P}]", labelpad=20)
        ax.set_ylabel(f"{y} [{population_event[y].pint.units:~P}]", labelpad=20)
        ax.set_zlabel(f"{z} [{population_event[z].pint.units:~P}]", labelpad=20)
        ax.set_title("Scatterer Sampling Distribution")
        return figure
