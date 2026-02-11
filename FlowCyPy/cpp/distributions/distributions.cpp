#include <random>
#include "distributions.h"


std::vector<double>
Normal::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<> dist(this->mean, this->standard_deviation);

    size_t sample_number = 0;
    while (sample_number < n_samples) {
        double sample = dist(gen);

        if (sample >= this->low_cutoff && sample <= this->high_cutoff) {
            output.push_back(sample);
            sample_number++;
        } else {
            if (this->strict_sampling == false)
                sample_number++;
        }
    }

    return output;
}

std::vector<double>
Uniform::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dist(this->lower_bound, this->upper_bound);

    for (size_t i = 0; i < n_samples; ++i) {
        output.push_back(dist(gen));
    }

    return output;
}

std::vector<double>
RosinRammler::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dist(0.0, 1.0);

    size_t sample_number = 0;
    while (sample_number < n_samples) {
        double u = dist(gen);
        double sample = this->scale * std::pow(-std::log(1 - u), 1 / this->shape);

        if (sample >= this->low_cutoff && sample <= this->high_cutoff) {
            output.push_back(sample);
            sample_number++;
        } else {
            if (this->strict_sampling == false)
                sample_number++;
        }
    }

    return output;
}


std::vector<double>
LogNormal::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::lognormal_distribution<> dist(this->mean, this->standard_deviation);

    size_t sample_number = 0;
    while (sample_number < n_samples) {
        double sample = dist(gen);

        if (sample >= this->low_cutoff && sample <= this->high_cutoff) {
            output.push_back(sample);
            sample_number++;
        } else {
            if (this->strict_sampling == false)
                sample_number++;
        }
    }

    return output;
}

std::vector<double>
Delta::sample(const size_t n_samples) const {
    std::vector<double> output(n_samples, this->value);
    return output;
}
