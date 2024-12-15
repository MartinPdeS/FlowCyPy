from sklearn.cluster import KMeans


class BaseClassifier:
    def filter_dataframe(self, features: list, detectors: list = None) -> object:
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
            detectors = self.dataframe.columns.get_level_values(0).unique().tolist()

        # Build the list of selected columns
        selected_features = [
            (detector, feature) for detector in detectors for feature in features
            if (detector, feature) in self.dataframe.columns
        ]

        if not selected_features:
            raise ValueError("No matching features found for the given detectors and features.")

        # Return the filtered DataFrame
        return self.dataframe[selected_features]


class KmeansClassifier(BaseClassifier):
    def __init__(self, dataframe: object) -> None:
        """
        Initialize the Classifier.

        Parameters
        ----------
        dataframe : DataFrame
            The input dataframe with multi-index columns.
        """
        self.dataframe = dataframe
        self.dataframe['Label'] = 0  # Initialize labels as 0



    def run(self, number_of_cluster: int, features: list = ['Heights'], detectors: list = None, random_state: int = 42) -> None:
        """
        Run KMeans clustering on the selected features and detectors.

        Parameters
        ----------
        number_of_cluster : int
            Number of clusters for KMeans.
        features : list
            List of features to use for clustering. Options include 'Heights', 'Widths', 'Areas'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.
        random_state : int, optional
            Random state for KMeans, by default 42.
        """
        # Filter the DataFrame
        X = self.filter_dataframe(features=features, detectors=detectors)

        # Ensure data is dequantified if it uses Pint quantities
        if hasattr(X, 'pint'):
            X = X.pint.dequantify()

        # Run KMeans
        kmeans = KMeans(n_clusters=number_of_cluster, random_state=random_state)
        self.dataframe['Label'] = kmeans.fit_predict(X)

from sklearn.cluster import DBSCAN
import numpy as np

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
        X = self.filter_dataframe(features=features, detectors=detectors)

        # Ensure data is dequantified if it uses Pint quantities
        if hasattr(X, 'pint'):
            X = X.pint.dequantify()

        # Handle missing values (if necessary)
        X = X.fillna(0).to_numpy()

        # Run DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        self.dataframe['Label'] = dbscan.fit_predict(X)
