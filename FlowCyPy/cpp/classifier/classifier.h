#pragma once
#include <vector>
#include <random>
#include <limits>
#include <cmath>
#include <cstddef>

class KmeansClassifier {
public:
    explicit KmeansClassifier(size_t number_of_cluster) : number_of_cluster(number_of_cluster) {}

    std::vector<int> run(const std::vector<std::vector<double>> &data_matrix, unsigned int random_state = 42) const;


private:
    size_t number_of_cluster;
};


class DbscanClassifier {
public:
    DbscanClassifier(double epsilon, std::size_t minimum_samples);

    std::vector<int> run(const std::vector<std::vector<double>> &data_matrix) const;

private:
    double epsilon;
    double epsilon_squared;
    std::size_t minimum_samples;

    double squared_euclidean_distance(const std::vector<double> &point_a, const std::vector<double> &point_b) const;

    std::vector<std::size_t> region_query(const std::vector<std::vector<double>> &data_matrix, std::size_t index) const;

    void expand_cluster(
        const std::vector<std::vector<double>> &data_matrix,
        std::size_t point_index,
        std::vector<std::size_t> &neighbor_indices,
        int cluster_id,
        std::vector<int> &labels,
        std::vector<bool> &visited
    ) const;
};
