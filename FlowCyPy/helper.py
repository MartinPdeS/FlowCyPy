from typing import Callable
import matplotlib.pyplot as plt
from MPSPlots.styles import mps


def plot_helper(function: Callable) -> Callable:
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
    def wrapper(self, ax: plt.Axes = None, show: bool = True, save_filename: str = None, figure_size: tuple = None, **kwargs) -> plt.Figure:
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
        mode_of_interest : str, optional
            Specifies the mode of interest for the plot. If 'all', all available modes will be plotted.
            This parameter is interpreted using the `interpret_mode_of_interest` function. Default is 'all'.
        save_filename : str, optional
            A file path to save the figure. If None, the figure will not be saved. Default is None.
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
        if ax is None:
            with plt.style.context(mps):
                figure, ax = plt.subplots(1, 1, figsize=figure_size)

        else:
            figure = ax.get_figure()

        output = function(self, ax=ax, **kwargs)

        _, labels = ax.get_legend_handles_labels()

        # Only add a legend if there are labels
        if labels:
            ax.legend()

        if save_filename:
            figure.savefig(save_filename)

        if show:
            plt.show()

        return output

    return wrapper
