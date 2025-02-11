from typing import Callable
import matplotlib.pyplot as plt
from MPSPlots.styles import mps


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
    def wrapper(self, show: bool = True, equal_limits: bool = False, save_filename: str = None, log_scale: bool = False, **kwargs) -> plt.Figure:
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

        if save_filename:
            grid.figure.savefig(save_filename)

        if show:
            plt.show()

        return grid

    return wrapper
