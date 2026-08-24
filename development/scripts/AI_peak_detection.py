from typing import Optional, List, Tuple, Dict, Union
from dataclasses import dataclass

import numpy as np
import pandas as pd


from TypedUnit import ureg, AnyUnit

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LogNorm, Normalize
from matplotlib.transforms import blended_transform_factory
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib as mpl
from MPSPlots.styles import scientific

from FlowCyPy import fluidics, Fluidics
from FlowCyPy import opto_electronics
from FlowCyPy import digital_processing
from FlowCyPy import FlowCytometer


C0, C1 = '#1f77b4', '#ff7f0e'  # color ordering
mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=[C0, C1])


class ScatterHueGridPlotter:

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------
    # helpers
    # ------------------------------------------------

    def _as_array(self, values):
        if hasattr(values, "pint"):
            return np.asarray(values.pint.magnitude, float)
        return np.asarray(values, float)

    def _robust_limits(self, values, q):

        finite = values[np.isfinite(values)]

        if finite.size == 0:
            return (0, 1)

        lo, hi = np.quantile(finite, q)

        span = hi - lo
        pad = 0.03 * span if span > 0 else 1

        return lo - pad, hi + pad

    def _log_tick(self, val, pos):

        if val < -20 or val > 20:
            return ""

        return rf"$10^{{{int(val)}}}$"

    def _format_axis_label(self, name, units):

        if units is None or units == "":
            return f"{name}"

        return f"{name} [{units}]"

    # ------------------------------------------------
    # log axis configuration
    # ------------------------------------------------

    def _configure_log_display(self, ax, tick_label_font_size=12):

        ax.xaxis.set_major_formatter(FuncFormatter(self._log_tick))
        ax.yaxis.set_major_formatter(FuncFormatter(self._log_tick))

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        x_span = int(np.ceil(xmax) - np.floor(xmin))
        y_span = int(np.ceil(ymax) - np.floor(ymin))

        if x_span <= 6:
            x_step = 1
        elif x_span <= 12:
            x_step = 2
        else:
            x_step = 4

        if y_span <= 6:
            y_step = 1
        elif y_span <= 12:
            y_step = 2
        else:
            y_step = 4

        major_x = np.arange(np.floor(xmin), np.ceil(xmax) + 1, x_step)
        major_y = np.arange(np.floor(ymin), np.ceil(ymax) + 1, y_step)

        ax.set_xticks(major_x)
        ax.set_yticks(major_y)

        offsets = np.log10(np.arange(2, 10))

        minor_x = []
        for m in np.arange(np.floor(xmin), np.ceil(xmax)):
            minor_x.extend(m + offsets)

        minor_y = []
        for m in np.arange(np.floor(ymin), np.ceil(ymax)):
            minor_y.extend(m + offsets)

        ax.set_xticks(minor_x, minor=True)
        ax.set_yticks(minor_y, minor=True)

        ax.grid(True, which="major", alpha=0.35)
        ax.grid(True, which="minor", alpha=0.15)

        ax.tick_params(axis="x", which="major", labelsize=tick_label_font_size, rotation=0)
        ax.tick_params(axis="y", which="major", labelsize=tick_label_font_size)

    def plot(
        self,
        dataframes,
        x,
        y,
        hue,
        titles=None,
        title_fontsize: int = 25,
        ncols=4,
        x_units="",
        y_units="",
        marginal_kind="kde",
        marginal_scale="density",
        kde_fill=False,
        hist_fill=False,
        hist_element="step",
        hist_multiple="layer",
        hist_common_norm=False,
        robust_quantiles=(0.01, 0.99),
        marker_size=20,
        alpha=0.35,
        hspace=0.1,
        wspace=0.1,
        label_font_size=14,
        tick_label_font_size=12,
        unit_figure_size: tuple = (6, 5),
        remove_y_labels=False,
        legend_marker_size=200,
        show_legend=True,
        log_x=False,
        log_y=False,
        show_top_ticks=False,
        show_right_ticks=False,
        n_points: int = None
    ):

        if marginal_scale not in {"density", "relative"}:
            raise ValueError("marginal_scale must be either 'density' or 'relative'.")

        nrows = np.ceil(len(dataframes) / ncols)

        fig = plt.figure(
            figsize=(unit_figure_size[0] * ncols, unit_figure_size[1] * nrows)
        )

        outer = fig.add_gridspec(
            int(nrows),
            int(ncols),
            hspace=hspace,
            wspace=wspace,
        )

        extracted = []

        for df in dataframes:

            xs = self._as_array(df[x])[:n_points]
            ys = self._as_array(df[y])[:n_points]
            hs = np.asarray(df[hue], dtype=str)

            mask = np.isfinite(xs) & np.isfinite(ys)

            xs = xs[mask]
            ys = ys[mask]
            hs = hs[mask]

            if log_x:
                mask = xs > 0
                xs = xs[mask]
                ys = ys[mask]
                hs = hs[mask]

            if log_y:
                mask = ys > 0
                xs = xs[mask]
                ys = ys[mask]
                hs = hs[mask]

            if log_x:
                xs = np.log10(xs)

            if log_y:
                ys = np.log10(ys)

            extracted.append((xs, ys, hs))

        all_x = np.concatenate([xs for xs, _, _ in extracted])
        all_y = np.concatenate([ys for _, ys, _ in extracted])

        global_xlim = self._robust_limits(all_x, robust_quantiles)
        global_ylim = self._robust_limits(all_y, robust_quantiles)

        last_non_empty_index = None
        first_joint_axis = None
        legend_handles = None
        legend_labels = None

        for i, (xs, ys, hs) in enumerate(extracted):
            if hs.size > 0:
                last_non_empty_index = i

        for i, (xs, ys, hs) in enumerate(extracted):

            r = i // ncols
            c = i % ncols

            inner = outer[r, c].subgridspec(
                2,
                2,
                height_ratios=(1.2, 6),
                width_ratios=(6, 1.2),
                hspace=0.05,
                wspace=0.05,
            )

            ax_mx = fig.add_subplot(inner[0, 0])
            ax_joint = fig.add_subplot(inner[1, 0], sharex=ax_mx)
            ax_my = fig.add_subplot(inner[1, 1], sharey=ax_joint)

            if first_joint_axis is None:
                first_joint_axis = ax_joint

            ax_joint.set_xlim(*global_xlim)
            ax_joint.set_ylim(*global_ylim)

            show_axis_legend = show_legend and (i == last_non_empty_index)

            sns.scatterplot(
                x=xs,
                y=ys,
                hue=hs,
                s=marker_size,
                alpha=alpha,
                ax=ax_joint,
                legend=show_axis_legend,
            )

            legend = ax_joint.get_legend()

            if show_axis_legend and legend is not None:
                legend_handles = legend.legend_handles
                legend_labels = [text.get_text() for text in legend.get_texts()]
                legend.remove()

            if not show_axis_legend and legend is not None:
                legend.remove()

            ax_joint.grid(True, alpha=0.25)

            if log_x or log_y:
                self._configure_log_display(
                    ax_joint,
                    tick_label_font_size=tick_label_font_size,
                )

            if marginal_kind == "kde":

                marginal_common_norm = marginal_scale == "relative"

                sns.kdeplot(
                    x=xs,
                    hue=hs,
                    fill=kde_fill,
                    common_norm=marginal_common_norm,
                    ax=ax_mx,
                    legend=False,
                )

                sns.kdeplot(
                    y=ys,
                    hue=hs,
                    fill=kde_fill,
                    common_norm=marginal_common_norm,
                    ax=ax_my,
                    legend=False,
                )

            elif marginal_kind == "hist":

                if marginal_scale == "density":
                    hist_stat = "density"
                    marginal_common_norm = hist_common_norm
                else:
                    hist_stat = "probability"
                    marginal_common_norm = True

                sns.histplot(
                    x=xs,
                    hue=hs,
                    fill=hist_fill,
                    element=hist_element,
                    multiple=hist_multiple,
                    common_norm=marginal_common_norm,
                    stat=hist_stat,
                    ax=ax_mx,
                    legend=False,
                )

                sns.histplot(
                    y=ys,
                    hue=hs,
                    fill=hist_fill,
                    element=hist_element,
                    multiple=hist_multiple,
                    common_norm=marginal_common_norm,
                    stat=hist_stat,
                    ax=ax_my,
                    legend=False,
                )

            elif marginal_kind != "none":
                raise ValueError("marginal_kind must be 'kde', 'hist', or 'none'.")

            ax_mx.set_ylabel("")
            ax_my.set_xlabel("")

            ax_mx.grid(True, alpha=0.15)
            ax_my.grid(True, alpha=0.15)

            ax_mx.tick_params(
                axis="both",
                which="both",
                bottom=False,
                top=False,
                left=False,
                right=False,
                labelbottom=False,
                labelleft=False,
            )
            ax_my.tick_params(
                axis="both",
                which="both",
                bottom=False,
                top=False,
                left=False,
                right=False,
                labelbottom=False,
                labelleft=False,
            )

            ax_joint.set_xlabel(
                self._format_axis_label(x, x_units),
                fontsize=label_font_size,
            )
            ax_joint.set_ylabel(
                self._format_axis_label(y, y_units),
                fontsize=label_font_size,
            )

            show_left_side = not (remove_y_labels and c != 0)

            ax_joint.tick_params(
                axis="both",
                which="major",
                bottom=True,
                top=show_top_ticks,
                left=show_left_side,
                right=show_right_ticks,
                labelbottom=True,
                labelleft=show_left_side,
                labeltop=False,
                labelright=False,
                labelsize=tick_label_font_size,
                length=4,
            )

            ax_joint.tick_params(
                axis="both",
                which="minor",
                bottom=True,
                top=show_top_ticks,
                left=show_left_side,
                right=show_right_ticks,
                length=2,
            )

            if not show_top_ticks:
                ax_joint.xaxis.set_ticks_position("bottom")
            else:
                ax_joint.xaxis.set_ticks_position("both")

            if show_left_side and show_right_ticks:
                ax_joint.yaxis.set_ticks_position("both")
            elif show_left_side:
                ax_joint.yaxis.set_ticks_position("left")
            elif show_right_ticks:
                ax_joint.yaxis.set_ticks_position("right")
            else:
                ax_joint.yaxis.set_ticks_position("none")

            if remove_y_labels and c != 0:
                ax_joint.set_ylabel("")

            title = titles[i] if titles else ""
            ax_joint.set_title(title, pad=70, fontsize=title_fontsize)

        if show_legend and first_joint_axis is not None and legend_handles is not None and legend_labels is not None:
            legend = first_joint_axis.legend(
                legend_handles,
                legend_labels,
                loc="best",
            )

            for handle in legend.legend_handles:
                if hasattr(handle, "set_markersize"):
                    handle.set_markersize(legend_marker_size)
                if hasattr(handle, "set_sizes"):
                    handle.set_sizes([legend_marker_size])
                if hasattr(handle, "set_alpha"):
                    handle.set_alpha(1.0)

        return fig



