from typing import Callable, List
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from functools import wraps
import inspect
from FlowCyPy.units import Quantity
from FlowCyPy import units
import pint_pandas
from MPSPlots.styles import mps as plot_style
from functools import wraps
import numpy as np

def get_dataframe_from_dict(dictionnary: dict, level_names: list = None) -> pd.DataFrame:
    dfs = []
    for pop_name, inner_dict in dictionnary.items():

        df_pop = pd.DataFrame(
            index=range(inner_dict.pop('n_elements'))
        )

        df_pop.index = pd.MultiIndex.from_product(
            [[pop_name], df_pop.index],
            names=level_names
        )

        for k, v in inner_dict.items():
            df_pop[k] = pint_pandas.PintArray(v.magnitude, v.units)

        dfs.append(df_pop)

    if len(dfs) == 0:
        return pd.DataFrame(columns=level_names).set_index(level_names)

    return pd.concat(dfs)

def validate_units(**expected_units):
    """
    Decorator to enforce that function arguments of type Quantity have the correct units.

    Parameters
    ----------
    expected_units : dict
        A dictionary where keys are argument names and values are the expected Pint units.

    Raises
    ------
    ValueError
        If any argument does not have the expected unit.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature and argument values
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for arg_name, expected_unit in expected_units.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]

                    if value is None:
                        continue

                    # Check if the value is a Pint Quantity
                    if not isinstance(value, Quantity):
                        raise TypeError(f"Argument '{arg_name}' must be a Pint Quantity, but got {type(value)}")

                    # Check if the argument has the expected units
                    if not value.check(value.units):
                        raise ValueError(f"Argument '{arg_name}' must have units of {expected_unit}, but got {value.units}")

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper
    return decorator


def plot_sns(function: Callable) -> Callable:
    """
    A decorator that helps in plotting by wrapping a plotting function with additional functionality
    such as handling axes creation, setting the figure style, managing legends, and saving figures.

    Parameters
    ----------
    function : Callable
        The plotting function that is decorated. It should accept `self`, `ax`, and `mode_of_interest`
        as parameters.

    Returns
    -------
    Callable
        A wrapper function that adds the specified plotting functionalities.

    Notes
    -----
    This decorator expects the decorated function to have the following signature:
    `function(self, ax=None, mode_of_interest='all', **kwargs)`.
    """
    def wrapper(self, show: bool = True, equal_limits: bool = False, save_as: str = None, log_scale: bool = False, **kwargs) -> plt.Figure:
        """
        A wrapped version of the plotting function that provides additional functionality for creating
        and managing plots.

        Parameters
        ----------
        self : object
            The instance of the class calling this method.
        ax : plt.Axes, optional
            A matplotlib Axes object to draw the plot on. If None, a new figure and axes are created.
            Default is None.
        show : bool, optional
            Whether to display the plot. If False, the plot will not be shown but can still be saved
            or returned. Default is True.
        log_scale : bool, optional
            If `True`, applies a logarithmic scale to both axes of the joint plot and their marginal distributions. Default is `False`.
        save_filename : str, optional
            A file path to save the figure. If None, the figure will not be saved. Default is None.
        equal_limits : bool, optional
            Ensures equal axis limits if True (default: False).
        **kwargs : dict
            Additional keyword arguments passed to the decorated function.

        Returns
        -------
        plt.Figure
            The matplotlib Figure object created or used for the plot.

        Notes
        -----
        - If no `ax` is provided, a new figure and axes are created using the style context `mps`.
        - The legend is only added if there are labels to display.
        - If `save_filename` is specified, the figure is saved to the given path.
        - The plot is shown if `show` is set to True.
        """
        with plt.style.context(plot_style):
            grid = function(self, **kwargs)

            grid.figure.tight_layout()

            if equal_limits:
                limits = [
                    min(grid.ax_joint.get_xlim()[0], grid.ax_joint.get_ylim()[0]),
                    max(grid.ax_joint.get_xlim()[1], grid.ax_joint.get_ylim()[1])
                ]
                grid.ax_joint.set_xlim(limits)
                grid.ax_joint.set_ylim(limits)

            if log_scale:
                grid.ax_joint.set_xscale('log')
                grid.ax_joint.set_yscale('log')
                grid.ax_marg_x.set_xscale('log')
                grid.ax_marg_y.set_yscale('log')

            if save_as is not None:
                grid.figure.savefig(save_as)

            if show:
                plt.show()

        return grid

    return wrapper

def plot_3d(function: Callable) -> Callable:
    """
    A decorator that wraps a 3D plotting function with additional functionality such as:
      - Creating a new 3D axes if none is provided.
      - Applying a custom style context.
      - Optionally setting equal limits for all axes.
      - Saving the figure to a file.
      - Displaying the figure.

    Parameters
    ----------
    function : Callable
        The 3D plotting function to decorate. The function should accept an 'ax' keyword argument.

    Returns
    -------
    Callable
        A wrapped function that returns a matplotlib Figure containing the 3D plot.
    """
    def wrapper(self, ax: plt.Axes = None, show: bool = True, equal_axes: bool = False, save_as: str = None, figsize = (8, 8), **kwargs) -> plt.Figure:

        with plt.style.context(plot_style):
            # If an Axes3D object is not provided, create one using our style context.
            if ax is None:
                # with plt.style.context(mps):
                figure = plt.figure(figsize=figsize)
                ax = figure.add_subplot(111, projection='3d')

            else:
                figure = ax.figure

            # Call the decorated plotting function.
            function(self, ax=ax, **kwargs)

            # Optionally enforce equal scaling for all three axes.
            if equal_axes:
                x_limits = ax.get_xlim3d()
                y_limits = ax.get_ylim3d()
                z_limits = ax.get_zlim3d()

                x_range = abs(x_limits[1] - x_limits[0])
                y_range = abs(y_limits[1] - y_limits[0])
                z_range = abs(z_limits[1] - z_limits[0])
                max_range = max(x_range, y_range, z_range)

                # Compute centers of each axis.
                x_middle = (x_limits[0] + x_limits[1]) / 2
                y_middle = (y_limits[0] + y_limits[1]) / 2
                z_middle = (z_limits[0] + z_limits[1]) / 2

                ax.set_xlim3d([x_middle - max_range/2, x_middle + max_range/2])
                ax.set_ylim3d([y_middle - max_range/2, y_middle + max_range/2])
                ax.set_zlim3d([z_middle - max_range/2, z_middle + max_range/2])

            ax.legend()

            plt.tight_layout()

            # Save the figure if a filename is provided.
            if save_as is not None:
                fig.savefig(save_as)

            # Display the figure if requested.
            if show:
                plt.show()

            return figure


    return wrapper


def add_event_to_ax(
    scatterer_dataframe: pd.DataFrame,
    ax: plt.Axes,
    time_units: units.Quantity,
    palette: str = 'tab10',
    filter_population: str | List[str] = None
) -> None:
    """
    Adds vertical markers for event occurrences in the scatterer data.

    Parameters
    ----------
    ax : plt.Axes
        The matplotlib axis to modify.
    time_units : units.Quantity
        Time units to use for plotting.
    palette : str, optional
        Color palette for different populations (default: 'tab10').
    filter_population : str or list of str, optional
        Populations to display. If None, all populations are shown.
    """
    # Get unique population names
    unique_populations = scatterer_dataframe.index.get_level_values('Population').unique()
    color_mapping = dict(zip(unique_populations, sns.color_palette(palette, len(unique_populations))))

    for population_name, group in scatterer_dataframe.groupby('Population'):
        if filter_population is not None and population_name not in filter_population:
            continue
        x = group.Time.pint.to(time_units)
        color = color_mapping[population_name]
        ax.vlines(x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), label=population_name, color=color)

    ax.tick_params(axis='y', left=False, labelleft=False)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel(f"Time [{time_units}]")
    ax.legend()



def _pre_plot(function):
    @wraps(function)
    def wrapper(self, show: bool = True, save_as: str = None, **kwargs):
        """
        Decorator to set the plot style and handle figure saving and showing.
        This decorator applies a specific plot style, saves the figure if a filename is provided,
        and shows the plot if requested.

        Parameters
        ----------
        function : callable
            The plotting function to be wrapped.
        show : bool, optional
            Whether to display the plot (default: True).
        save_as : str, optional
            If provided, the figure is saved to this filename.
        **kwargs : dict
            Additional keyword arguments to pass to the plotting function.

        Returns
        -------
        plt.Figure
            The figure containing the plot.
        """

        with plt.style.context(plot_style):
            figure = function(self, **kwargs)

            plt.tight_layout()

            if save_as is not None:
                plt.savefig(save_as)

            if show:
                plt.show()

        return figure

    return wrapper


def clip_data(signal: pint_pandas.PintArray, clip_value: str | Quantity = None) -> pint_pandas.PintArray:
    """
    Clips the data in a PintArray based on a specified threshold.
    If `clip_value` is a string ending with '%', it is treated as a percentage of the maximum value.
    If `clip_value` is a Quantity, it is used as the threshold value.
    If `clip_value` is None, no clipping is performed.
    Parameters
    ----------
    signal : pint_pandas.PintArray
        The data to be clipped.
    clip_value : str or Quantity, optional
        The clipping threshold. If a string, it should end with '%'. If a Quantity, it should have compatible units.
        If None, no clipping is performed.
    Returns
    -------
    pint_pandas.PintArray
        The clipped data.
    """
    if clip_value is None:
        # If no clip value is provided, return the original signal.
        return signal

    # Remove data above the clip threshold if clip_value is provided.
    if clip_value is not None:
        if isinstance(clip_value, str) and clip_value.endswith('%'):
            # For a percentage clip, compute the threshold quantile.
            percent = float(clip_value.rstrip('%'))
            clip_value = np.percentile(signal, 100 - percent)
        else:
            clip_value = clip_value.to(signal.pint.signal_units).magnitude
        # Remove values above clip_value instead of clipping them.
        signal = signal[signal <= clip_value]

    return signal