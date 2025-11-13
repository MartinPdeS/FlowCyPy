import numpy as np
import pytest
from FlowCyPy.binary.classifier import KMEANSCLASSIFIER, DBSCANCLASSIFIER


def test_kmeans_basic_clustering():
    """
    Test that KmeansClassifier returns a label for each sample.
    """
    number_of_cluster = 3
    number_of_samples = 50
    number_of_features = 4

    data_matrix = np.random.rand(number_of_samples, number_of_features)

    classifier = KMEANSCLASSIFIER(number_of_cluster)
    labels = classifier._cpp_run(data_matrix)

    labels = np.asarray(labels)

    assert labels.shape == (number_of_samples,)
    assert labels.dtype == int
    assert labels.min() >= 0
    assert labels.max() < number_of_cluster


def test_kmeans_reproducible_random_state():
    """
    Test that identical random_state gives identical results.
    """
    data_matrix = np.random.rand(100, 3)
    classifier = KMEANSCLASSIFIER(4)

    labels_first = classifier._cpp_run(data_matrix, random_state=123)
    labels_second = classifier._cpp_run(data_matrix, random_state=123)

    assert np.array_equal(labels_first, labels_second)


def test_kmeans_different_random_states():
    """
    Test that different random_state values produce different results.
    """
    data_matrix = np.random.rand(100, 3)
    classifier = KMEANSCLASSIFIER(3)

    labels_a = classifier._cpp_run(data_matrix, random_state=1)
    labels_b = classifier._cpp_run(data_matrix, random_state=99)

    # You do not want this to be a strict guarantee but it should hold for almost all calls
    assert not np.array_equal(labels_a, labels_b)


def test_kmeans_invalid_input_shape():
    """
    Test that a one dimensional input raises an exception.
    """
    classifier = KMEANSCLASSIFIER(2)

    with pytest.raises(Exception):
        classifier._cpp_run(np.array([1.0, 2.0, 3.0]))


def test_kmeans_empty_matrix():
    """
    Test that an empty array raises an exception.
    """
    classifier = KMEANSCLASSIFIER(2)

    empty_matrix = np.array([]).reshape(0, 3)

    with pytest.raises(Exception):
        classifier._cpp_run(empty_matrix)


def test_dbscan_two_blobs_clustering():
    """
    DBSCANCLASSIFIER should find two main clusters on a simple two blob dataset.
    """
    random_generator = np.random.default_rng(123)

    number_of_samples_per_blob = 80

    blob_a = random_generator.normal(
        loc=0.0, scale=0.25, size=(number_of_samples_per_blob, 2)
    )
    blob_b = random_generator.normal(
        loc=3.0, scale=0.25, size=(number_of_samples_per_blob, 2)
    )

    data_matrix = np.vstack([blob_a, blob_b])

    classifier = DBSCANCLASSIFIER(epsilon=0.6, minimum_samples=5)
    labels = classifier._cpp_run(data_matrix)

    assert isinstance(labels, np.ndarray)
    assert labels.shape == (2 * number_of_samples_per_blob,)

    unique_labels = np.unique(labels)
    # There should be at most one noise label equal to minus one
    # and two actual cluster labels
    cluster_labels = unique_labels[unique_labels != -1]
    assert cluster_labels.size == 2

    # Check that most points in each blob share a dominant label
    labels_blob_a = labels[:number_of_samples_per_blob]
    labels_blob_b = labels[number_of_samples_per_blob:]

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

    cluster_points = random_generator.normal(loc=0.0, scale=0.2, size=(50, 2))
    noise_points = np.array(
        [
            [5.0, 5.0],
            [6.0, 6.0],
            [7.0, 7.0],
        ]
    )

    data_matrix = np.vstack([cluster_points, noise_points])

    classifier = DBSCANCLASSIFIER(epsilon=0.4, minimum_samples=5)
    labels = classifier._cpp_run(data_matrix)

    assert labels.shape == (53,)

    noise_labels = labels[-len(noise_points) :]
    assert np.all(noise_labels == -1)


def test_dbscan_repeated_run_is_deterministic():
    """
    DBSCANCLASSIFIER should be deterministic for the same parameters and data.
    """
    random_generator = np.random.default_rng(77)

    data_matrix = random_generator.normal(loc=1.0, scale=0.5, size=(100, 3))

    classifier = DBSCANCLASSIFIER(epsilon=0.5, minimum_samples=4)
    labels_first = classifier._cpp_run(data_matrix)
    labels_second = classifier._cpp_run(data_matrix)

    assert np.array_equal(labels_first, labels_second)


def test_dbscan_invalid_input_shape_raises():
    """
    One dimensional input array should raise an exception.
    """
    classifier = DBSCANCLASSIFIER(epsilon=0.5, minimum_samples=5)

    one_dimensional_array = np.array([1.0, 2.0, 3.0])

    with pytest.raises(Exception):
        classifier._cpp_run(one_dimensional_array)


def test_dbscan_empty_matrix_raises():
    """
    Empty input matrix should raise an exception.
    """
    classifier = DBSCANCLASSIFIER(epsilon=0.5, minimum_samples=5)

    empty_matrix = np.empty((0, 2))

    with pytest.raises(Exception):
        classifier._cpp_run(empty_matrix)


if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
