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
    bool include_shot_noise; // whether to include shot noise in generated signals
    bool include_rin_noise;  // whether to include RIN noise in generated signals

    virtual ~BaseSource() = default;

    BaseSource(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double polarization,
        bool include_shot_noise = true,
        bool include_rin_noise = true
    )
        :   wavelength(wavelength),
            rin(rin),
            optical_power(optical_power),
            amplitude(0.0),
            polarization(polarization),
            include_shot_noise(include_shot_noise),
            include_rin_noise(include_rin_noise)
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

    double get_watt_to_photon_factor(const double bandwidth) const {
        if (bandwidth <= 0.0) {
            throw std::runtime_error("bandwidth must be strictly positive.");
        }

        const double photon_energy = this->get_photon_energy();
        const double sampling_interval = 1.0 / (2.0 * bandwidth);

        return sampling_interval / photon_energy;   // [photons / watt]
    }

    void add_rin_to_signal(
        std::vector<double>& signal_values,
        const double bandwidth
    ) const {
        if (bandwidth < 0.0) {
            throw std::runtime_error("bandwidth must be non negative.");
        }

        static thread_local std::random_device random_device;
        static thread_local std::mt19937 generator(random_device());

        const double rin_linear = this->get_rin_linear();

        for (size_t index = 0; index < signal_values.size(); ++index) {
            const double signal_value = signal_values[index];
            const double standard_deviation = std::sqrt(rin_linear * bandwidth) * signal_value;

            std::normal_distribution<double> distribution(0.0, standard_deviation);

            signal_values[index] += distribution(generator);
        }
    }

    void add_shot_noise_to_signal(
        std::vector<double>& power_values,
        const double bandwidth
    ) const {
        if (bandwidth <= 0.0) {
            throw std::runtime_error("bandwidth must be strictly positive.");
        }

        static thread_local std::random_device random_device;
        static thread_local std::mt19937 generator(random_device());

        const double watt_to_photon = this->get_watt_to_photon_factor(bandwidth);

        for (size_t index = 0; index < power_values.size(); ++index) {
            const double current_power = power_values[index];

            if (current_power < 0.0) {
                throw std::runtime_error("shot noise cannot be applied to negative optical power values.");
            }

            const double mean_photon_count = current_power * watt_to_photon;

            double noisy_photon_count = 0.0;

            if (mean_photon_count < 100.0) {
                std::poisson_distribution<int> distribution(mean_photon_count);
                noisy_photon_count = static_cast<double>(distribution(generator));
            } else {
                std::normal_distribution<double> distribution(
                    mean_photon_count,
                    std::sqrt(mean_photon_count)
                );
                noisy_photon_count = std::max(0.0, distribution(generator));
            }

            power_values[index] = noisy_photon_count / watt_to_photon;
        }
    }

    std::vector<double> get_amplitude_signal(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z,
        const double bandwidth
    ) const {
        this->validate_coordinate_vectors(x, y, z);

        std::vector<double> amplitudes;
        amplitudes.reserve(x.size());

        for (size_t index = 0; index < x.size(); ++index) {
            amplitudes.push_back(
                this->get_amplitude_at(
                    x[index],
                    y[index],
                    z[index]
                )
            );
        }

        if (this->include_rin_noise) {
            this->add_rin_to_signal(amplitudes, bandwidth);
        }

        return amplitudes;
    }

    std::vector<double> get_power_signal(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z,
        const double bandwidth
    ) const {
        this->validate_coordinate_vectors(x, y, z);

        std::vector<double> power_values;
        power_values.reserve(x.size());

        for (size_t index = 0; index < x.size(); ++index) {
            power_values.push_back(
                this->get_power_at(
                    x[index],
                    y[index],
                    z[index]
                )
            );
        }

        if (this->include_rin_noise) {
            this->add_rin_to_signal(power_values, bandwidth);
        }

        if (this->include_shot_noise) {
            this->add_shot_noise_to_signal(power_values, bandwidth);
        }

        return power_values;
    }

    double get_power_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const {
        return this->optical_power * this->get_normalized_profile_value(x, y, z);
    }

    virtual std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const = 0;

    virtual double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const = 0;

    virtual std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level,
        const double bandwidth
    ) const = 0;

protected:
    virtual double get_amplitude_at_focus() const = 0;

    virtual double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const = 0;

    void update_amplitude() {
        this->amplitude = this->get_amplitude_at_focus();
    }

    void validate_coordinate_vectors(
        const std::vector<double>& x,
        const std::vector<double>& y,
        const std::vector<double>& z
    ) const {
        if (x.size() != y.size() || x.size() != z.size()) {
            throw std::runtime_error("x, y, and z must have the same size.");
        }
    }

    void validate_pulse_vectors(
        const std::vector<double>& pulse_widths,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes
    ) const {
        if (
            pulse_widths.size() != pulse_centers.size() ||
            pulse_widths.size() != pulse_amplitudes.size()
        ) {
            throw std::runtime_error(
                "pulse_widths, pulse_centers, and pulse_amplitudes must have the same size."
            );
        }
    }

    void validate_velocity_vector(
        const std::vector<double>& velocity
    ) const {
        if (velocity.empty()) {
            throw std::runtime_error("velocity must not be empty.");
        }

        if (std::any_of(velocity.begin(), velocity.end(), [](double value) { return value <= 0.0; })) {
            throw std::runtime_error("velocity must be strictly positive.");
        }
    }
};




