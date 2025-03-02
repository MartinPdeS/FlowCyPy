import pytest
import pandas as pd
import numpy as np
from sklearn.datasets import make_blobs
from FlowCyPy.classifier import KmeansClassifier, GaussianMixtureClassifier, DBSCANClassifier

@pytest.fixture
def generate_test_data():
    """
    Generate synthetic multi-index DataFrame for clustering tests.

    Returns
    -------
    pd.DataFrame
        A DataFrame with multi-index columns where the first level represents
        features and the second level represents detectors.
    """
    X, _ = make_blobs(n_samples=300, centers=3, random_state=42, cluster_std=1.0)
    features = ['Feature1', 'Feature2']
    detectors = ['Detector1', 'Detector2']

    # Create multi-index columns
    multi_columns = pd.MultiIndex.from_product([features, detectors], names=["Feature", "Detector"])

    # Generate random data for each detector
    data = np.tile(X, (1, len(detectors)))  # Duplicate X for each detector
    dataframe = pd.DataFrame(data, columns=multi_columns)

    return dataframe


def test_kmeans_classifier(generate_test_data):
    """
    Test KMeansClassifier on synthetic data.
    """
    data = generate_test_data
    classifier = KmeansClassifier(number_of_cluster=3)

    # Run classifier
    data = classifier.run(dataframe=data, features=['Feature1', 'Feature2'])

    # Assert labels are assigned and are within the expected range
    assert 'Label' in data.columns
    assert len(set(data['Label'].unique())) == 3


def test_gaussian_mixture_classifier(generate_test_data):
    """
    Test GaussianMixtureClassifier on synthetic data.
    """
    data = generate_test_data
    classifier = GaussianMixtureClassifier(number_of_components=3)

    # Run classifier
    data = classifier.run(dataframe=data, features=['Feature1', 'Feature2'])

    # Assert labels are assigned and are within the expected range
    assert 'Label' in data.columns
    assert len(set(data['Label'].unique())) == 3


def test_dbscan_classifier(generate_test_data):
    """
    Test DBSCANClassifier on synthetic data.
    """
    data = generate_test_data
    classifier = DBSCANClassifier(epsilon=1.0, min_samples=5)

    # Run classifier
    data = classifier.run(dataframe=data, features=['Feature1', 'Feature2'])

    # Assert labels are assigned and are within the expected range
    assert 'Label' in data.columns
    assert len(set(data['Label'].unique())) <= 5


if __name__ == '__main__':
    pytest.main(["-W error", __file__])