class Peaks2DGridPlotter:

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------
    # helpers
    # ------------------------------------------------

    def _sample(self, x, y, max_points):

        if max_points is None or x.size <= max_points:
            return x, y

        idx = self.rng.choice(x.size, max_points, replace=False)

        return x[idx], y[idx]

    def _log_tick(self, val, pos):

        if val < -30 or val > 30:
            return ""

        if not np.isfinite(val):
            return ""

        return rf"$10^{{{int(val)}}}$"

    def _format_axis_label(self, name, units):

        if units is None or units == "":
            return f"{name}"

        return f"{name} [{units}]"

    # ------------------------------------------------
    # joint renderers
    # ------------------------------------------------

    def _draw_hexbin(
        self,
        ax,
        logx,
        logy,
        gridsize,
        cmap,
        density_scale,
        cmap_scale,
    ):

        hb = ax.hexbin(
            logx,
            logy,
            gridsize=gridsize,
            cmap=cmap,
            mincnt=1,
        )

        counts = np.asarray(hb.get_array())

        if counts.size > 0:

            vmin = np.percentile(counts, cmap_scale[0])
            vmax = np.percentile(counts, cmap_scale[1])

            if vmax <= vmin:
                vmin = counts.min()
                vmax = counts.max()

            if density_scale == "log":

                vmin = max(vmin, 1)
                norm = LogNorm(vmin=vmin, vmax=vmax)

            else:

                norm = Normalize(vmin=vmin, vmax=vmax)

            hb.set_norm(norm)

        return hb

    def _draw_scatter(
        self,
        ax,
        logx,
        logy,
        marker_size,
        alpha,
        color,
        rasterized,
    ):

        return ax.scatter(
            logx,
            logy,
            s=marker_size,
            alpha=alpha,
            c=color,
            rasterized=rasterized,
        )

    def _draw_joint(
        self,
        ax,
        logx,
        logy,
        joint_kind,
        gridsize,
        cmap,
        density_scale,
        cmap_scale,
        marker_size,
        alpha,
        color,
        rasterized,
    ):

        if joint_kind == "hexbin":
            return self._draw_hexbin(
                ax=ax,
                logx=logx,
                logy=logy,
                gridsize=gridsize,
                cmap=cmap,
                density_scale=density_scale,
                cmap_scale=cmap_scale,
            )

        if joint_kind == "scatter":
            return self._draw_scatter(
                ax=ax,
                logx=logx,
                logy=logy,
                marker_size=marker_size,
                alpha=alpha,
                color=color,
                rasterized=rasterized,
            )

        raise ValueError("joint_kind must be either 'hexbin' or 'scatter'.")

    # ------------------------------------------------
    # marginals
    # ------------------------------------------------

    def _draw_marginals(self, ax_x, ax_y, logx, logy, kind, fill):

        if kind == "none":

            ax_x.set_visible(False)
            ax_y.set_visible(False)
            return

        if kind == "kde":

            if logx.size > 20:
                sns.kdeplot(
                    x=logx,
                    ax=ax_x,
                    fill=fill,
                    color="black",
                    linewidth=1.2,
                    legend=False,
                )

            if logy.size > 20:
                sns.kdeplot(
                    y=logy,
                    ax=ax_y,
                    fill=fill,
                    color="black",
                    linewidth=1.2,
                    legend=False,
                )

        elif kind == "hist":

            sns.histplot(
                x=logx,
                ax=ax_x,
                bins=60,
                element="step",
                color="black",
                legend=False,
            )
            sns.histplot(
                y=logy,
                ax=ax_y,
                bins=60,
                element="step",
                color="black",
                legend=False,
            )

        else:
            raise ValueError("marginal_kind must be 'none', 'kde', or 'hist'.")

        ax_x.set_ylabel("")
        ax_x.set_xlabel("")
        ax_y.set_ylabel("")
        ax_y.set_xlabel("")

        ax_x.grid(True, alpha=0.15)
        ax_y.grid(True, alpha=0.15)

        ax_x.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )
        ax_y.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

    # ------------------------------------------------
    # configure log display + secondary grid
    # ------------------------------------------------

    def _configure_log_display(self, ax, tick_label_font_size=12):

        ax.xaxis.set_major_formatter(FuncFormatter(self._log_tick))
        ax.yaxis.set_major_formatter(FuncFormatter(self._log_tick))

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        x_span = max(1, int(np.ceil(xmax) - np.floor(xmin)))
        y_span = max(1, int(np.ceil(ymax) - np.floor(ymin)))

        if x_span <= 6:
            x_major_step = 1
        elif x_span <= 12:
            x_major_step = 2
        else:
            x_major_step = 4

        if y_span <= 6:
            y_major_step = 1
        elif y_span <= 12:
            y_major_step = 2
        else:
            y_major_step = 4

        x_major_start = int(np.floor(xmin))
        x_major_stop = int(np.ceil(xmax)) + 1
        y_major_start = int(np.floor(ymin))
        y_major_stop = int(np.ceil(ymax)) + 1

        major_x = np.arange(x_major_start, x_major_stop, x_major_step)
        major_y = np.arange(y_major_start, y_major_stop, y_major_step)

        ax.set_xticks(major_x)
        ax.set_yticks(major_y)

        offsets = np.log10(np.arange(2, 10))

        minor_x = []
        for decade in range(x_major_start, x_major_stop):
            for offset in offsets:
                tick = decade + offset
                if xmin <= tick <= xmax:
                    minor_x.append(tick)

        minor_y = []
        for decade in range(y_major_start, y_major_stop):
            for offset in offsets:
                tick = decade + offset
                if ymin <= tick <= ymax:
                    minor_y.append(tick)

        ax.set_xticks(minor_x, minor=True)
        ax.set_yticks(minor_y, minor=True)

        ax.grid(True, which="major", alpha=0.35)
        ax.grid(True, which="minor", alpha=0.15)

        ax.tick_params(axis="x", which="major", labelsize=tick_label_font_size)
        ax.tick_params(axis="y", which="major", labelsize=tick_label_font_size)

    # ------------------------------------------------
    # inset
    # ------------------------------------------------

    def _add_inset(
        self,
        ax,
        logx,
        logy,
        joint_kind,
        gridsize,
        cmap,
        density_scale,
        cmap_scale,
        marker_size,
        alpha,
        color,
        rasterized,
        inset_xlim,
        inset_ylim,
        loc,
    ):

        inset = inset_axes(
            ax,
            width="35%",
            height="35%",
            loc=loc,
            borderpad=1,
        )

        self._draw_joint(
            ax=inset,
            logx=logx,
            logy=logy,
            joint_kind=joint_kind,
            gridsize=gridsize,
            cmap=cmap,
            density_scale=density_scale,
            cmap_scale=cmap_scale,
            marker_size=marker_size,
            alpha=alpha,
            color=color,
            rasterized=rasterized,
        )

        inset.set_xlim(
            np.log10(inset_xlim[0]) if inset_xlim[0] is not None else None,
            np.log10(inset_xlim[1]) if inset_xlim[1] is not None else None,
        )

        inset.set_ylim(
            np.log10(inset_ylim[0]) if inset_ylim[0] is not None else None,
            np.log10(inset_ylim[1]) if inset_ylim[1] is not None else None,
        )

        inset.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

        rect = plt.Rectangle(
            (np.log10(inset_xlim[0]), np.log10(inset_ylim[0])),
            np.log10(inset_xlim[1]) - np.log10(inset_xlim[0]),
            np.log10(inset_ylim[1]) - np.log10(inset_ylim[0]),
            fill=False,
            linewidth=1.2,
            color="black",
        )

        ax.add_patch(rect)

    # ------------------------------------------------
    # main plotting
    # ------------------------------------------------

    def add_trigger(
        self,
        fig,
        threshold,
        label="Trigger",
        padding=0.02,
        fontsize=12,
        **line_kwargs,
    ):
        """Draw a trigger threshold and label on every joint plot.

        Parameters
        ----------
        fig : matplotlib.figure.Figure
            Figure returned by :meth:`plot`.
        threshold : float
            Trigger threshold in the y-axis data coordinates.
        label : str, default="Trigger"
            Text displayed next to the threshold line.
        padding : float, default=0.02
            Horizontal padding from the right edge of each joint axis,
            expressed as a fraction of the axis width.
        fontsize : float, default=12
            Font size of the trigger label.
        **line_kwargs
            Additional keyword arguments passed to ``Axes.axhline``.
        """
        if fontsize is not None and fontsize <= 0:
            raise ValueError("fontsize must be positive or None.")
        if not 0 <= padding < 1:
            raise ValueError("padding must be in the interval [0, 1).")

        line_kwargs.setdefault("color", "red")
        line_kwargs.setdefault("linestyle", "--")
        line_kwargs.setdefault("linewidth", 1.5)

        for ax in fig.axes:
            if not getattr(ax, "_flowcypy_joint_axis", False):
                continue

            ax.axhline(threshold, **line_kwargs)

            label_transform = blended_transform_factory(
                ax.transAxes,
                ax.transData,
            )
            ax.text(
                1.0 - padding,
                threshold,
                label,
                transform=label_transform,
                ha="right",
                va="bottom",
                fontsize=fontsize,
                color=line_kwargs["color"],
            )

        return fig

    def plot(
        self,
        records,
        x_detector,
        y_detector,
        titles=None,
        ncols=4,
        joint_kind="hexbin",
        gridsize=200,
        cmap="turbo",
        density_scale="log",
        cmap_scale=(5, 99),
        marker_size=10,
        alpha=0.35,
        color="black",
        rasterized=True,
        xlim=None,
        ylim=None,
        x_units="",
        y_units="",
        marginal_kind="kde",
        marginal_fill=True,
        add_inset=False,
        inset_xlim=None,
        inset_ylim=None,
        inset_loc="upper right",
        inset_axes_indices=None,
        remove_y_labels=False,
        label_font_size=14,
        tick_label_font_size=12,
        title_fontsize=25,
        max_points=None,
        hspace=0.1,
        wspace=0.1,
        show_top_ticks=False,
        show_right_ticks=False,
        n_points: int = None,
    ):

        nrows = math.ceil(len(records) / ncols)

        fig = plt.figure(figsize=(6 * ncols, 5 * nrows))

        outer = fig.add_gridspec(
            nrows,
            ncols,
            hspace=hspace,
            wspace=wspace,
        )

        extracted = []

        for record in records:

            peaks = record.peaks

            x = np.asarray(peaks.loc[x_detector, "Height"], float)
            y = np.asarray(peaks.loc[y_detector, "Height"], float)

            if n_points is not None:
                x = x[:n_points]
                y = y[:n_points]

            mask = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)

            x = x[mask]
            y = y[mask]

            x, y = self._sample(x, y, max_points)

            logx = np.log10(x)
            logy = np.log10(y)

            extracted.append((logx, logy))

        all_logx = np.concatenate([logx for logx, _ in extracted]) if extracted else np.array([0.0, 1.0])
        all_logy = np.concatenate([logy for _, logy in extracted]) if extracted else np.array([0.0, 1.0])

        if xlim is None:
            global_xlim = (
                np.nanmin(all_logx),
                np.nanmax(all_logx),
            )
        else:
            global_xlim = (
                np.log10(xlim[0]) if xlim[0] is not None else np.nanmin(all_logx),
                np.log10(xlim[1]) if xlim[1] is not None else np.nanmax(all_logx),
            )

        if ylim is None:
            global_ylim = (
                np.nanmin(all_logy),
                np.nanmax(all_logy),
            )
        else:
            global_ylim = (
                np.log10(ylim[0]) if ylim[0] is not None else np.nanmin(all_logy),
                np.log10(ylim[1]) if ylim[1] is not None else np.nanmax(all_logy),
            )

        for i, (logx, logy) in enumerate(extracted):

            r = i // ncols
            c = i % ncols

            inner = outer[r, c].subgridspec(
                2,
                2,
                height_ratios=(1.2, 6),
                width_ratios=(6, 1.2),
                hspace=0.05,
                wspace=0.05,
            )

            ax_mx = fig.add_subplot(inner[0, 0])
            ax_joint = fig.add_subplot(inner[1, 0], sharex=ax_mx)
            ax_my = fig.add_subplot(inner[1, 1], sharey=ax_joint)
            ax_joint._flowcypy_joint_axis = True

            self._draw_joint(
                ax=ax_joint,
                logx=logx,
                logy=logy,
                joint_kind=joint_kind,
                gridsize=gridsize,
                cmap=cmap,
                density_scale=density_scale,
                cmap_scale=cmap_scale,
                marker_size=marker_size,
                alpha=alpha,
                color=color,
                rasterized=rasterized,
            )

            ax_joint.set_xlim(*global_xlim)
            ax_joint.set_ylim(*global_ylim)

            self._configure_log_display(
                ax_joint,
                tick_label_font_size=tick_label_font_size,
            )

            self._draw_marginals(
                ax_mx,
                ax_my,
                logx,
                logy,
                marginal_kind,
                marginal_fill,
            )

            should_draw_inset = False

            if add_inset:
                if inset_axes_indices is None:
                    should_draw_inset = True
                else:
                    should_draw_inset = i in inset_axes_indices

            if should_draw_inset:

                self._add_inset(
                    ax=ax_joint,
                    logx=logx,
                    logy=logy,
                    joint_kind=joint_kind,
                    gridsize=gridsize,
                    cmap=cmap,
                    density_scale=density_scale,
                    cmap_scale=cmap_scale,
                    marker_size=marker_size,
                    alpha=alpha,
                    color=color,
                    rasterized=rasterized,
                    inset_xlim=inset_xlim,
                    inset_ylim=inset_ylim,
                    loc=inset_loc,
                )

            ax_joint.set_xlabel(
                self._format_axis_label(x_detector, x_units),
                fontsize=label_font_size,
            )
            ax_joint.set_ylabel(
                self._format_axis_label(y_detector, y_units),
                fontsize=label_font_size,
            )

            show_left_side = not (remove_y_labels and c != 0)

            ax_joint.tick_params(
                axis="both",
                which="major",
                bottom=True,
                top=show_top_ticks,
                left=show_left_side,
                right=show_right_ticks,
                labelbottom=True,
                labelleft=show_left_side,
                labeltop=False,
                labelright=False,
                labelsize=tick_label_font_size,
                length=4,
            )

            ax_joint.tick_params(
                axis="both",
                which="minor",
                bottom=True,
                top=show_top_ticks,
                left=show_left_side,
                right=show_right_ticks,
                length=2,
            )

            if not show_top_ticks:
                ax_joint.xaxis.set_ticks_position("bottom")
            else:
                ax_joint.xaxis.set_ticks_position("both")

            if show_left_side and show_right_ticks:
                ax_joint.yaxis.set_ticks_position("both")
            elif show_left_side:
                ax_joint.yaxis.set_ticks_position("left")
            elif show_right_ticks:
                ax_joint.yaxis.set_ticks_position("right")
            else:
                ax_joint.yaxis.set_ticks_position("none")

            if remove_y_labels and c != 0:
                ax_joint.set_ylabel("")

            title = titles[i] if titles else ""
            ax_joint.set_title(title, pad=70, fontsize=title_fontsize)

        return fig

