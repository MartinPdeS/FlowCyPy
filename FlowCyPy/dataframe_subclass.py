from typing import Optional, Union, List, Tuple, Any
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import seaborn as sns
import pint_pandas
from FlowCyPy import helper, units

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

    @helper.plot_sns
    def plot_2d(self, x: str, y: str, alpha: float = 0.8, bandwidth_adjust: float = 1, color_palette: Optional[Union[str, dict]] = None) -> plt.Figure:
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
            marginal_kws={'bw_adjust': bandwidth_adjust}
        )

        grid.figure.suptitle("Scatterer Sampling Distribution")
        grid.ax_joint.set_xlabel(f"{x} [{x_unit}]")
        grid.ax_joint.set_ylabel(f"{y} [{y_unit}]")
        return grid

    @helper.plot_3d
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

        ax.set_xlabel(f"{x} [{x_unit}]", labelpad=20)
        ax.set_ylabel(f"{y} [{y_unit}]", labelpad=20)
        ax.set_zlabel(f"{z} [{z_unit}]", labelpad=20)
        ax.set_title("Scatterer Sampling Distribution")
        return ax.figure

    @helper._pre_plot
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

        df[x] = helper.clip_data(signal=df[[x]], clip_value=clip_data)

        sns.histplot(data=df, x=df[x], ax=ax, kde=kde, bins=bins, color=color, hue=df['Population'])
        ax.set_xlabel(f"{x} [{unit}]")
        ax.set_title(f"Distribution of {x}")

        return figure


class ClassifierDataFrame(BaseSubFrame):
    """
    A subclass of pandas DataFrame for classifying peaks.
    """
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
            raise ValueError("Missing 'Label' column. Run `classify_dataset` before plotting.")

        temp = self.pint.dequantify().sort_index(axis=1)

        grid = sns.jointplot(
            x=temp[(feature, x)].values.squeeze(),
            y=temp[(feature, y)].values.squeeze(),
            hue=temp['Label'].values.squeeze()
        )

        grid.figure.suptitle('Event classification')
        return grid


