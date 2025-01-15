from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
import pandas as pd
from typing import List, Dict, Tuple
import seaborn as sns
import matplotlib.pyplot as plt
from MPSPlots.styles import mps

class BaseClassifier:
    def filter_dataframe(self, dataframe: pd.DataFrame, features: list, detectors: list = None) -> object:
        """
        Filter the DataFrame based on the selected features and detectors.

        Parameters
        ----------
        features : list
            List of features to use for filtering. Options include 'Heights', 'Widths', 'Areas'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.

        Returns
        -------
        DataFrame
            A filtered DataFrame containing only the selected detectors and features.

        Raises
        ------
        ValueError
            If no matching features are found for the given detectors and features.
        """
        # Determine detectors to use

        if detectors is None:
            detectors = dataframe.columns.get_level_values(0).unique().tolist()

        return dataframe.loc[:, (features, detectors)]


class KmeansClassifier(BaseClassifier):
    def __init__(self, number_of_cluster: int) -> None:
        """
        Initialize the Classifier.

        Parameters
        ----------
        dataframe : DataFrame
            The input dataframe with multi-index columns.
        """
        self.number_of_cluster = number_of_cluster
        # self.dataframe = dataframe
        # self.dataframe['Label'] = 0  # Initialize labels as 0

    def run(self, dataframe: pd.DataFrame, features: list = ['Height'], detectors: list = None, random_state: int = 42) -> pd.DataFrame:
        """
        Run KMeans clustering on the selected features and detectors.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The input DataFrame with multi-index (e.g., by 'Detector').
        features : list
            List of features to use for clustering. Options include 'Height', 'Width', 'Area'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.
        random_state : int, optional
            Random state for KMeans, by default 42.

        Returns
        -------
        pd.DataFrame
            DataFrame with clustering labels added.
        """
        # Filter the DataFrame
        sub_dataframe = self.filter_dataframe(dataframe=dataframe, features=features, detectors=detectors)

        # Ensure data is dequantified if it uses Pint quantities
        if hasattr(sub_dataframe, 'pint'):
            sub_dataframe = sub_dataframe.pint.dequantify().droplevel('unit', axis=1)

        # Run KMeans
        kmeans = KMeans(n_clusters=self.number_of_cluster, random_state=random_state)
        labels = kmeans.fit_predict(sub_dataframe)

        dataframe['Label'] = labels

        return labels

    def plot(self, x_detector: str, y_detector: str) -> None:
        with plt.style.context(mps):
            sns.jointplot(
                data=self.sub_dataframe,
                x=x_detector,
                hue='Label',
                y=y_detector
            )

        plt.show()

class DBScanClassifier(BaseClassifier):
    def __init__(self, dataframe: object) -> None:
        """
        Initialize the DBScanClassifier.

        Parameters
        ----------
        dataframe : DataFrame
            The input dataframe with multi-index columns.
        """
        self.dataframe = dataframe
        self.dataframe['Label'] = -1  # Initialize labels as -1 (noise for DBSCAN)

    def run(self, eps: float = 0.5, min_samples: int = 5, features: list = ['Heights'], detectors: list = None) -> None:
        """
        Run DBSCAN clustering on the selected features and detectors.

        Parameters
        ----------
        eps : float, optional
            The maximum distance between two samples for them to be considered as in the same neighborhood, by default 0.5.
        min_samples : int, optional
            The number of samples in a neighborhood for a point to be considered a core point, by default 5.
        features : list
            List of features to use for clustering. Options include 'Heights', 'Widths', 'Areas'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.
        """
        # Filter the DataFrame
        sub_dataframe = self.filter_dataframe(features=features, detectors=detectors)

        # Ensure data is dequantified if it uses Pint quantities
        if hasattr(sub_dataframe, 'pint'):
            sub_dataframe = sub_dataframe.pint.dequantify()

        # Handle missing values (if necessary)
        sub_dataframe = sub_dataframe.fillna(0).to_numpy()

        # Run DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        sub_dataframe['Label'] = dbscan.fit_predict(sub_dataframe)

        return sub_dataframe


class RangeClassifier:
    """
    A classifier for assigning population labels based on defined ranges.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The input dataframe with features to classify.
    feature : str
        The column name of the feature to classify.

    Attributes
    ----------
    dataframe : pd.DataFrame
        The dataframe with an added 'Label' column.
    ranges : List[Tuple[float, float, str]]
        The list of ranges and their associated labels.
    """

    def __init__(self, dataframe: pd.DataFrame) -> None:
        """
        Initialize the classifier.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The input dataframe with features to classify.
        feature : str
            The column name of the feature to classify.
        """
        self.dataframe = dataframe
        self.ranges = []  # To store the ranges and their labels

    def run(self, ranges: Dict[str, Tuple[float, float]]) -> None:
        """
        Classify the dataframe by assigning population labels based on specified ranges applied to the index.

        Parameters
        ----------
        ranges : dict
            A dictionary where keys are population names (labels) and values are tuples
            specifying the (lower, upper) bounds of the range for that population.

        Example
        -------
        >>> ranges = {
        >>>     'Population 0': (0, 100),
        >>>     'Population 1': (100, 150),
        >>>     'Population 2': (150, 200)
        >>> }
        >>> classifier.run(ranges)
        """
        # Create conditions and corresponding labels
        conditions = []
        labels = []
        for label, (lower, upper) in ranges.items():
            conditions.append((self.dataframe.index >= lower) & (self.dataframe.index < upper))
            labels.append(label)

        # Use np.select to efficiently apply conditions
        self.dataframe['Label'] = pd.Series(
            pd.cut(self.dataframe.index,
                   bins=[float('-inf')] + [upper for _, (_, upper) in ranges.items()],
                   labels=list(ranges.keys()),
                   include_lowest=True),
            index=self.dataframe.index)