from dataclasses import dataclass
from typing import Any, Optional

from TypedUnit import AnyUnit, ureg

from FlowCyPy import (
    FlowCytometer,
    digital_processing,
    fluidics,
    opto_electronics,
)


@dataclass(frozen=True)
class PopulationSpecification:
    """Declarative specification for one particle population."""

    name: str
    characteristic_diameter: AnyUnit
    spread: float
    refractive_index_mean: AnyUnit
    refractive_index_standard_deviation: AnyUnit
    minimum_refractive_index: Optional[AnyUnit] = None
    maximum_refractive_index: Optional[AnyUnit] = None
    concentration: AnyUnit = None
    sampling_method: object = None


def _build_population_with_cutoffs(
    *,
    medium_refractive_index,
    specification: PopulationSpecification,
    minimum_diameter_after_sec: Optional[AnyUnit],
    reduce_concentration_consistently: bool,
):
    """Build a sphere population using the current FlowCyPy API."""

    diameter_distribution = fluidics.distributions.RosinRammler(
        scale=specification.characteristic_diameter,
        shape=float(specification.spread),
        low_cutoff=minimum_diameter_after_sec,
    )

    refractive_index_distribution = fluidics.distributions.Normal(
        mean=specification.refractive_index_mean,
        standard_deviation=specification.refractive_index_standard_deviation,
        low_cutoff=specification.minimum_refractive_index,
        high_cutoff=specification.maximum_refractive_index,
    )

    concentration = specification.concentration

    if reduce_concentration_consistently:
        concentration *= (
            diameter_distribution.proportion_within_cutoffs()
            * refractive_index_distribution.proportion_within_cutoffs()
        )

    return fluidics.populations.SpherePopulation(
        name=specification.name,
        concentration=concentration,
        medium_refractive_index=medium_refractive_index,
        refractive_index=refractive_index_distribution,
        diameter=diameter_distribution,
        sampling_method=specification.sampling_method,
    )


