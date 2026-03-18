import numpy as np
import pandas as pd
import pytest

from FlowCyPy.signal_processing.classifier import KmeansClassifier, DBScanClassifier
from FlowCyPy.sub_frames.classifier import ClassifierDataFrame


def make_wide_dataframe(
    data_matrix: np.ndarray,
    features: list[str] | None = None,
    detectors: list[str] | None = None,
) -> pd.DataFrame:
    """
    Build a wide pandas DataFrame compatible with the classifier bindings.

    The returned DataFrame mimics the structure produced by
    ``run_record.peaks.unstack("Detector")``. Its row index is event-based and
    its columns are a MultiIndex with levels ``Feature`` and ``Detector``.

    Parameters
    ----------
    data_matrix : numpy.ndarray
        Two dimensional array of shape ``(n_events, n_columns)`` containing the
        feature values arranged feature by feature across detectors.
    features : list of str, optional
        Feature names. Default is ``["Height"]``.
    detectors : list of str, optional
        Detector names. Default is ``["forward", "side"]``.

    Returns
    -------
    pandas.DataFrame
        Wide DataFrame with MultiIndex columns and an event index.

    Raises
    ------
    ValueError
        If the shape of ``data_matrix`` does not match the number of requested
        features and detectors.
    """
    if features is None:
        features = ["Height"]

    if detectors is None:
        detectors = ["forward", "side"]

    expected_number_of_columns = len(features) * len(detectors)

    if data_matrix.ndim != 2:
        raise ValueError("data_matrix must be two dimensional.")

    if data_matrix.shape[1] != expected_number_of_columns:
        raise ValueError(
            f"Expected {expected_number_of_columns} columns from features and detectors, "
            f"got {data_matrix.shape[1]}."
        )

    columns = pd.MultiIndex.from_product(
        [features, detectors],
        names=["Feature", "Detector"],
    )

    index = pd.MultiIndex.from_arrays(
        [
            np.arange(data_matrix.shape[0], dtype=int),
            np.zeros(data_matrix.shape[0], dtype=int),
        ],
        names=["SegmentID", "PeakID"],
    )

    return pd.DataFrame(data_matrix, index=index, columns=columns)


def make_two_blob_wide_dataframe(
    number_of_samples_per_blob: int = 80,
    random_seed: int = 123,
) -> pd.DataFrame:
    """
    Build a simple two cluster DataFrame for detector based classification tests.

    Parameters
    ----------
    number_of_samples_per_blob : int, default=80
        Number of samples per blob.
    random_seed : int, default=123
        Seed for reproducible synthetic data generation.

    Returns
    -------
    pandas.DataFrame
        Wide DataFrame with two clearly separated blobs.
    """
    random_generator = np.random.default_rng(random_seed)

    blob_a_forward = random_generator.normal(
        loc=0.0, scale=0.25, size=(number_of_samples_per_blob, 1)
    )
    blob_a_side = random_generator.normal(
        loc=0.2, scale=0.25, size=(number_of_samples_per_blob, 1)
    )

    blob_b_forward = random_generator.normal(
        loc=3.0, scale=0.25, size=(number_of_samples_per_blob, 1)
    )
    blob_b_side = random_generator.normal(
        loc=3.2, scale=0.25, size=(number_of_samples_per_blob, 1)
    )

    blob_a = np.hstack([blob_a_forward, blob_a_side])
    blob_b = np.hstack([blob_b_forward, blob_b_side])

    data_matrix = np.vstack([blob_a, blob_b])

    return make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )


def test_kmeans_basic_clustering():
    """
    Test that KmeansClassifier returns a classified DataFrame with one label per event.
    """
    random_generator = np.random.default_rng(42)

    number_of_clusters = 3
    number_of_samples = 50

    data_matrix = random_generator.random((number_of_samples, 2))
    dataframe = make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )

    classifier = KmeansClassifier(number_of_clusters)
    classified = classifier.run(
        dataframe=dataframe,
        features=["Height"],
        detectors=["forward", "side"],
        random_state=123,
    )

    assert isinstance(classified, (pd.DataFrame, ClassifierDataFrame))
    assert "Label" in classified.columns

    labels = classified["Label"].dropna().to_numpy()
    assert labels.ndim == 1
    assert labels.size == number_of_samples * 2
    assert labels.min() >= 0
    assert labels.max() < number_of_clusters


def test_kmeans_reproducible_random_state():
    """
    Test that identical random_state gives identical labels.
    """
    random_generator = np.random.default_rng(1234)

    data_matrix = random_generator.random((100, 2))
    dataframe = make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )

    classifier = KmeansClassifier(4)

    classified_first = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
        random_state=123,
    )
    classified_second = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
        random_state=123,
    )

    labels_first = classified_first["Label"].dropna().to_numpy()
    labels_second = classified_second["Label"].dropna().to_numpy()

    assert np.array_equal(labels_first, labels_second)


def test_kmeans_different_random_states():
    """
    Test that different random_state values usually produce different labels.
    """
    random_generator = np.random.default_rng(5678)

    data_matrix = random_generator.random((100, 2))
    dataframe = make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )

    classifier = KmeansClassifier(3)

    classified_a = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
        random_state=1,
    )
    classified_b = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
        random_state=99,
    )

    labels_a = classified_a["Label"].dropna().to_numpy()
    labels_b = classified_b["Label"].dropna().to_numpy()

    assert not np.array_equal(labels_a, labels_b)