class PeakDataFrame(BaseSubFrame):
    """
    A subclass of pandas DataFrame for handling peak data with custom plotting.
    """
    def plot(self, **kwargs) -> Any:
        """
        Dispatch plotting to 2D or 3D methods based on provided kwargs.
        """
        if 'z' in kwargs:
            return self.plot_3d(**kwargs)

        if 'y' in kwargs:
            return self.plot_2d(**kwargs)

        return self.hist(**kwargs)

    def standard_deviation(self, detector_name: str, metrics: str | slice = slice(None)):
        """
        Calculate the standard deviation of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the standard deviation.
        metrics : str or slice, optional
            The metrics to consider for the standard deviation calculation. Defaults to all metrics.

        Returns
        -------
        units.Quantity
            The standard deviation of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]

        return sub_frame.std()

    def robust_standard_deviation(self, detector_name: str, metrics: str | slice = slice(None)):
        """
        Calculate the robust standard deviation of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the robust standard deviation.
        metrics : str or slice, optional
            The metrics to consider for the standard deviation calculation. Defaults to all metrics.

        Returns
        -------
        units.Quantity
            The robust standard deviation of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]

        return numpy.abs(sub_frame - sub_frame.median()).median() * 1.4826

    def mean(self, detector_name: str, metrics: str | slice = slice(None)):
        """
        Calculate the mean of the specified detector's signal.

        Parameters
        ----------
        detector_name : str
            The name of the detector for which to calculate the mean.

        Returns
        -------
        units.Quantity
            The mean of the signal in the specified units.
        """
        sub_frame = self.loc[detector_name, metrics]
        return sub_frame.mean(axis=0)

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

    @helper._pre_plot
    def hist(
        self,
        x: tuple[str, str],
        figure_size: tuple = (10, 6),
        kde: bool = False,
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, units.Quantity]] = None
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
        x : tuple[str, str]
            The column name to plot (eg. ('forward', 'Height')).
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
            values above the corresponding quantile (e.g. the top 20% of values) are excluded.
            If a pint.Quantity is given, values above that absolute value are removed.
        save_as : str, optional
            If provided, the figure is saved to this filename.
        show : bool, optional
            If True, displays the plot immediately (default: True).

        Returns
        -------
        plt.Figure
            The histogram figure.
        """
        if len(self) == 1:
            return

        detector_name, feature = x

        figure, ax = plt.subplots(ncols=1, nrows=1, figsize=figure_size)

        ax.set_ylabel(f"{detector_name} : {feature}  [count]")

        kde = False

        data = self.loc[x].sort_index()

        data = helper.clip_data(signal=data, clip_value=clip_data)

        sns.histplot(x=data, ax=ax, kde=kde, bins=bins, color=color)

        return figure

    @helper.plot_sns
    def plot_2d(self, x: tuple[str, str], y: tuple[str, str], feature: str = 'Height', bandwidth_adjust: float = 0.8) -> plt.Figure:
        """
        Plot the joint KDE distribution of a feature between two detectors.

        Parameters
        ----------
        x : tuple[str, str]
            Detector for the x-axis.
        y : tuple[str, str]
            Detector for the y-axis.
        bandwidth_adjust : float, optional
            KDE bandwidth adjustment (default: 0.8).

        Returns
        -------
        plt.Figure
            The joint KDE plot figure.
        """
        x_detector, x_feature = x
        y_detector, y_feature = y

        features = tuple(set([x_feature, y_feature]))

        df = self.loc[[x_detector, y_detector], features].sort_index()

        grid = sns.jointplot(
            x=df.loc[x],
            y=df.loc[y],
            kind='kde',
            fill=True,
            cmap="Blues",
            joint_kws={'bw_adjust': bandwidth_adjust, 'alpha': 0.7}
        )

        grid.figure.suptitle("Peaks properties")
        grid.ax_joint.scatter(
            df.loc[x],
            df.loc[y],
            color='C1',
            alpha=0.6
        )

        grid.set_axis_labels(f"Detector: {x_detector} : feature: {x_feature}", f"Detector: {y_detector} : feature: {y_feature}")
        return grid

    @helper.plot_3d
    def plot_3d(self, ax: plt.Axes, x: str, y: str, z: str) -> plt.Figure:
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
        x_detector, x_feature = x
        y_detector, y_feature = y
        z_detector, z_feature = z

        df = self.pint.dequantify().astype(float)
        x_series = df.loc[x].values
        y_series = df.loc[y].values
        z_series = df.loc[z].values


        ax.scatter(x_series, y_series, z_series)

        ax.set_xlabel(f"{x_detector} : {x_feature}", labelpad=20)
        ax.set_ylabel(f"{y_detector} : {y_feature}", labelpad=20)
        ax.set_zlabel(f"{z_detector} : {z_feature}", labelpad=20)

        ax.set_title("Peaks Properties")



class BaseAcquisitionDataFrame(BaseSubFrame):
    """
    Base class for acquisition data frames with common plotting and logging functionalities.
    """
    def __init__(self, dataframe: pd.DataFrame, scatterer = None, **attributes: dict):
        super().__init__(dataframe)

        self.attrs['scatterer'] = scatterer
        self.attrs.update(attributes)

        self.normalize_units()

    def digitalize(self, digitizer: object):
        """
        Convert analog signals to digital signals using the provided digitizer.

        Parameters
        ----------
        digitizer : object
            An instance of a digitizer that implements the `capture_signal` method.

        Returns
        -------
        BaseAcquisitionDataFrame
            A new instance of the class with digitalized signals.
        """
        digital_df = pd.DataFrame(
            index=self.index,
            columns=self.columns,
            data=dict(Time=self.Time)
        )

        for detector_name in self.detector_names:
            analog_signal = self[detector_name]
            digitized_signal, _ = digitizer.capture_signal(signal=analog_signal)

            digital_df[detector_name] = pint_pandas.PintArray(digitized_signal, units.bit_bins)

        return self.__class__(
            dataframe=digital_df,
            plot_type='digital',
            scatterer=self.attrs['scatterer']
        )

    def normalize_units(self, signal_units: units.Quantity | str = 'auto', time_units: units.Quantity | str = 'auto') -> None:
        """
        Normalize the DataFrame's signal and time columns to specified units.

        Parameters
        ----------
        signal_units : units.Quantity
            The units to which the signal columns should be normalized.
        time_units : units.Quantity
            The units to which the time column should be normalized.
        """

        if signal_units == 'auto':
            signal_units = self[self.detector_names[0]].max().to_compact().units

        if time_units == 'auto':
            time_units = self['Time'].max().to_compact().units

        for columns in self.columns:
            if columns == 'Time':
                self[columns] = self[columns].pint.to(time_units)
            else:
                self[columns] = self[columns].pint.to(signal_units)

        self.signal_units = self.iloc[0, 0].units
        self.time_units = self['Time'].pint.units

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
    def scatterer(self) -> object:
        return self.attrs['scatterer']

    @property
    def detector_names(self) -> List[str]:
        """Return a list of unique detector names."""
        return [col for col in self.columns if col != 'Time']


    @helper._pre_plot
    def plot(self, filter_population: Union[str, List[str]] = None, figure_size: tuple = (12, 5), **kwargs) -> None:
        """
        Plot acquisition data for each detector and the scatterer events.
        This method creates a multi-panel plot with each detector's signal and a scatterer event plot.

        Parameters
        ----------
        filter_population : Union[str, List[str]], optional
            If provided, filters the scatterer events to only include those from the specified population(s).
            Can be a single population name or a list of names.
        figure_size : tuple, optional
            Size of the figure in inches (default: (12, 5)).
        show : bool, optional
            Whether to display the plot (default: True).
        save_as : str, optional
            If provided, the figure is saved to this filename.

        Returns
        -------
        plt.Figure
            The figure containing the acquisition data plots.

        """
        n_plots = len(self.detector_names) + 1  # One extra plot for events
        time_units = self["Time"].max().to_compact().units
        signal_units = self.iloc[0, 0].units

        figure, axes_array = plt.subplots(
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

        return figure

    @helper._pre_plot
    def hist(
        self,
        figure_size: tuple = (10, 6),
        kde: bool = False,
        bins: Optional[int] = 'auto',
        color: Optional[Union[str, dict]] = None,
        clip_data: Optional[Union[str, units.Quantity]] = None,
    ) -> plt.Figure:
        """
        Plot a histogram distribution for a given column using Seaborn, with an option to remove extreme values.

        Parameters
        ----------
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
        save_as : str, optional
            If provided, the figure is saved to this filename.

        Returns
        -------
        plt.Figure
            The figure containing the acquisition data plots.
        """
        if len(self) == 1:
            return

        n_plots = len(self.detector_names)

        figure, axes = plt.subplots(nrows=n_plots, figsize=figure_size, sharex=True, sharey=True)

        for ax, detector_name in zip(axes, self.detector_names):
            ax.set_ylabel(detector_name)
            # ax.set_xlabel(f"{x} [{unit}]")
            signal = self[detector_name].pint.quantity.magnitude

            signal = helper.clip_data(signal=signal, clip_value=clip_data)

            sns.histplot(x=signal, ax=ax, kde=kde, bins=bins, color=color)

        return figure


class AcquisitionDataFrame(BaseAcquisitionDataFrame):
    """
    DataFrame subclass for continuous (analog) acquisition data.
    """
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
