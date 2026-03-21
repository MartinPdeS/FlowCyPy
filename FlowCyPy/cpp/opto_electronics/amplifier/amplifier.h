#pragma once

#include <vector>
#include <limits>
#include <utils/constants.h>
#include <signal_generator/signal_generator.h>

class Amplifier {
public:
    double gain; // units of V/V
    double bandwidth; // units of Hz
    double voltage_noise_density; // units of V/sqrt(Hz)
    double current_noise_density; // units of A/sqrt(Hz)


    Amplifier(
        double gain,
        double bandwidth = std::numeric_limits<double>::quiet_NaN(),
        double voltage_noise_density = 0.0,
        double current_noise_density = 0.0
    ) : gain(gain),
        bandwidth(bandwidth),
        voltage_noise_density(voltage_noise_density),
        current_noise_density(current_noise_density)
    {
    }

    double get_rms_noise() const {
        double voltage_noise = voltage_noise_density * std::sqrt(this->bandwidth);
        double current_noise = current_noise_density * std::sqrt(this->bandwidth) * this->gain;
        return std::sqrt(voltage_noise * voltage_noise + current_noise * current_noise);
    }

    void amplify(SignalGenerator& signal) const {
        if (std::isnan(this->bandwidth)) {
            this->amplify_without_bandwidth(signal);
        } else {
            this->amplify_with_bandwidth(signal);
        }

        if (this->voltage_noise_density > 0.0 || this->current_noise_density > 0.0) {
            double noise_rms = this->get_rms_noise();
            signal.add_gaussian_noise(0.0, noise_rms);
        }
    }

    void amplify_with_bandwidth(SignalGenerator& signal) const {
        for (const auto& [channel, values] : signal.data_dict) {
            if (channel == SignalGenerator::TIME_KEY) {
                continue; // Skip time axis
            }

            for (double& sample : signal.data_dict[channel]) {
                // Apply a simple low-pass filter based on the bandwidth
                double filtered_sample = sample * (this->bandwidth / (this->bandwidth + 1.0)); // Placeholder for actual filter implementation
                sample = filtered_sample * this->gain;
            }
        }
    }

    void amplify_without_bandwidth(SignalGenerator& signal) const {
        for (const auto& [channel, values] : signal.data_dict) {
            if (channel == SignalGenerator::TIME_KEY) {
                continue; // Skip time axis
            }

            for (double& sample : signal.data_dict[channel]) {
                sample *= this->gain;
            }
        }
    }

};
