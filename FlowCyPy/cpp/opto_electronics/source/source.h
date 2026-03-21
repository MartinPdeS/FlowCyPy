#pragma once

#include <vector>
#include <random>
#include <cmath>
#include <stdexcept>
#include <algorithm>

#include <utils/constants.h>


class BaseSource {
public:
    double wavelength;      // [meter]
    double rin;             // [dB / hertz]
    double optical_power;   // [watt]
    double amplitude;       // [volt / meter]
    double polarization;    // [radian]

    virtual ~BaseSource() = default;

    BaseSource(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double polarization
    )
        : wavelength(wavelength),
          rin(rin),
          optical_power(optical_power),
          amplitude(0.0),
          polarization(polarization)
    {
        if (this->wavelength <= 0.0) {
            throw std::runtime_error("wavelength must be strictly positive.");
        }

        if (this->optical_power < 0.0) {
            throw std::runtime_error("optical_power must be non negative.");
        }
    }

    double get_frequency() const {
        return Constants::light_speed / this->wavelength;
    }

    double get_photon_energy() const {
        return Constants::plank * this->get_frequency();
    }

    double get_rin_linear() const {
        return std::pow(10.0, this->rin / 10.0);
    }

    void add_rin_to_signal(std::vector<double>& amplitudes, const double bandwidth) const {
        if (bandwidth < 0.0) {
            throw std::runtime_error("bandwidth must be non negative.");
        }

        static thread_local std::random_device random_device;
        static thread_local std::mt19937 generator(random_device());

        const double rin_linear = this->get_rin_linear();

        for (size_t index = 0; index < amplitudes.size(); ++index) {
            const double signal_amplitude = amplitudes[index];
            const double standard_deviation = std::sqrt(rin_linear * bandwidth) * signal_amplitude;

            std::normal_distribution<double> distribution(0.0, standard_deviation);

            amplitudes[index] += distribution(generator);
        }
    }

    std::vector<double> get_amplitude_signal(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z,
        const double bandwidth,
        const bool include_source_noise = true
    ) const {
        if (x.size() != y.size() || x.size() != z.size()) {
            throw std::runtime_error("x, y, and z must have the same size.");
        }

        std::vector<double> amplitudes(x.size());

        for (size_t index = 0; index < x.size(); ++index) {
            amplitudes[index] = this->get_amplitude_at(
                x[index],
                y[index],
                z[index]
            );
        }

        if (include_source_noise) {
            this->add_rin_to_signal(amplitudes, bandwidth);
        }

        return amplitudes;
    }

    virtual double get_particle_width(const double velocity) const = 0;

    virtual double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const = 0;

protected:
    virtual double get_amplitude_at_focus() const = 0;

    void update_amplitude() {
        this->amplitude = this->get_amplitude_at_focus();
    }
};


class Gaussian : public BaseSource {
public:
    double waist;   // [meter]

    Gaussian(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist,
        const double polarization
    )
        : BaseSource(wavelength, rin, optical_power, polarization),
          waist(waist)
    {
        if (this->waist <= 0.0) {
            throw std::runtime_error("waist must be strictly positive.");
        }

        this->update_amplitude();
    }

    void set_waist(const double waist) {
        if (waist <= 0.0) {
            throw std::runtime_error("waist must be strictly positive.");
        }

        this->waist = waist;
        this->update_amplitude();
    }

    double get_particle_width(const double velocity) const override {
        if (velocity <= 0.0) {
            throw std::runtime_error("velocity must be strictly positive.");
        }

        return this->waist / (2.0 * velocity);
    }

    double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const override {
        (void)x;

        return this->amplitude * std::exp(
            -(y * y) / (this->waist * this->waist)
            - (z * z) / (this->waist * this->waist)
        );
    }

protected:
    double get_amplitude_at_focus() const override {
        const double area = this->waist * this->waist;

        return std::sqrt(
            4.0 * this->optical_power /
            (
                Constants::pi *
                Constants::vacuum_permitivity *
                Constants::light_speed *
                area
            )
        );
    }
};


class AsymetricGaussian : public BaseSource {
public:
    double waist_y;   // [meter]
    double waist_z;   // [meter]

    AsymetricGaussian(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist_y,
        const double waist_z,
        const double polarization
    )
        : BaseSource(wavelength, rin, optical_power, polarization),
          waist_y(waist_y),
          waist_z(waist_z)
    {
        if (this->waist_y <= 0.0) {
            throw std::runtime_error("waist_y must be strictly positive.");
        }

        if (this->waist_z <= 0.0) {
            throw std::runtime_error("waist_z must be strictly positive.");
        }

        this->update_amplitude();
    }

    void set_waist(const double waist_y, const double waist_z) {
        if (waist_y <= 0.0) {
            throw std::runtime_error("waist_y must be strictly positive.");
        }

        if (waist_z <= 0.0) {
            throw std::runtime_error("waist_z must be strictly positive.");
        }

        this->waist_y = waist_y;
        this->waist_z = waist_z;
        this->update_amplitude();
    }

    double get_particle_width(const double velocity) const override {
        if (velocity <= 0.0) {
            throw std::runtime_error("velocity must be strictly positive.");
        }

        return this->waist_z / (2.0 * velocity);
    }

    double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const override {
        (void)x;

        return this->amplitude * std::exp(
            -(y * y) / (this->waist_y * this->waist_y)
            - (z * z) / (this->waist_z * this->waist_z)
        );
    }

protected:
    double get_amplitude_at_focus() const override {
        const double area = this->waist_y * this->waist_z;

        return std::sqrt(
            4.0 * this->optical_power /
            (
                Constants::pi *
                Constants::vacuum_permitivity *
                Constants::light_speed *
                area
            )
        );
    }
};
