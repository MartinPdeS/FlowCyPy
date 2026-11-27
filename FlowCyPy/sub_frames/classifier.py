import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from ._plotting import figure_options


class ClassifierDataFrame(pd.DataFrame):
    """
    A subclass of pandas DataFrame for classifying peaks.
    """

    @property
    def _constructor(self) -> type:
        """Ensure operations return instances of ScattererDataFrame."""
        return self.__class__

    @figure_options
    def plot(self, x: str, y: str) -> plt.Figure:
        """
        Visualize the classification of peaks using a scatter plot.

        Parameters
        ----------
        x : tuple[str, str]
            Tuple ``(detector_name, feature_name)`` used for the x axis.
        y : tuple[str, str]
            Tuple ``(detector_name, feature_name)`` used for the y axis.

        Raises
        ------
        ValueError
            If the 'Label' column is missing.

        Returns
        -------
        plt.Figure
            Joint scatter plot colored by the assigned class label.
        """
        x_detector, x_feature = x
        y_detector, y_feature = y
        if "Label" not in self.columns:
            raise ValueError(
                "Missing 'Label' column. Run `classify_dataset` before plotting."
            )

        temp = self.unstack(level=2)

        x = temp[(x_feature, x_detector)]
        y = temp[(y_feature, y_detector)]
        label = temp[("Label", y_detector)]

        grid = sns.jointplot(
            x=x,
            y=y,
            hue=label,
        )

        grid.set_axis_labels(
            f"{x_detector}: {x_feature}",
            f"{y_detector}: {y_feature}",
        )
        grid.figure.suptitle("Event classification")
        legend = grid.ax_joint.get_legend()
        if legend is not None:
            legend.set_title("Population")
        return grid.figure
