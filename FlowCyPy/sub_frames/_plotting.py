"""Common display and export options for dataframe plots."""

from contextlib import nullcontext
from functools import wraps
import matplotlib.pyplot as plt


def figure_options(function):
    """Apply caller-supplied figure options and display or save the result."""
    @wraps(function)
    def plot(*args, style=None, show=True, save_as=None, tight_layout=True,
             figure_size=None, xscale=None, yscale=None, xlim=None, ylim=None, **kwargs):
        with plt.style.context(style) if style is not None else nullcontext():
            figure = function(*args, **kwargs)
            for axis in figure.axes:
                if xscale is not None:
                    axis.set_xscale(xscale)
                if yscale is not None:
                    axis.set_yscale(yscale)
                if xlim is not None:
                    axis.set_xlim(xlim)
                if ylim is not None:
                    axis.set_ylim(ylim)
            if figure_size is not None:
                figure.set_size_inches(figure_size)
            if tight_layout:
                figure.tight_layout()
            if save_as is not None:
                figure.savefig(save_as, dpi=300)
            if show:
                plt.show()
            return figure

    return plot
