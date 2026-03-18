#include <random>
#include "distributions.h"
#include "detail.h"


// __________ NORMAL _____________
// ________________________________
Normal::Normal(
    const double mean,
    const double standard_deviation,
    const double low_cutoff,
    const double high_cutoff
)
: mean(mean),
  standard_deviation(standard_deviation),
  low_cutoff(low_cutoff),
  high_cutoff(high_cutoff),
  generator(std::random_device{}())
{
    if (!(this->standard_deviation > 0.0)) {
        throw std::invalid_argument("standard_deviation must be > 0");
    }
    if (!(this->low_cutoff <= this->high_cutoff)) {
        throw std::invalid_argument("low_cutoff must be <= high_cutoff");
    }
}

std::vector<double> Normal::sample(const std::size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    if (n_samples == 0) {
        return output;
    }

    const double a = (low_cutoff - mean) / standard_deviation;
    const double b = (high_cutoff - mean) / standard_deviation;

    double Fa = detail::normal_cdf(a);
    double Fb = detail::normal_cdf(b);

    Fa = detail::clamp_open01(Fa);
    Fb = detail::clamp_open01(Fb);

    if (Fb < Fa) {
        std::swap(Fa, Fb);
    }

    const double span = Fb - Fa;

    // If the interval is extremely tiny, sampling degenerates numerically
    // In that case, return the closest bound (still within the truncation)
    const double eps = 64.0 * std::numeric_limits<double>::epsilon();
    if (!(span > eps)) {
        const double clamped_value = std::clamp(mean, low_cutoff, high_cutoff);
        output.assign(n_samples, clamped_value);
        return output;
    }

    std::uniform_real_distribution<double> uniform(Fa, Fb);

    for (std::size_t i = 0; i < n_samples; ++i) {
        const double u = uniform(generator);
        const double z = detail::normal_inv_cdf(u);
        const double x = mean + standard_deviation * z;

        // Numerically, x can be off by a few ulps near the bounds, clamp it safely.
        output.push_back(std::clamp(x, low_cutoff, high_cutoff));
    }

    return output;
}

// Normal.cpp

double Normal::proportion_within_cutoffs() const {
    const double a = (low_cutoff  - mean) / standard_deviation;
    const double b = (high_cutoff - mean) / standard_deviation;

    double Fa = detail::normal_cdf(a);
    double Fb = detail::normal_cdf(b);

    // Numerical safety
    Fa = detail::clamp_open01(Fa);
    Fb = detail::clamp_open01(Fb);

    if (Fb < Fa) {
        std::swap(Fa, Fb);
    }

    return Fb - Fa;
}

// __________ UNIFORM _____________
// ________________________________
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

double Uniform::proportion_within_cutoffs() const { return 1.0; }


// __________ ROSIN-RAMMLER _____________
// ______________________________________
std::vector<double>
RosinRammler::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    if (n_samples == 0) {
        return output;
    }

    if (!(scale > 0.0)) {
        throw std::invalid_argument("scale must be > 0");
    }
    if (!(shape > 0.0)) {
        throw std::invalid_argument("shape must be > 0");
    }
    if (!(low_cutoff <= high_cutoff)) {
        throw std::invalid_argument("low_cutoff must be <= high_cutoff");
    }

    // Support is x >= 0
    const double effective_low = std::max(low_cutoff, 0.0);
    const double effective_high = std::max(high_cutoff, 0.0);

    double F_low = detail::rosin_rammler_cdf(effective_low, scale, shape);
    double F_high = detail::rosin_rammler_cdf(effective_high, scale, shape);

    F_low = detail::clamp_open01(F_low);
    F_high = detail::clamp_open01(F_high);

    if (F_high < F_low) {
        std::swap(F_low, F_high);
    }

    const double span = F_high - F_low;
    const double eps = 64.0 * std::numeric_limits<double>::epsilon();

    if (!(span > eps)) {
        const double clamped_value = std::clamp(scale, low_cutoff, high_cutoff);
        output.assign(n_samples, clamped_value);
        return output;
    }

    std::uniform_real_distribution<double> uniform(F_low, F_high);

    for (size_t i = 0; i < n_samples; ++i) {
        const double p = uniform(generator);
        const double x = detail::rosin_rammler_inv_cdf(p, scale, shape);
        output.push_back(std::clamp(x, low_cutoff, high_cutoff));
    }

    return output;
}