def run_sec_swarm_demo(
    *,
    minimum_diameter_after_sec: Optional[AnyUnit],
    ev_spread: float,
    lp_spread: float,
    wavelength: AnyUnit,
    threshold: str,
    trigger_channel: str,
    saturation_levels=None,
    ev_characteristic_diameter: AnyUnit = 120 * ureg.nanometer,
    lp_characteristic_diameter: AnyUnit = 40 * ureg.nanometer,
    lp_concentration: AnyUnit = 5e15 * ureg.particle / ureg.milliliter,
    ev_concentration: AnyUnit = 5e9 * ureg.particle / ureg.milliliter,
    lp_refractive_index_mean: AnyUnit = 1.47 * ureg.RIU,
    lp_refractive_index_standard_deviation: AnyUnit = 0.01 * ureg.RIU,
    ev_refractive_index_mean: AnyUnit = 1.39 * ureg.RIU,
    ev_refractive_index_standard_deviation: AnyUnit = 0.01 * ureg.RIU,
    lp_minimum_refractive_index: Optional[AnyUnit] = None,
    lp_maximum_refractive_index: Optional[AnyUnit] = None,
    ev_minimum_refractive_index: Optional[AnyUnit] = None,
    ev_maximum_refractive_index: Optional[AnyUnit] = None,
    reduce_concentration_consistently: bool = True,
    dilution_factor: float = 80.0,
    run_time: AnyUnit = 1 * ureg.millisecond,
    gamma_monte_carlo_samples: int = 10_000,
):
    """Run an SEC-style flow-cytometry simulation."""

    flow_cell = fluidics.FlowCell(
        sample_volume_flow=fluidics.SampleFlowRate.MEDIUM.value,
        sheath_volume_flow=fluidics.SheathFlowRate.MEDIUM.value,
        width=200 * ureg.micrometer,
        height=100 * ureg.micrometer,
        perfectly_aligned=True,
    )

    scatterer_collection = fluidics.ScattererCollection()

    medium_refractive_index = fluidics.distributions.Delta(
        1.33 * ureg.RIU
    )

    lp_specification = PopulationSpecification(
        name="LPs",
        characteristic_diameter=lp_characteristic_diameter,
        spread=float(lp_spread),
        refractive_index_mean=lp_refractive_index_mean,
        refractive_index_standard_deviation=(
            lp_refractive_index_standard_deviation
        ),
        minimum_refractive_index=lp_minimum_refractive_index,
        maximum_refractive_index=lp_maximum_refractive_index,
        concentration=lp_concentration,
        sampling_method=fluidics.populations.GammaModel(
            number_of_samples=gamma_monte_carlo_samples,
        ),
    )

    ev_specification = PopulationSpecification(
        name="EVs",
        characteristic_diameter=ev_characteristic_diameter,
        spread=float(ev_spread),
        refractive_index_mean=ev_refractive_index_mean,
        refractive_index_standard_deviation=(
            ev_refractive_index_standard_deviation
        ),
        minimum_refractive_index=ev_minimum_refractive_index,
        maximum_refractive_index=ev_maximum_refractive_index,
        concentration=ev_concentration,
        sampling_method=fluidics.populations.ExplicitModel(),
    )

    lp_population = _build_population_with_cutoffs(
        medium_refractive_index=medium_refractive_index,
        specification=lp_specification,
        minimum_diameter_after_sec=minimum_diameter_after_sec,
        reduce_concentration_consistently=(
            reduce_concentration_consistently
        ),
    )

    ev_population = _build_population_with_cutoffs(
        medium_refractive_index=medium_refractive_index,
        specification=ev_specification,
        minimum_diameter_after_sec=minimum_diameter_after_sec,
        reduce_concentration_consistently=(
            reduce_concentration_consistently
        ),
    )

    if ev_concentration != 0:
        scatterer_collection.add_population(ev_population)

    if lp_concentration != 0:
        scatterer_collection.add_population(lp_population)

    if dilution_factor != 1.0:
        scatterer_collection.dilute(float(dilution_factor))

    fluidics_system = fluidics.Fluidics(
        scatterer_collection=scatterer_collection,
        flow_cell=flow_cell,
    )

    beam = opto_electronics.source.Gaussian(
        waist_z=10 * ureg.micrometer,
        waist_y=60 * ureg.micrometer,
        wavelength=wavelength,
        optical_power=200 * ureg.milliwatt,
        include_shot_noise=False,
        debug_mode=False,
    )

    detector_side = opto_electronics.Detector(
        name="side",
        phi_angle=90 * ureg.degree,
        numerical_aperture=0.9 * ureg.AU,
        responsivity=10 * ureg.ampere / ureg.watt,
        dark_current=20 * ureg.nanoampere,
    )

    detector_forward = opto_electronics.Detector(
        name="forward",
        phi_angle=0 * ureg.degree,
        numerical_aperture=0.2 * ureg.AU,
        cache_numerical_aperture=0.08 * ureg.AU,
        responsivity=10 * ureg.ampere / ureg.watt,
        dark_current=20 * ureg.nanoampere,
    )

    amplifier = opto_electronics.Amplifier(
        gain=0.1 * ureg.volt / ureg.ampere,
        bandwidth=10 * ureg.megahertz,
        voltage_noise_density=(
            0.00001 * ureg.nanovolt / ureg.sqrt_hertz
        ),
    )

    digitizer = opto_electronics.Digitizer(
        bit_depth=20,
        use_auto_range=True,
        sampling_rate=30 * ureg.megahertz,
        debug_mode=False,
    )

    analog_processing = [
        opto_electronics.circuits.BesselLowPass(
            cutoff_frequency=2 * ureg.megahertz,
            order=4,
            gain=2,
        ),
    ]

    optical_system = opto_electronics.OptoElectronics(
        detectors=[detector_side, detector_forward],
        source=beam,
        amplifier=amplifier,
        digitizer=digitizer,
        analog_processing=analog_processing,
    )

    discriminator = digital_processing.discriminator.DynamicWindow(
        trigger_channel=trigger_channel,
        threshold=threshold,
        pre_buffer=20,
        post_buffer=20,
        max_triggers=-1,
    )

    peak_algorithm = digital_processing.peak_locator.GlobalPeakLocator(
        compute_width=False,
        debug_mode=False,
    )

    processing = digital_processing.DigitalProcessing(
        discriminator=discriminator,
        peak_algorithm=peak_algorithm,
    )

    cytometer = FlowCytometer(
        fluidics=fluidics_system,
        background_power=0.00001 * ureg.milliwatt,
    )

    return cytometer.run(
        opto_electronics=optical_system,
        run_time=run_time,
        digital_processing=processing,
    )

