# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import MPSPlots
import seaborn as sns

from FlowCyPy.sub_frames.base import BaseSubFrame


class ClassifierDataFrame(BaseSubFrame):
    """
    A subclass of pandas DataFrame for classifying peaks.
    """

    @MPSPlots.helper.post_mpl_plot
    def plot(self, x: str, y: str) -> plt.Figure:
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
        x_detector, x_feature = x
        y_detector, y_feature = y
        if "Label" not in self.columns:
            raise ValueError(
                "Missing 'Label' column. Run `classify_dataset` before plotting."
            )

        temp = self.pint.dequantify().sort_index(axis=1)

        grid = sns.jointplot(
            x=temp[(x_feature, x_detector)].values.squeeze(),
            y=temp[(y_feature, y_detector)].values.squeeze(),
            hue=temp["Label"].values.squeeze(),
        )

        grid.figure.suptitle("Event classification")
        return grid.figure