class Gaussian : public BaseSource {
public:
    double waist_y;   // [meter]
    double waist_z;   // [meter]

    Gaussian(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist_y,
        const double waist_z,
        const double polarization,
        bool include_shot_noise = true,
        bool include_rin_noise = true
    )
        : BaseSource(wavelength, rin, optical_power, polarization, include_shot_noise, include_rin_noise),
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

    void set_waist(
        const double waist_y,
        const double waist_z
    ) {
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

    std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const override {
        this->validate_velocity_vector(velocity);

        std::vector<double> widths;
        widths.reserve(velocity.size());

        for (double current_velocity : velocity) {
            widths.push_back(this->waist_z / (2.0 * current_velocity));
        }

        return widths;
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

    std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level,
        const double bandwidth
    ) const override {
        this->validate_pulse_vectors(
            velocities,
            pulse_centers,
            pulse_amplitudes
        );

        std::vector<double> signal;
        signal.reserve(time_array.size());

        for (double time_value : time_array) {
            double signal_value = base_level;

            for (size_t index = 0; index < velocities.size(); ++index) {
                if (velocities[index] <= 0.0) {
                    throw std::runtime_error("all velocity values must be strictly positive.");
                }

                const double pulse_width = this->waist_z / (2.0 * velocities[index]);
                const double normalized_time =
                    (time_value - pulse_centers[index]) / pulse_width;

                const double exponent = -0.5 * normalized_time * normalized_time;

                signal_value += pulse_amplitudes[index] * std::exp(exponent);
            }

            signal.push_back(signal_value);
        }

        if (this->include_shot_noise) {
            this->add_shot_noise_to_signal(signal, bandwidth);
        }

        return signal;
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

    double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const override {
        (void)x;

        return std::exp(
            -(y * y) / (this->waist_y * this->waist_y)
            - (z * z) / (this->waist_z * this->waist_z)
        );
    }
};



class FlatTop : public BaseSource {
public:
    double waist_y;   // [meter]
    double waist_z;   // [meter]

    FlatTop(
        const double wavelength,
        const double rin,
        const double optical_power,
        const double waist_y,
        const double waist_z,
        const double polarization,
        bool include_shot_noise = true,
        bool include_rin_noise = true
    )
        : BaseSource(wavelength, rin, optical_power, polarization, include_shot_noise, include_rin_noise),
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

    void set_waist(
        const double waist_y,
        const double waist_z
    ) {
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

    std::vector<double> get_particle_width(
        const std::vector<double>& velocity
    ) const override {
        this->validate_velocity_vector(velocity);

        std::vector<double> widths;
        widths.reserve(velocity.size());

        for (double current_velocity : velocity) {
            widths.push_back(this->waist_z / (2.0 * current_velocity));
        }

        return widths;
    }

    double get_amplitude_at(
        const double x,
        const double y,
        const double z = 0.0
    ) const override {
        (void)x;

        const double normalized_radius_squared =
            (y * y) / (this->waist_y * this->waist_y) +
            (z * z) / (this->waist_z * this->waist_z);

        if (normalized_radius_squared <= 1.0) {
            return this->amplitude;
        }

        return 0.0;
    }

    std::vector<double> generate_pulses(
        const std::vector<double>& velocities,
        const std::vector<double>& pulse_centers,
        const std::vector<double>& pulse_amplitudes,
        const std::vector<double>& time_array,
        const double base_level,
        const double bandwidth
    ) const override {
        this->validate_pulse_vectors(
            velocities,
            pulse_centers,
            pulse_amplitudes
        );

        std::vector<double> signal;
        signal.reserve(time_array.size());

        for (double time_value : time_array) {
            double signal_value = base_level;

            for (size_t index = 0; index < velocities.size(); ++index) {
                if (velocities[index] <= 0.0) {
                    throw std::runtime_error("all velocity values must be strictly positive.");
                }

                const double pulse_width = this->waist_z / (2.0 * velocities[index]);
                const bool is_inside_pulse =
                    std::abs(time_value - pulse_centers[index]) <= pulse_width / 2.0;

                signal_value += pulse_amplitudes[index] * (is_inside_pulse ? 1.0 : 0.0);
            }

            signal.push_back(signal_value);
        }

        if (this->include_shot_noise) {
            this->add_shot_noise_to_signal(signal, bandwidth);
        }

        return signal;
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

    double get_normalized_profile_value(
        const double x,
        const double y,
        const double z = 0.0
    ) const override {
        (void)x;

        const double normalized_radius_squared =
            (y * y) / (this->waist_y * this->waist_y) +
            (z * z) / (this->waist_z * this->waist_z);

        if (normalized_radius_squared <= 1.0) {
            return 1.0;
        }

        return 0.0;
    }
};
