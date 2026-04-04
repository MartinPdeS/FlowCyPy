#pragma once

#include <string>
#include <vector>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <optional>


class Detector {
public:
    double phi_angle;
    double numerical_aperture;

    double cache_numerical_aperture;
    double gamma_angle;
    int sampling;
    double responsivity;
    double dark_current;
    double bandwidth;
    std::string name;

    Detector(
        const double phi_angle,
        const double numerical_aperture,
        const double cache_numerical_aperture = 0.0,
        const double gamma_angle = 0.0,
        const int sampling = 200,
        const double responsivity = 1.0,
        const double dark_current = 0.0,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        const std::string& name = ""
    );

    bool has_bandwidth() const;
    void clear_bandwidth();

    std::vector<double> apply_dark_current_noise(
        const std::vector<double>& signal,
        const double bandwidth = std::numeric_limits<double>::quiet_NaN()
    ) const;

    std::string repr() const;

private:
    double resolve_bandwidth(
        const double bandwidth
    ) const;

    bool bandwidth_is_defined(
        const double bandwidth
    ) const;

    double get_optical_power_to_photon_factor(
        const double wavelength,
        const double bandwidth
    ) const;
};
