#pragma once

#include <vector>
#include <random>
#include <limits>

class BaseDistribution {
    public:
        std::string units;

        virtual ~BaseDistribution(){};
        virtual std::vector<double> sample(const size_t n_samples) const = 0;
        virtual double proportion_within_cutoffs() const = 0;

};


class Normal : public BaseDistribution {
public:
    double mean = 0.0;
    double standard_deviation = 1.0;
    double low_cutoff = -1.0;
    double high_cutoff = 1.0;
    mutable std::mt19937 generator;


    Normal(
        double mean,
        double standard_deviation,
        double low_cutoff,
        double high_cutoff
    );

    std::vector<double> sample(const size_t n_samples) const override;
    double proportion_within_cutoffs() const override;

};


class Uniform : public BaseDistribution {
    public:
        double lower_bound;
        double upper_bound;
        mutable std::mt19937 generator;

        Uniform(const double lower_bound, const double upper_bound)
        : lower_bound(lower_bound), upper_bound(upper_bound)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
        double proportion_within_cutoffs() const override;

    };

class RosinRammler : public BaseDistribution {
    public:
        double scale;
        double shape;
        double low_cutoff;
        double high_cutoff;
        mutable std::mt19937 generator;

        RosinRammler(
            const double scale,
            const double shape,
            const double low_cutoff = std::numeric_limits<double>::lowest(),
            const double high_cutoff = std::numeric_limits<double>::infinity()
        )
        :   scale(scale),
            shape(shape),
            low_cutoff(low_cutoff),
            high_cutoff(high_cutoff)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
        double proportion_within_cutoffs() const override;
};

class LogNormal : public BaseDistribution {
    public:
        double mean;
        double standard_deviation;
        double low_cutoff;
        double high_cutoff;
        mutable std::mt19937 generator;

        LogNormal(
            const double mean,
            const double standard_deviation,
            const double low_cutoff = std::numeric_limits<double>::lowest(),
            const double high_cutoff = std::numeric_limits<double>::infinity()
        )
        :   mean(mean),
            standard_deviation(standard_deviation),
            low_cutoff(low_cutoff),
            high_cutoff(high_cutoff)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
        double proportion_within_cutoffs() const override;

};


class Delta : public BaseDistribution {
    public:
        double value;
        mutable std::mt19937 generator;

        Delta(const double value)
        : value(value)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
        double proportion_within_cutoffs() const override;

};
