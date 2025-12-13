from typing import List, Optional, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MPSPlots import helper
import seaborn as sns
import pint_pandas

from FlowCyPy.sampling_method import ExplicitModel, GammaModel


class EventCollection:
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

    def _add_explicit_model_to_ax(
        self, events, ax, color, time_units: str = "second"
    ) -> None:
        """
        Internal method to add explicit model events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        if events.empty:
            return
        ax.vlines(
            events.Time.pint.to(time_units).pint.quantity,
            ymin=0,
            ymax=1,
            transform=ax.get_xaxis_transform(),
            label=events.population.name,
            color=color,
        )

    def _add_gamma_model_to_ax(
        self, events, ax, color, time_units: str = "second"
    ) -> None:
        """
        Internal method to add gamma model events to a matplotlib axis.

        Parameters
        ----------
        ax : plt.Axes
            The matplotlib axis to add the events to.
        time_units : str, optional
            Units for the time axis (default is 'second').
        """
        ax.fill_between(
            x=events.attrs["time_trace"].to(time_units),
            y1=0,
            y2=events.attrs["particles_trace"],
            label=events.population.name,
            color=color,
            alpha=0.5,
        )

    def _add_to_ax(
        self, ax, time_units: str, filter_population: Optional[List[str]] = None
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
        palette = "tab10"
        color_mapping = dict(
            zip(
                [event.population.name for event in self],
                sns.color_palette(palette, len(self)),
            )
        )

        for events in self.events_list:
            if (
                filter_population is not None
                and events.population.name not in filter_population
            ):
                continue
            if isinstance(events.sampling_method, ExplicitModel):
                self._add_explicit_model_to_ax(
                    events,
                    ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )
            if isinstance(events.sampling_method, GammaModel):
                self._add_gamma_model_to_ax(
                    events,
                    ax,
                    color=color_mapping[events.population.name],
                    time_units=time_units,
                )

        ax.set_xlabel(f"Time [{time_units}]")
        ax.legend()

    def get_concatenated_dataframe(
        self, filter_population: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Concatenates all population event DataFrames into a single DataFrame with a MultiIndex.

        Parameters
        ----------
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, includes all populations.

        Returns
        -------
        pd.DataFrame
            A MultiIndex DataFrame containing all events from all populations. The first index level
            indicates the population name.
        """

        if len(self) == 0:
            return pd.DataFrame(
                index=pd.MultiIndex(
                    levels=[[]],
                    codes=[[]],
                    names=["Population"],
                )
            )

        for population in self:
            if population.empty:
                continue

            for key in population:
                values = population[key].pint.quantity.to_reduced_units()
                population[key] = pint_pandas.PintArray(values.magnitude, values.units)

        population_event = pd.concat(
            [event for event in self if not event.empty],
            keys=[event.population.name for event in self if not event.empty],
            names=["Population"],
        )

        for key in population_event:
            unit = population_event[key].max().to_compact().units
            population_event[key] = population_event[key].pint.to(unit)

        if filter_population is not None:
            population_event = population_event.loc[filter_population]

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

    @helper.post_mpl_plot
    def plot_hist(
        self,
        x: str = "Diameter",
        kde: bool = False,
        bins: Optional[int] = 50,
        color: Optional[Union[str, dict]] = None,
        filter_population: Optional[List[str]] = None,
        binrange: Optional[tuple] = None,
        common_norm: bool = False,
        common_bins: bool = False,
        scale_by_population: bool = True,
        scale_by_bin: bool = False,
    ) -> plt.Figure:
        """
        Plot a population resolved histogram for a chosen variable.

        The histogram can be optionally scaled to reflect physical concentration.
        Two scaling modes are supported:

            1. particle per milliliter (default)
            2. particle per (milliliter * bin) if `scale_by_bin=True`

        Parameters
        ----------
        x : str
            Column name to plot.
        kde : bool
            Whether to overlay a kernel density estimate.
        bins : int or sequence
            Number of bins or explicit bin edges.
        color : str or dict
            Color specification.
        filter_population : list or None
            Which populations to include.
        binrange : tuple or None
            Range for the histogram.
        common_norm : bool
            Forwarded to seaborn.
        common_bins : bool
            Forwarded to seaborn.
        scale_by_population : bool
            Scale histogram by population level concentration.
        scale_by_bin : bool
            If True, divides weights by the bin width to display densities
            in particle/(milliliter * bin).

        Returns
        -------
        matplotlib.figure.Figure
        """

        population_event = self.get_concatenated_dataframe(filter_population)
        figure, ax = plt.subplots(1, 1)

        if len(population_event) == 0:
            ax.set(xlabel=f"{x}", title=f"Distribution of {x}")
            return figure

        # Convert to plain numeric columns
        df = (
            population_event.reset_index("Population")
            .pint.dequantify()
            .droplevel("unit", axis=1)
        )

        # ------------------------------------------------------------
        # Construct per population weights
        # ------------------------------------------------------------
        if scale_by_population:
            population_weight_map = {
                event.attrs["Name"]: event.attrs["ParticleCount"]
                .to("particle/milliliter")
                .magnitude
                for event in self
            }
            df["Weight"] = df["Population"].map(population_weight_map)
        else:
            df["Weight"] = 1.0

        # ------------------------------------------------------------
        # Compute bin width if user wants particle/(milliliter * bin)
        # ------------------------------------------------------------
        if scale_by_bin:
            # Determine edges
            if binrange is None:
                xmin = df[x].min()
                xmax = df[x].max()
            else:
                xmin, xmax = binrange

            if isinstance(bins, int):
                bin_edges = np.linspace(xmin, xmax, bins + 1)
            else:
                bin_edges = np.asarray(bins)

            bin_width = np.diff(bin_edges)[0]

            # Scaling population weights by bin width
            # This changes units from particle/mL to particle/(mL * bin)
            df["Weight"] = df["Weight"] / bin_width
        else:
            bin_width = None  # not used

        # ------------------------------------------------------------
        # Plot histogram
        # ------------------------------------------------------------
        sns.histplot(
            data=df,
            x=x,
            ax=ax,
            kde=kde,
            bins=bins,
            hue="Population",
            color=color,
            binrange=binrange,
            common_norm=common_norm,
            common_bins=common_bins,
            weights=df["Weight"],
        )

        # ------------------------------------------------------------
        # Axis labels
        # ------------------------------------------------------------
        x_units = population_event[x].pint.units
        if scale_by_population and not scale_by_bin:
            ylabel = "particle per milliliter"
        elif scale_by_population and scale_by_bin:
            ylabel = f"Particle (mL {x_units:~P})$^{{-1}}$"
        else:
            ylabel = "Counts"

        ax.set(
            xlabel=f"{x} [{x_units:~P}]",
            ylabel=ylabel,
            title=f"Distribution of {x}",
        )

        return figure

    @helper.post_mpl_plot
    def plot_2d(
        self,
        x: str,
        y: str,
        alpha: float = 0.8,
        bandwidth_adjust: float = 1.0,
        filter_population: Optional[List[str]] = None,
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
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, includes all populations.

        Returns
        -------
        plt.Figure
            The matplotlib Figure object containing the plot.
        """
        population_event = self.get_concatenated_dataframe(filter_population)

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

    @helper.post_mpl_plot
    def plot_3d(
        self,
        x: str,
        y: str,
        z: str = None,
        hue: str = "Population",
        alpha: float = 0.8,
        filter_population: Optional[List[str]] = None,
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
        filter_population : Optional[List[str]], optional
            List of population names to include. If None, includes all populations.

        Returns
        -------
        plt.Figure
            The figure containing the 3D scatter plot.
        """
        population_event = self.get_concatenated_dataframe(filter_population)

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
