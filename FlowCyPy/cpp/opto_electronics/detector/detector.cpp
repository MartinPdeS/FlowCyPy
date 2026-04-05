#include "detector.h"

#include <random>
#include <sstream>
#include <cstdint>

#include <utils/constants.h>


Detector::Detector(
    const double phi_angle,
    const double numerical_aperture,
    const double cache_numerical_aperture,
    const double gamma_angle,
    const int sampling,
    const double responsivity,
    const double dark_current,
    const double bandwidth,
    const std::string& name
)
    : phi_angle(phi_angle),
      numerical_aperture(numerical_aperture),
      cache_numerical_aperture(cache_numerical_aperture),
      gamma_angle(gamma_angle),
      sampling(sampling),
      responsivity(responsivity),
      dark_current(dark_current),
      bandwidth(bandwidth),
      name(name)
{
    if (std::isnan(this->phi_angle)) {
        throw std::invalid_argument("Detector phi_angle must be defined.");
    }

    if (std::isnan(this->gamma_angle)) {
        throw std::invalid_argument("Detector gamma_angle must be defined.");
    }

    if (std::isnan(this->numerical_aperture) || this->numerical_aperture < 0.0) {
        throw std::invalid_argument("Detector numerical_aperture must be non negative.");
    }

    if (
        std::isnan(this->cache_numerical_aperture) ||
        this->cache_numerical_aperture < 0.0
    ) {
        throw std::invalid_argument(
            "Detector cache_numerical_aperture must be non negative."
        );
    }

    if (this->sampling <= 0) {
        throw std::invalid_argument("Detector sampling must be strictly positive.");
    }

    if (std::isnan(this->responsivity) || this->responsivity < 0.0) {
        throw std::invalid_argument("Detector responsivity must be non negative.");
    }

    if (std::isnan(this->dark_current) || this->dark_current < 0.0) {
        throw std::invalid_argument("Detector dark_current must be non negative.");
    }

    if (!std::isnan(this->bandwidth) && this->bandwidth <= 0.0) {
        throw std::invalid_argument(
            "Detector bandwidth must be strictly positive when provided."
        );
    }

    if (this->name.empty()) {
        this->name = std::to_string(
            reinterpret_cast<std::uintptr_t>(this)
        );
    }
}


bool Detector::has_bandwidth() const {
    return !std::isnan(this->bandwidth);
}


void Detector::clear_bandwidth() {
    this->bandwidth = std::numeric_limits<double>::quiet_NaN();
}


bool Detector::bandwidth_is_defined(const double bandwidth) const {
    return !std::isnan(bandwidth);
}


double Detector::resolve_bandwidth(
    const double bandwidth
) const {
    if (!std::isnan(bandwidth)) {
        if (bandwidth <= 0.0) {
            throw std::invalid_argument(
                "Detector method bandwidth must be strictly positive when provided."
            );
        }

        return bandwidth;
    }

    return this->bandwidth;
}


std::vector<double> Detector::apply_dark_current_noise(
    const std::vector<double>& signal,
    const double bandwidth
) const {
    const double effective_bandwidth = this->resolve_bandwidth(bandwidth);

    if (!this->bandwidth_is_defined(effective_bandwidth)) {
        return signal;
    }

    if (signal.empty()) {
        throw std::invalid_argument("Signal array is empty.");
    }

    const double standard_deviation_noise = std::sqrt(
        2.0 *
        Constants::e *
        this->dark_current *
        effective_bandwidth
    );

    std::random_device random_device;
    std::mt19937_64 random_number_generator(random_device());
    std::normal_distribution<double> normal_distribution(
        this->dark_current,
        standard_deviation_noise
    );

    std::vector<double> noisy_signal(signal.size());

    for (size_t index = 0; index < signal.size(); ++index) {
        noisy_signal[index] = signal[index] + normal_distribution(random_number_generator);
    }

    return noisy_signal;
}


double Detector::get_optical_power_to_photon_factor(
    const double wavelength,
    const double bandwidth
) const {
    if (std::isnan(wavelength) || wavelength <= 0.0) {
        throw std::invalid_argument("Detector wavelength must be strictly positive.");
    }

    if (std::isnan(bandwidth) || bandwidth <= 0.0) {
        throw std::invalid_argument("Detector bandwidth must be strictly positive.");
    }

    const double energy_per_photon = Constants::plank * Constants::light_speed / wavelength;
    const double sampling_interval = 1.0 / (bandwidth * 2.0);

    return sampling_interval / energy_per_photon;
}


std::string Detector::repr() const {
    return
        "Detector("
        "name='" + this->name + "'" +
        ", phi_angle=" + std::to_string(this->phi_angle) + "rad" +
        ", numerical_aperture=" + std::to_string(this->numerical_aperture) +
        ", cache_numerical_aperture=" + std::to_string(this->cache_numerical_aperture) +
        ", gamma_angle=" + std::to_string(this->gamma_angle) + "rad" +
        ", sampling=" + std::to_string(this->sampling) +
        ", responsivity=" + std::to_string(this->responsivity) + "A/W" +
        ", dark_current=" + std::to_string(this->dark_current) + "A" +
        ", bandwidth=" + (
            std::isnan(this->bandwidth) ? std::string("None") : std::to_string(this->bandwidth)
        ) + "Hz"
        ")";
}
