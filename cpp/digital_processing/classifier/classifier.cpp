#include "classifier.h"


std::vector<int> KmeansClassifier::run(const std::vector<std::vector<double>> &data_matrix, unsigned int random_state) const
{
    const size_t number_of_samples = data_matrix.size();
    if (number_of_samples == 0)
        throw std::runtime_error("Input matrix has no samples");


    const size_t number_of_features = data_matrix[0].size();
    if (number_of_features == 0)
        throw std::runtime_error("Input matrix has no features");


    // KMeans model outputs
    std::vector<std::vector<double>> centroids(number_of_cluster, std::vector<double>(number_of_features));
    std::vector<int> labels(number_of_samples, 0);

    // Initialise centroids by sampling random points
    std::mt19937 generator(random_state);
    std::uniform_int_distribution<size_t> choose(0, number_of_samples - 1);

    for (size_t k = 0; k < number_of_cluster; k++)
        centroids[k] = data_matrix[choose(generator)];

    bool changed = true;
    size_t max_iterations = 300;
    size_t iteration = 0;

    while (changed && iteration < max_iterations) {
        changed = false;

        // Update labels
        for (size_t i = 0; i < number_of_samples; i++) {
            double best_distance = std::numeric_limits<double>::max();
            int best_cluster = 0;

            for (size_t k = 0; k < number_of_cluster; k++) {
                double distance = 0.0;
                for (size_t f = 0; f < number_of_features; f++) {
                    double diff = data_matrix[i][f] - centroids[k][f];
                    distance += diff * diff;
                }

                if (distance < best_distance) {
                    best_distance = distance;
                    best_cluster = static_cast<int>(k);
                }
            }

            if (labels[i] != best_cluster) {
                labels[i] = best_cluster;
                changed = true;
            }
        }

        // Recompute centroids
        std::vector<std::vector<double>> new_centroids(number_of_cluster, std::vector<double>(number_of_features, 0.0));
        std::vector<size_t> cluster_sizes(number_of_cluster, 0);

        for (size_t i = 0; i < number_of_samples; i++) {
            int c = labels[i];
            cluster_sizes[c] += 1;
            for (size_t f = 0; f < number_of_features; f++) {
                new_centroids[c][f] += data_matrix[i][f];
            }
        }

        for (size_t c = 0; c < number_of_cluster; c++) {
            if (cluster_sizes[c] == 0) // Rechoose centroid if empty cluster
                new_centroids[c] = data_matrix[choose(generator)];

            else
                for (size_t f = 0; f < number_of_features; f++)
                    new_centroids[c][f] /= static_cast<double>(cluster_sizes[c]);


        }

        centroids = new_centroids;
        iteration++;
    }

    return labels;
}


DbscanClassifier::DbscanClassifier(double epsilon, std::size_t minimum_samples)
    : epsilon(epsilon),
      epsilon_squared(epsilon * epsilon),
      minimum_samples(minimum_samples)
{
    if (epsilon <= 0.0) {
        throw std::runtime_error("epsilon must be positive");
    }
    if (minimum_samples == 0) {
        throw std::runtime_error("minimum_samples must be at least one");
    }
}

double DbscanClassifier::squared_euclidean_distance(const std::vector<double> &point_a, const std::vector<double> &point_b) const
{
    if (point_a.size() != point_b.size()) {
        throw std::runtime_error("Points must have the same dimension");
    }

    double value = 0.0;
    for (std::size_t i = 0; i < point_a.size(); i++) {
        double difference = point_a[i] - point_b[i];
        value += difference * difference;
    }
    return value;
}

std::vector<std::size_t> DbscanClassifier::region_query(const std::vector<std::vector<double>> &data_matrix, std::size_t index) const
{
    std::vector<std::size_t> neighbors;
    const std::vector<double> &point = data_matrix[index];

    for (std::size_t j = 0; j < data_matrix.size(); j++) {
        double distance_squared = squared_euclidean_distance(point, data_matrix[j]);
        if (distance_squared <= epsilon_squared) {
            neighbors.push_back(j);
        }
    }
    return neighbors;
}

void DbscanClassifier::expand_cluster(
    const std::vector<std::vector<double>> &data_matrix,
    std::size_t point_index,
    std::vector<std::size_t> &neighbor_indices,
    int cluster_id,
    std::vector<int> &labels,
    std::vector<bool> &visited
) const {
    labels[point_index] = cluster_id;

    for (std::size_t i = 0; i < neighbor_indices.size(); i++) {
        std::size_t neighbor_index = neighbor_indices[i];

        if (!visited[neighbor_index]) {
            visited[neighbor_index] = true;
            std::vector<std::size_t> neighbor_neighbors =
                region_query(data_matrix, neighbor_index);

            if (neighbor_neighbors.size() >= minimum_samples) {
                neighbor_indices.insert(
                    neighbor_indices.end(),
                    neighbor_neighbors.begin(),
                    neighbor_neighbors.end()
                );
            }
        }

        if (labels[neighbor_index] == -1) {
            labels[neighbor_index] = cluster_id;
        }
    }
}

std::vector<int> DbscanClassifier::run(const std::vector<std::vector<double>> &data_matrix) const
{
    std::size_t number_of_samples = data_matrix.size();
    if (number_of_samples == 0) {
        throw std::runtime_error("Input matrix has no samples");
    }

    std::size_t number_of_features = data_matrix[0].size();
    if (number_of_features == 0) {
        throw std::runtime_error("Input matrix has no features");
    }

    for (const auto &row : data_matrix) {
        if (row.size() != number_of_features) {
            throw std::runtime_error("All rows must have the same number of features");
        }
    }

    std::vector<int> labels(number_of_samples, -1); // -1 means noise
    std::vector<bool> visited(number_of_samples, false);

    int current_cluster_id = 0;

    for (std::size_t i = 0; i < number_of_samples; i++) {
        if (visited[i]) {
            continue;
        }

        visited[i] = true;
        std::vector<std::size_t> neighbor_indices = region_query(data_matrix, i);

        if (neighbor_indices.size() < minimum_samples) {
            labels[i] = -1;
        } else {
            expand_cluster(
                data_matrix,
                i,
                neighbor_indices,
                current_cluster_id,
                labels,
                visited
            );
            current_cluster_id += 1;
        }
    }

    return labels;
}