plt.close('all')

# EV + LP
sec_values = [0, 0, 35, 70] * ureg.nanometer
ev_concentrations = [5e10, 5e10, 5e10, 5e10, 5e10] * ureg.particle / ureg.milliliter
lp_concentrations = [0, 5e12, 5e12, 5e12, 5e12] * ureg.particle / ureg.milliliter

run_records = []
for index, (sec, lp_concentration, ev_concentration) in enumerate(zip(sec_values, lp_concentrations, ev_concentrations)):

    print(f"{index} / {len(sec_values)}")

    run_record = run_sec_swarm_demo(
        wavelength=488 * ureg.nanometer,
        trigger_channel='side',
        reduce_concentration_consistently=True,
        minimum_diameter_after_sec=sec,
        saturation_levels=[-2 * ureg.millivolt, 2 * ureg.millivolt],
        ev_spread=1.1,
        lp_spread=0.9,
        ev_characteristic_diameter=120 * ureg.nanometer,
        lp_characteristic_diameter=40 * ureg.nanometer,
        lp_concentration=lp_concentration * 10,
        ev_concentration=ev_concentration,
        dilution_factor=1000.0 / 3,
        threshold='5sigma',
        # threshold=10 * ureg.millivolt,
        gamma_monte_carlo_samples=10_000,
        lp_refractive_index_mean=1.47 * ureg.RIU,
        lp_refractive_index_standard_deviation=0.01 * ureg.RIU,
        ev_refractive_index_mean=1.39 * ureg.RIU,
        ev_refractive_index_standard_deviation=0.01 * ureg.RIU,
        run_time=10 * ureg.millisecond,
    )

    run_records.append(run_record)