def test_kmeans_invalid_input_shape():
    """
    Test that a non DataFrame input raises an exception.
    """
    classifier = KmeansClassifier(2)

    with pytest.raises(Exception):
        classifier.run(
            dataframe=np.array([1.0, 2.0, 3.0]),
            features=["Height"],
            detectors=["forward", "side"],
        )


def test_kmeans_empty_matrix():
    """
    Test that an empty DataFrame raises an exception.
    """
    classifier = KmeansClassifier(2)

    empty_dataframe = make_wide_dataframe(
        data_matrix=np.empty((0, 2)),
        features=["Height"],
        detectors=["forward", "side"],
    )

    with pytest.raises(Exception):
        classifier.run(
            dataframe=empty_dataframe,
            features=["Height"],
            detectors=["forward", "side"],
        )


def test_dbscan_two_blobs_clustering():
    """
    DBScanClassifier should find two main clusters on a simple two blob dataset.
    """
    number_of_samples_per_blob = 80
    dataframe = make_two_blob_wide_dataframe(
        number_of_samples_per_blob=number_of_samples_per_blob,
        random_seed=123,
    )

    classifier = DBScanClassifier(epsilon=0.6, minimum_samples=5)
    classified = classifier.run(
        dataframe=dataframe,
        features=["Height"],
        detectors=["forward", "side"],
    )

    assert isinstance(classified, (pd.DataFrame, ClassifierDataFrame))
    assert "Label" in classified.columns

    event_labels = (
        classified["Label"].groupby(level=["SegmentID", "PeakID"]).first().to_numpy()
    )

    assert event_labels.shape == (2 * number_of_samples_per_blob,)

    unique_labels = np.unique(event_labels)
    cluster_labels = unique_labels[unique_labels != -1]
    assert cluster_labels.size == 2

    labels_blob_a = event_labels[:number_of_samples_per_blob]
    labels_blob_b = event_labels[number_of_samples_per_blob:]

    dominant_label_a = np.bincount(labels_blob_a[labels_blob_a != -1]).argmax()
    dominant_label_b = np.bincount(labels_blob_b[labels_blob_b != -1]).argmax()

    assert dominant_label_a != dominant_label_b

    fraction_a_in_dominant = np.mean(labels_blob_a == dominant_label_a)
    fraction_b_in_dominant = np.mean(labels_blob_b == dominant_label_b)

    assert fraction_a_in_dominant > 0.9
    assert fraction_b_in_dominant > 0.9


def test_dbscan_noise_points_detected():
    """
    Points that are isolated with too few neighbors should be labeled as noise.
    """
    random_generator = np.random.default_rng(42)

    cluster_forward = random_generator.normal(loc=0.0, scale=0.2, size=(50, 1))
    cluster_side = random_generator.normal(loc=0.1, scale=0.2, size=(50, 1))

    noise_forward = np.array([[5.0], [6.0], [7.0]])
    noise_side = np.array([[5.1], [6.1], [7.1]])

    cluster_points = np.hstack([cluster_forward, cluster_side])
    noise_points = np.hstack([noise_forward, noise_side])

    data_matrix = np.vstack([cluster_points, noise_points])

    dataframe = make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )

    classifier = DBScanClassifier(epsilon=0.4, minimum_samples=5)
    classified = classifier.run(
        dataframe=dataframe,
        features=["Height"],
        detectors=["forward", "side"],
    )

    event_labels = (
        classified["Label"].groupby(level=["SegmentID", "PeakID"]).first().to_numpy()
    )

    assert event_labels.shape == (53,)

    noise_labels = event_labels[-3:]
    assert np.all(noise_labels == -1)


def test_dbscan_repeated_run_is_deterministic():
    """
    DBScanClassifier should be deterministic for the same parameters and data.
    """
    random_generator = np.random.default_rng(77)

    data_matrix = random_generator.normal(loc=1.0, scale=0.5, size=(100, 2))
    dataframe = make_wide_dataframe(
        data_matrix=data_matrix,
        features=["Height"],
        detectors=["forward", "side"],
    )

    classifier = DBScanClassifier(epsilon=0.5, minimum_samples=4)

    classified_first = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
    )
    classified_second = classifier.run(
        dataframe=dataframe.copy(),
        features=["Height"],
        detectors=["forward", "side"],
    )

    labels_first = (
        classified_first["Label"]
        .groupby(level=["SegmentID", "PeakID"])
        .first()
        .to_numpy()
    )
    labels_second = (
        classified_second["Label"]
        .groupby(level=["SegmentID", "PeakID"])
        .first()
        .to_numpy()
    )

    assert np.array_equal(labels_first, labels_second)


def test_dbscan_invalid_input_shape_raises():
    """
    Non DataFrame input should raise an exception.
    """
    classifier = DBScanClassifier(epsilon=0.5, minimum_samples=5)

    with pytest.raises(Exception):
        classifier.run(
            dataframe=np.array([1.0, 2.0, 3.0]),
            features=["Height"],
            detectors=["forward", "side"],
        )


def test_dbscan_empty_matrix_raises():
    """
    Empty DataFrame input should raise an exception.
    """
    classifier = DBScanClassifier(epsilon=0.5, minimum_samples=5)

    empty_dataframe = make_wide_dataframe(
        data_matrix=np.empty((0, 2)),
        features=["Height"],
        detectors=["forward", "side"],
    )

    with pytest.raises(Exception):
        classifier.run(
            dataframe=empty_dataframe,
            features=["Height"],
            detectors=["forward", "side"],
        )


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
