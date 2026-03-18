#pragma once

#include <vector>
#include <random>
#include <utils/constants.h>

class BaseSource {
public:
    double wavelength;    // [meter]
    double rin;           // [/hertz]
    double optical_power; // [watt]
    double amplitude;     // [volt/meter]
    double polarization;   // radian

    virtual ~BaseSource() = default;

    BaseSource(const double _wavelength, const double _rin, const double _optical_power, const double _polarization)
    : wavelength(_wavelength), rin(_rin), optical_power(_optical_power), polarization(_polarization)
    {

    }

    /**
     * Compute frequency in hertz
     */
    double get_frequency() const {
        return Constants::light_speed / this->wavelength;
    }

    /**
     * Compute photon energy in joule/particle
     */
    double get_photon_energy() const {
        return Constants::plank * this->get_frequency(); // joule / particles
    }

    /**
     * Convert RIN from dB/Hz to linear scale
     */
    double get_rin_linear() const {
        return std::pow(10, this->rin / 10);
    }

    /**
     * Add RIN noise to the provided signal amplitudes
     *
     * @param amplitudes Vector of signal amplitudes to which RIN noise will be added
     * @param bandwidth Bandwidth in hertz over which the RIN is considered
     */
    void add_rin_to_signal(std::vector<double> &amplitudes, const double bandwidth) const {
        static thread_local std::random_device rd;
        static thread_local std::mt19937 generator(rd());

        double rin_linear = this->get_rin_linear();

        std::vector<double> output;
        output.reserve(amplitudes.size());

        for (size_t index=0; index<amplitudes.size(); ++index) {
            double amplitude = amplitudes[index];
            double std_dev = std::sqrt(rin_linear * bandwidth * amplitude);

            std::normal_distribution<double> distribution(0.0, std_dev);

            amplitudes[index] += distribution(generator);
        }
    }

private:
    /**
     * Compute the electric field amplitude at the focus point
     */
    virtual double get_amplitude_at_focus() const = 0;
};


class Gaussian : public BaseSource {
public:
    double waist;

    Gaussian(
        const double _wavelength,
        const double _rin,
        const double _optical_power,
        const double _waist,
        const double _polarization
    )
    : BaseSource(_wavelength, _rin, _optical_power, _polarization), waist(_waist)
    {
        this->amplitude = this->get_amplitude_at_focus();
    }

    void set_numerical_apreture(const double numerical_aperture) {
        this->waist = this->wavelength / (Constants::pi * numerical_aperture);
    }

    void set_waist(const double waist) {
        this->waist = waist;
    }

private:
    double get_amplitude_at_focus() const override
    {
        double area = this->waist * this->waist;
        double amplitude = std::sqrt(
            4. * this->optical_power / (Constants::pi * Constants::vacuum_permitivity * Constants::light_speed * area)
        );

        return amplitude; // [volt/meter]
    }
};


class AsymetricGaussian : public BaseSource {
public:
    double waist_y;
    double waist_z;

    AsymetricGaussian(
        const double _wavelength,
        const double _rin,
        const double _optical_power,
        const double _waist_y,
        const double _waist_z,
        const double _polarization
    )
    : BaseSource(_wavelength, _rin, _optical_power, _polarization), waist_y(_waist_y), waist_z(_waist_z)
    {
        this->amplitude = this->get_amplitude_at_focus();
    }

    void set_numerical_apreture(const double numerical_aperture_y, double numerical_aperture_z) {
        this->waist_y = this->wavelength / (Constants::pi * numerical_aperture_y);
        this->waist_z = this->wavelength / (Constants::pi * numerical_aperture_z);
    }

    void set_waist(const double waist_y, const double waist_z) {
        this->waist_y = waist_y;
        this->waist_z = waist_z;
    }


private:
    double get_amplitude_at_focus() const override
    {
        double area = this->waist_y * this->waist_z;
        double amplitude = std::sqrt(
            4. * this->optical_power / (Constants::pi * Constants::vacuum_permitivity * Constants::light_speed * area)
        );

        return amplitude; // [volt/meter]
    }
};
