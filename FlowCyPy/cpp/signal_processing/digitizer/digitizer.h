#pragma once

#include <vector>
#include <string>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <algorithm>
#include <cstddef>
#include <cstdint>


class Digitizer {
public:
    double bandwidth;
    double sampling_rate;
    size_t bit_depth;
    double min_voltage;
    double max_voltage;
    bool use_auto_range;

    Digitizer(
        const double bandwidth,
        const double sampling_rate,
        const size_t bit_depth = 0,
        const double min_voltage = std::numeric_limits<double>::quiet_NaN(),
        const double max_voltage = std::numeric_limits<double>::quiet_NaN(),
        const bool use_auto_range = false
    )
        : bandwidth(bandwidth),
          sampling_rate(sampling_rate),
          bit_depth(bit_depth),
          min_voltage(min_voltage),
          max_voltage(max_voltage),
          use_auto_range(use_auto_range)
    {
        if (sampling_rate <= 0.0) {
            throw std::invalid_argument("Digitizer sampling_rate must be strictly positive.");
        }

        if (bandwidth <= 0.0) {
            throw std::invalid_argument("Digitizer bandwidth must be strictly positive.");
        }

        if (
            !std::isnan(this->min_voltage) &&
            !std::isnan(this->max_voltage) &&
            this->max_voltage <= this->min_voltage
        ) {
            throw std::invalid_argument("Digitizer requires max_voltage to be greater than min_voltage.");
        }
    }

    bool has_voltage_range() const {
        return !std::isnan(this->min_voltage) && !std::isnan(this->max_voltage);
    }

    bool should_digitize() const {
        return this->bit_depth > 0;
    }

    void clear_voltage_range() {
        this->min_voltage = std::numeric_limits<double>::quiet_NaN();
        this->max_voltage = std::numeric_limits<double>::quiet_NaN();
    }

    void clip_signal(std::vector<double>& signal) const {
        if (!this->has_voltage_range()) {
            return;
        }

        for (auto& sample : signal) {
            if (std::isnan(sample)) {
                continue;
            }

            if (sample < this->min_voltage) {
                sample = this->min_voltage;
            }
            else if (sample > this->max_voltage) {
                sample = this->max_voltage;
            }
        }
    }

    std::pair<double, double> get_min_max(const std::vector<double>& signal) const {
        double minimum_value = std::numeric_limits<double>::infinity();
        double maximum_value = -std::numeric_limits<double>::infinity();
        bool found_valid_sample = false;

        for (const auto& sample : signal) {
            if (std::isnan(sample)) {
                continue;
            }

            found_valid_sample = true;
            minimum_value = std::min(minimum_value, sample);
            maximum_value = std::max(maximum_value, sample);
        }

        if (!found_valid_sample) {
            throw std::runtime_error(
                "Cannot compute min and max from a signal containing only NaN values."
            );
        }

        return {minimum_value, maximum_value};
    }

    void set_auto_range(const std::vector<double>& signal) {
        const auto [computed_min_voltage, computed_max_voltage] = this->get_min_max(signal);
        this->min_voltage = computed_min_voltage;
        this->max_voltage = computed_max_voltage;
    }

    void digitize_signal(std::vector<double>& signal) const {
        if (!this->should_digitize()) {
            return;
        }

        if (!this->has_voltage_range()) {
            throw std::runtime_error(
                "Digitization requires min_voltage and max_voltage to be defined."
            );
        }

        if (this->max_voltage <= this->min_voltage) {
            throw std::runtime_error(
                "Digitization requires max_voltage to be greater than min_voltage."
            );
        }

        const uint64_t quantization_level_count = (uint64_t(1) << this->bit_depth) - uint64_t(1);
        const double voltage_span = this->max_voltage - this->min_voltage;

        for (auto& sample : signal) {
            if (std::isnan(sample)) {
                continue;
            }

            const double normalized_value = (sample - this->min_voltage) / voltage_span;
            const double quantized_index = std::round(normalized_value * static_cast<double>(quantization_level_count));

            sample = this->min_voltage + (
                quantized_index / static_cast<double>(quantization_level_count)
            ) * voltage_span;
        }
    }

    void process_signal(std::vector<double>& signal) {
        if (this->use_auto_range) {
            this->set_auto_range(signal);
        }

        this->clip_signal(signal);
        this->digitize_signal(signal);
    }

    void process_signal(std::vector<double>& signal, const bool use_auto_range_override) {
        if (use_auto_range_override) {
            this->set_auto_range(signal);
        }

        this->clip_signal(signal);
        this->digitize_signal(signal);
    }

    void capture_signal(const std::vector<double>& signal) {
        if (this->use_auto_range) {
            this->set_auto_range(signal);
        }
    }

    void capture_signal(const std::vector<double>& signal, const bool use_auto_range_override) {
        if (use_auto_range_override) {
            this->set_auto_range(signal);
        }
    }

    std::vector<double> get_time_series(const double run_time) const {
        if (run_time < 0.0) {
            throw std::invalid_argument("Digitizer run_time must be non negative.");
        }

        const size_t sample_count = static_cast<size_t>(this->sampling_rate * run_time);
        std::vector<double> time_series(sample_count);

        for (size_t index = 0; index < sample_count; ++index) {
            time_series[index] = static_cast<double>(index) / this->sampling_rate;
        }

        return time_series;
    }
};