double RosinRammler::proportion_within_cutoffs() const {
    if (!(scale > 0.0) || !(shape > 0.0)) {
        return 0.0;
    }
    if (!(low_cutoff <= high_cutoff)) {
        return 0.0;
    }

    const double effective_low = std::max(low_cutoff, 0.0);
    const double effective_high = std::max(high_cutoff, 0.0);

    const double F_low = detail::rosin_rammler_cdf(effective_low, scale, shape);
    const double F_high = detail::rosin_rammler_cdf(effective_high, scale, shape);

    return std::max(0.0, F_high - F_low);
}

// __________ LOG-NORMAL _____________
// ___________________________________
std::vector<double>
LogNormal::sample(const size_t n_samples) const {
    std::vector<double> output;
    output.reserve(n_samples);

    if (n_samples == 0) {
        return output;
    }

    if (!(standard_deviation > 0.0)) {
        throw std::invalid_argument("standard_deviation must be > 0");
    }

    if (!(low_cutoff > 0.0)) {
        throw std::invalid_argument("LogNormal requires low_cutoff > 0");
    }

    if (!(low_cutoff <= high_cutoff)) {
        throw std::invalid_argument("low_cutoff must be <= high_cutoff");
    }

    // Transform cutoffs into log space
    const double log_low  = std::log(low_cutoff);
    const double log_high = std::log(high_cutoff);

    const double a = (log_low  - mean) / standard_deviation;
    const double b = (log_high - mean) / standard_deviation;

    double Fa = detail::normal_cdf(a);
    double Fb = detail::normal_cdf(b);

    Fa = detail::clamp_open01(Fa);
    Fb = detail::clamp_open01(Fb);

    if (Fb < Fa) {
        std::swap(Fa, Fb);
    }

    const double span = Fb - Fa;
    const double eps = 64.0 * std::numeric_limits<double>::epsilon();

    // Degenerate truncation case
    if (!(span > eps)) {
        const double clamped =
            std::clamp(std::exp(mean), low_cutoff, high_cutoff);
        output.assign(n_samples, clamped);
        return output;
    }

    std::uniform_real_distribution<double> uniform(Fa, Fb);

    for (size_t i = 0; i < n_samples; ++i) {
        const double u = uniform(generator);
        const double z = detail::normal_inv_cdf(u);
        const double y = mean + standard_deviation * z;
        const double x = std::exp(y);

        // Numerical safety near bounds
        output.push_back(std::clamp(x, low_cutoff, high_cutoff));
    }

    return output;
}

double LogNormal::proportion_within_cutoffs() const {
    if (!(low_cutoff > 0.0)) {
        return 0.0;
    }

    const double log_low  = std::log(low_cutoff);
    const double log_high = std::log(high_cutoff);

    const double a = (log_low  - mean) / standard_deviation;
    const double b = (log_high - mean) / standard_deviation;

    double Fa = detail::normal_cdf(a);
    double Fb = detail::normal_cdf(b);

    Fa = detail::clamp_open01(Fa);
    Fb = detail::clamp_open01(Fb);

    if (Fb < Fa) {
        std::swap(Fa, Fb);
    }

    return Fb - Fa;
}

// __________ DELTA _____________
// ______________________________
std::vector<double>
Delta::sample(const size_t n_samples) const {
    std::vector<double> output(n_samples, this->value);
    return output;
}

double Delta::proportion_within_cutoffs() const { return 1.0; }
