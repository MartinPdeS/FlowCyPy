from typing import Optional, Union, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from FlowCyPy import helper
from MPSPlots.styles import mps
from FlowCyPy import units

class ScattererDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """

    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return ScattererDataFrame


    @helper.plot_sns
    def plot(self, x: str = 'Size', y: str = 'RefractiveIndex', alpha: float = 0.8, bandwidth_adjust: float = 1, color_palette: Optional[Union[str, dict]] = None) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn jointplot,
        automatically extracting units from Pint arrays.
        """
        df_reset = self.reset_index()

        if len(df_reset) == 1:
            return

        # Extract units if the column contains Pint Quantities
        df_reset[x] = df_reset[x].pint.to(df_reset[x].max().to_compact().units)
        df_reset[y] = df_reset[y].pint.to(df_reset[y].max().to_compact().units)
        x_unit = getattr(df_reset[x], "pint", None)
        y_unit = getattr(df_reset[y], "pint", None)

        x_label = f"{x} [{x_unit.units}]" if x_unit else x
        y_label = f"{y} [{y_unit.units}]" if y_unit else y

        with plt.style.context(mps):
            grid = sns.jointplot(
                data=df_reset,
                x=x,
                y=y,
                hue='Population',
                palette=color_palette,
                kind='scatter',
                alpha=alpha,
                marginal_kws=dict(bw_adjust=bandwidth_adjust)
            )

        grid.figure.suptitle("Scatterer Sampling Distribution")

        # Set axis labels with extracted units
        grid.ax_joint.set_xlabel(x_label)
        grid.ax_joint.set_ylabel(y_label)

        return grid

class ContinuousAcquisitionDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return ContinuousAcquisitionDataFrame

    def plot(
        self,
        figure_size: tuple = (10, 6),
        show: bool = True,
        save_filename: str = None,
        filter_population: str | List[str] = None,
    ) -> None:
        """
        Visualizes raw signals for all detector channels and the scatterer distribution.

        Parameters
        ----------
        figure_size : tuple, optional
            Size of the plot in inches (default: (10, 6)).
        show : bool, optional
            If True, displays the plot immediately (default: True).
        show_populations : str or list of str, optional
            List of population names to highlight in the event plot. If None, shows all populations.
        save_filename : str, optional
            If provided, saves the figure to the specified file.
        """
        n_plots = len(self.index.get_level_values('Detector').unique()) + 1  # One extra plot for events

        time_units = self.Time.max().to_compact().units

        with plt.style.context(mps):
            fig, axes = plt.subplots(
                ncols=1,
                nrows=n_plots,
                figsize=figure_size,
                sharex=True,
                height_ratios=[1] * (n_plots - 1) + [0.5]
            )

        # Plot digitized and continuous signals for each detector
        for ax, (detector_name, group) in zip(axes[:-1], self.groupby("Detector")):
            # Convert time and signal data to the appropriate units
            time_data = group["Time"].pint.to(time_units)
            digitized_signal = group["DigitizedSignal"]

            # Plot digitized signal
            ax.step(time_data, digitized_signal, label="Digitized Signal", where='mid')
            ax.set_ylabel(detector_name)
            ax.set_ylim([0, self.attrs['bit_depth']])

            # Twin axis for continuous signal
            ax2 = ax.twinx()
            cont_time, cont_signal, cont_signal_units = self._get_continuous_signal(detector_name, time_units)
            ax2.plot(cont_time, cont_signal, color='black', linewidth=1, linestyle='-', label='Continuous Signal', zorder=0)

            # Set y-limits for the continuous signal
            saturation_levels = self.attrs['saturation_levels'][detector_name]
            if saturation_levels[0] != saturation_levels[1]:
                ax2.set_ylim(saturation_levels)

        # Add event markers to the last subplot
        # Handle `filter_population` default case
        if filter_population is None:
            filter_population = self.attrs['scatterer_dataframe'].index.get_level_values('Population').unique()

        helper.add_event_to_ax(self.attrs['scatterer_dataframe'], ax=axes[-1], time_units=time_units, show_populations=filter_population)
        axes[-1].set_xlabel(f"Time [{time_units}]")

        # Save or show the figure
        if save_filename:
            fig.savefig(fname=save_filename)
        if show:
            plt.show()

    def _get_continuous_signal(self, detector_name: str, time_units: units.Quantity):
        """
        Retrieves and converts the continuous signal data for a given detector.

        Parameters
        ----------
        detector_name : str
            Name of the detector.
        time_units : units.Quantity
            Desired time units.

        Returns
        -------
        tuple
            (time array, signal array, signal units)
        """
        data = self.loc[detector_name]
        cont_time = data['Time'].pint.to(time_units)
        cont_signal = data['Signal']
        cont_signal_units = cont_signal.max().to_compact().units
        return cont_time, cont_signal.pint.to(cont_signal_units), cont_signal_units


class TriggeredAcquisitionDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    bit_depth: int
    saturation_levels: dict
    scatterer_dataframe: pd.DataFrame

    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return PeakDataFrame

    def plot(self, show: bool = True, filter_population: str | List[str] = None) -> None:
        """Plot detected peaks on signal segments."""
        n_plots = len(self.index.get_level_values('Detector').unique()) + 1  # One extra plot for events

        with plt.style.context(mps):
            _, axes = plt.subplots(
                nrows=n_plots,
                ncols=1,
                height_ratios=[1] * (n_plots - 1) + [0.5],
                figsize=(10, 6),
                sharex=True,
                constrained_layout=True
            )

        time_units = self['Time'].max().to_compact().units

        for ax, (detector_name, group) in zip(axes, self.groupby(level='Detector')):
            ax.set_ylabel(detector_name)

            for _, sub_group in group.groupby(level='SegmentID'):
                x = sub_group['Time'].pint.to(time_units)
                digitized = sub_group['DigitizedSignal']
                ax.step(x, digitized, where='mid', linewidth=2)
                ax.set_ylim([0, self.attrs['bit_depth']])

        # Add event markers to the last subplot
        # Handle `filter_population` default case
        if filter_population is None:
            filter_population = self.attrs['scatterer_dataframe'].index.get_level_values('Population').unique()

        helper.add_event_to_ax(self.attrs['scatterer_dataframe'], ax=axes[-1], time_units=time_units, show_populations=filter_population)
        axes[-1].set_xlabel(f"Time [{time_units}]")

        if show:
            plt.show()


class ClassifierDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return ClassifierDataFrame

    @helper.plot_sns
    def plot(self, feature: str, x_detector: str, y_detector: str) -> None:
        """
        Visualize the classification of peaks using a scatter plot.

        Parameters
        ----------
        feature : str
            The feature to classify (e.g., 'Height', 'Width', 'Area').
        x_detector : str
            The detector to use for the x-axis.
        y_detector : str
            The detector to use for the y-axis.

        Raises
        ------
        ValueError
            If the 'Label' column is missing in the data, suggesting that
            the `classify_dataset` method must be called first.
        """
        # Check if 'Label' exists in the dataset
        if 'Label' not in self.columns:
            raise ValueError(
                "The 'Label' column is missing. Ensure the dataset has been classified "
                "by calling the `classify_dataset` method before using `classifier`."
            )

        # Set the plotting style
        with plt.style.context(mps):
            grid = sns.jointplot(
                data=self,
                x=(feature, x_detector),
                y=(feature, y_detector),
                hue='Label',
            )

        grid.figure.suptitle('Event classification')

        return grid


class PeakDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame with a custom plot method.
    """
    bit_depth: int
    saturation_levels: dict
    scatterer_dataframe: pd.DataFrame

    @property
    def _constructor(self):
        """
        Ensures that operations returning DataFrames return instances of CustomDataFrame.
        """
        return PeakDataFrame

    @helper.plot_sns
    def plot(self, x_detector: str, y_detector: str, signal: str = 'Height', bandwidth_adjust: float = 0.8) -> None:
        """
        Plot the joint KDE distribution of the specified signal between two detectors using seaborn,
        optionally overlaying scatter points.

        Parameters
        ----------
        x_detector : str
            Name of the detector to use for the x-axis.
        y_detector : str
            Name of the detector to use for the y-axis.
        signal : str, optional
            The signal column to plot, by default 'Height'.
        bandwidth_adjust : float, optional
            Bandwidth adjustment factor for KDE, by default 0.8.
        """
        # Filter to only include rows for the specified detectors
        x_data = self.loc[x_detector, signal]
        y_data = self.loc[y_detector, signal]

        x_units = x_data.pint.units
        y_units = y_data.pint.units

        with plt.style.context(mps):
            # Create joint KDE plot with scatter points overlay
            grid = sns.jointplot(x=x_data, y=y_data, kind='kde', fill=True, cmap="Blues",
                joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
            )

        grid.figure.suptitle("Peaks properties")
        grid.ax_joint.scatter(x_data, y_data, color='C1', alpha=0.6)

        grid.set_axis_labels(f"{signal} ({x_detector}) [{x_units}]", f"{signal} ({y_detector}) [{y_units}]", fontsize=12)

        return grid
