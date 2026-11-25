#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace detail {

// Standard normal CDF Phi(x)
inline double normal_cdf(double x) {
    // Phi(x) = 0.5 * erfc(-x / sqrt(2))
    return 0.5 * std::erfc(-x * M_SQRT1_2);
}

// Inverse standard normal CDF, Acklam rational approximation
// Valid for 0 < p < 1
inline double normal_inv_cdf(double p) {
    const double a1 = -3.969683028665376e+01;
    const double a2 =  2.209460984245205e+02;
    const double a3 = -2.759285104469687e+02;
    const double a4 =  1.383577518672690e+02;
    const double a5 = -3.066479806614716e+01;
    const double a6 =  2.506628277459239e+00;

    const double b1 = -5.447609879822406e+01;
    const double b2 =  1.615858368580409e+02;
    const double b3 = -1.556989798598866e+02;
    const double b4 =  6.680131188771972e+01;
    const double b5 = -1.328068155288572e+01;

    const double c1 = -7.784894002430293e-03;
    const double c2 = -3.223964580411365e-01;
    const double c3 = -2.400758277161838e+00;
    const double c4 = -2.549732539343734e+00;
    const double c5 =  4.374664141464968e+00;
    const double c6 =  2.938163982698783e+00;

    const double d1 =  7.784695709041462e-03;
    const double d2 =  3.224671290700398e-01;
    const double d3 =  2.445134137142996e+00;
    const double d4 =  3.754408661907416e+00;

    const double tiny = std::numeric_limits<double>::min();
    p = std::clamp(p, tiny, 1.0 - tiny);

    const double plow = 0.02425;
    const double phigh = 1.0 - plow;

    double q = 0.0;
    double r = 0.0;

    if (p < plow) {
        q = std::sqrt(-2.0 * std::log(p));
        return (((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
               ((((d1*q + d2)*q + d3)*q + d4)*q + 1.0);
    }

    if (p > phigh) {
        q = std::sqrt(-2.0 * std::log(1.0 - p));
        return -(((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
                 ((((d1*q + d2)*q + d3)*q + d4)*q + 1.0);
    }

    q = p - 0.5;
    r = q * q;

    return (((((a1*r + a2)*r + a3)*r + a4)*r + a5)*r + a6) * q /
           (((((b1*r + b2)*r + b3)*r + b4)*r + b5)*r + 1.0);
}

inline double clamp_open01(double p) {
    const double tiny = std::numeric_limits<double>::min();
    return std::clamp(p, tiny, 1.0 - tiny);
}

inline double rosin_rammler_cdf(const double x, const double scale, const double shape) {
    if (x <= 0.0) {
        return 0.0;
    }
    const double t = std::pow(x / scale, shape);
    return 1.0 - std::exp(-t);
}

inline double rosin_rammler_inv_cdf(const double p, const double scale, const double shape) {
    const double pp = clamp_open01(p);
    return scale * std::pow(-std::log(1.0 - pp), 1.0 / shape);
}

} // namespace detail
