from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.mixture import GaussianMixture
import pandas as pd
from FlowCyPy.dataframe_subclass import ClassifierDataFrame


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
            detectors = dataframe.columns.get_level_values(1).unique().tolist()

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

        return ClassifierDataFrame(dataframe)

class GaussianMixtureClassifier(BaseClassifier):
    def __init__(self, number_of_components: int) -> None:
        """
        Initialize the Gaussian Mixture Classifier.

        Parameters
        ----------
        number_of_components : int
            Number of Gaussian components (clusters) to use for the model.
        """
        self.number_of_components = number_of_components

    def run(self, dataframe: pd.DataFrame, features: list = ['Height'], detectors: list = None, random_state: int = 42) -> pd.DataFrame:
        """
        Run Gaussian Mixture Model (GMM) clustering on the selected features and detectors.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The input DataFrame with multi-index (e.g., by 'Detector').
        features : list
            List of features to use for clustering. Options include 'Height', 'Width', 'Area'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.
        random_state : int, optional
            Random state for reproducibility, by default 42.

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

        # Run Gaussian Mixture Model
        gmm = GaussianMixture(n_components=self.number_of_components, random_state=random_state)
        labels = gmm.fit_predict(sub_dataframe)

        # Add labels to the original DataFrame
        dataframe['Label'] = labels

        return ClassifierDataFrame(dataframe)

class DBSCANClassifier(BaseClassifier):
    def __init__(self, epsilon: float = 0.5, min_samples: int = 5) -> None:
        """
        Initialize the DBSCAN Classifier.

        Parameters
        ----------
        epsilon : float, optional
            The maximum distance between two samples for them to be considered as neighbors.
            Default is 0.5.
        min_samples : int, optional
            The number of samples in a neighborhood for a point to be considered a core point.
            Default is 5.
        """
        self.epsilon = epsilon
        self.min_samples = min_samples

    def run(self, dataframe: pd.DataFrame, features: list = ['Height'], detectors: list = None) -> pd.DataFrame:
        """
        Run DBSCAN clustering on the selected features and detectors.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The input DataFrame with multi-index (e.g., by 'Detector').
        features : list
            List of features to use for clustering. Options include 'Height', 'Width', 'Area'.
        detectors : list, optional
            List of detectors to use. If None, use all detectors.

        Returns
        -------
        pd.DataFrame
            DataFrame with clustering labels added. Noise points are labeled as -1.
        """
        # Filter the DataFrame
        sub_dataframe = self.filter_dataframe(dataframe=dataframe, features=features, detectors=detectors)

        # Ensure data is dequantified if it uses Pint quantities
        if hasattr(sub_dataframe, 'pint'):
            sub_dataframe = sub_dataframe.pint.dequantify().droplevel('unit', axis=1)

        # Run DBSCAN
        dbscan = DBSCAN(eps=self.epsilon, min_samples=self.min_samples)
        labels = dbscan.fit_predict(sub_dataframe)

        # Add labels to the original DataFrame
        dataframe['Label'] = labels

        return ClassifierDataFrame(dataframe)
