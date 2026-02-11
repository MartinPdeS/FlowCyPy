#pragma once

#include <vector>

class BaseDistribution {
    public:
        std::string units;
        virtual ~BaseDistribution(){};
        virtual std::vector<double> sample(const size_t n_samples) const = 0;
};


class Normal : public BaseDistribution {
    public:
        double mean;
        double standard_deviation;
        double low_cutoff;
        double high_cutoff;
        bool strict_sampling;

        Normal(
            const double mean,
            const double standard_deviation,
            const double low_cutoff = std::numeric_limits<double>::lowest(),
            const double high_cutoff = std::numeric_limits<double>::infinity(),
            const bool strict_sampling = false
        )
        :   mean(mean),
            standard_deviation(standard_deviation),
            low_cutoff(low_cutoff),
            high_cutoff(high_cutoff),
            strict_sampling(strict_sampling)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
};

class Uniform : public BaseDistribution {
    public:
        double lower_bound;
        double upper_bound;

        Uniform(const double lower_bound, const double upper_bound)
        : lower_bound(lower_bound), upper_bound(upper_bound)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
};

class RosinRammler : public BaseDistribution {
    public:
        double scale;
        double shape;
        double low_cutoff;
        double high_cutoff;
        bool strict_sampling;

        RosinRammler(
            const double scale,
            const double shape,
            const double low_cutoff = std::numeric_limits<double>::lowest(),
            const double high_cutoff = std::numeric_limits<double>::infinity(),
            const bool strict_sampling = false
        )
        :   scale(scale),
            shape(shape),
            low_cutoff(low_cutoff),
            high_cutoff(high_cutoff),
            strict_sampling(strict_sampling)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
};

class LogNormal : public BaseDistribution {
    public:
        double mean;
        double standard_deviation;
        double low_cutoff;
        double high_cutoff;
        bool strict_sampling;

        LogNormal(
            const double mean,
            const double standard_deviation,
            const double low_cutoff = std::numeric_limits<double>::lowest(),
            const double high_cutoff = std::numeric_limits<double>::infinity(),
            const bool strict_sampling = false
        )
        :   mean(mean),
            standard_deviation(standard_deviation),
            low_cutoff(low_cutoff),
            high_cutoff(high_cutoff),
            strict_sampling(strict_sampling)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
};


class Delta : public BaseDistribution {
    public:
        double value;

        Delta(const double value)
        : value(value)
        {}

        std::vector<double> sample(const size_t n_samples) const override;
};
