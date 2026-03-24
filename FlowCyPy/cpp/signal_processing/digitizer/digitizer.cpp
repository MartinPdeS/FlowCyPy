#include "digitizer.h"

#include <omp.h>


Digitizer::Digitizer(
    const double bandwidth,
    const double sampling_rate,
    const size_t bit_depth,
    const double min_voltage,
    const double max_voltage,
    const bool use_auto_range,
    const bool output_signed_codes,
    const bool debug_mode
)
    : bandwidth(bandwidth),
      sampling_rate(sampling_rate),
      bit_depth(bit_depth),
      min_voltage(min_voltage),
      max_voltage(max_voltage),
      use_auto_range(use_auto_range),
      output_signed_codes(output_signed_codes),
      debug_mode(debug_mode)
{
    if (std::isnan(this->sampling_rate) || this->sampling_rate <= 0.0) {
        throw std::invalid_argument("Digitizer sampling_rate must be strictly positive.");
    }

    if (!std::isnan(this->bandwidth) && this->bandwidth <= 0.0) {
        throw std::invalid_argument("Digitizer bandwidth must be strictly positive when provided.");
    }

    if (
        !std::isnan(this->min_voltage) &&
        !std::isnan(this->max_voltage) &&
        this->max_voltage <= this->min_voltage
    ) {
        throw std::invalid_argument(
            "Digitizer requires max_voltage to be greater than min_voltage."
        );
    }

    if (this->bit_depth > 63) {
        throw std::invalid_argument(
            "Digitizer bit_depth must be smaller than or equal to 63."
        );
    }

    if (this->debug_mode) {
        std::printf(
            "[Digitizer] Initialized | bandwidth=%g Hz | sampling_rate=%g Hz | bit_depth=%zu | min_voltage=%g V | max_voltage=%g V | use_auto_range=%d | output_signed_codes=%d\n",
            this->bandwidth,
            this->sampling_rate,
            this->bit_depth,
            this->min_voltage,
            this->max_voltage,
            static_cast<int>(this->use_auto_range),
            static_cast<int>(this->output_signed_codes)
        );
    }
}


bool Digitizer::has_bandwidth() const {
    return !std::isnan(this->bandwidth);
}


bool Digitizer::has_voltage_range() const {
    return !std::isnan(this->min_voltage) && !std::isnan(this->max_voltage);
}


bool Digitizer::should_digitize() const {
    return this->bit_depth > 0;
}


bool Digitizer::has_signed_output_codes() const {
    return this->output_signed_codes;
}


void Digitizer::clear_bandwidth() {
    this->bandwidth = std::numeric_limits<double>::quiet_NaN();

    if (this->debug_mode) {
        std::printf("[Digitizer] bandwidth cleared\n");
    }
}


void Digitizer::clear_voltage_range() {
    this->min_voltage = std::numeric_limits<double>::quiet_NaN();
    this->max_voltage = std::numeric_limits<double>::quiet_NaN();

    if (this->debug_mode) {
        std::printf("[Digitizer] voltage range cleared\n");
    }
}


void Digitizer::clip_signal(std::vector<double>& signal) const {
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


std::pair<double, double> Digitizer::get_min_max(const std::vector<double>& signal) const {
    double minimum_value = std::numeric_limits<double>::infinity();
    double maximum_value = -std::numeric_limits<double>::infinity();
    bool found_valid_sample = false;

    for (const double sample : signal) {
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


void Digitizer::set_auto_range(const std::vector<double>& signal) {
    const auto [computed_min_voltage, computed_max_voltage] = this->get_min_max(signal);

    if (computed_max_voltage <= computed_min_voltage) {
        throw std::runtime_error(
            "Automatic range inference produced an invalid voltage span."
        );
    }

    this->min_voltage = computed_min_voltage;
    this->max_voltage = computed_max_voltage;

    if (this->debug_mode) {
        std::printf(
            "[Digitizer] auto range set | min_voltage=%g V | max_voltage=%g V\n",
            this->min_voltage,
            this->max_voltage
        );
    }
}


int64_t Digitizer::get_minimum_code() const {
    if (!this->should_digitize()) {
        throw std::runtime_error(
            "Digitizer minimum code is undefined when bit_depth is 0."
        );
    }

    if (this->output_signed_codes) {
        return -(int64_t(1) << (this->bit_depth - 1));
    }

    return 0;
}


int64_t Digitizer::get_maximum_code() const {
    if (!this->should_digitize()) {
        throw std::runtime_error(
            "Digitizer maximum code is undefined when bit_depth is 0."
        );
    }

    if (this->output_signed_codes) {
        return (int64_t(1) << (this->bit_depth - 1)) - 1;
    }

    return static_cast<int64_t>((uint64_t(1) << this->bit_depth) - uint64_t(1));
}


void Digitizer::digitize_signal(std::vector<double>& signal) const {
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

    const double voltage_span = this->max_voltage - this->min_voltage;
    const int64_t minimum_code = this->get_minimum_code();
    const int64_t maximum_code = this->get_maximum_code();
    const double code_span = static_cast<double>(maximum_code - minimum_code);

    for (auto& sample : signal) {
        if (std::isnan(sample)) {
            continue;
        }

        const double clipped_sample = std::clamp(
            sample,
            this->min_voltage,
            this->max_voltage
        );

        const double normalized_value =
            (clipped_sample - this->min_voltage) / voltage_span;

        const double floating_code =
            static_cast<double>(minimum_code) + normalized_value * code_span;

        const int64_t quantized_code = std::clamp(
            static_cast<int64_t>(std::llround(floating_code)),
            minimum_code,
            maximum_code
        );

        sample = static_cast<double>(quantized_code);
    }
}


void Digitizer::process_signal(std::vector<double>& signal) {
    this->clip_signal(signal);
    this->digitize_signal(signal);
}


void Digitizer::capture_signal(const std::vector<double>& signal) {
    if (!this->use_auto_range) {
        return;
    }

    this->set_auto_range(signal);
}


void Digitizer::capture_signal(
    const std::vector<double>& signal,
    const bool use_auto_range_override
) {
    if (!use_auto_range_override) {
        return;
    }

    this->set_auto_range(signal);
}


void Digitizer::process_data_map(
    std::map<std::string, std::vector<double>>& data_map
) const {
    std::vector<std::string> channel_names;
    channel_names.reserve(data_map.size());

    for (const auto& [channel_name, channel_signal] : data_map) {
        (void)channel_signal;

        if (channel_name == "Time") {
            continue;
        }

        channel_names.push_back(channel_name);
    }

    if (this->debug_mode) {
        std::printf(
            "[Digitizer::process_data_map] channels=%zu | digitize=%d | has_voltage_range=%d\n",
            channel_names.size(),
            static_cast<int>(this->should_digitize()),
            static_cast<int>(this->has_voltage_range())
        );
    }

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (this->debug_mode) {
                std::printf(
                    "[Digitizer::process_data_map] using %d OpenMP threads\n",
                    omp_get_num_threads()
                );
            }
        }

        #pragma omp for
        for (ptrdiff_t index = 0; index < static_cast<ptrdiff_t>(channel_names.size()); ++index) {
            const std::string& channel_name =
                channel_names[static_cast<size_t>(index)];

            std::vector<double>& channel_signal = data_map.at(channel_name);

            this->clip_signal(channel_signal);
            this->digitize_signal(channel_signal);
        }
    }
}


std::map<std::string, std::vector<double>> Digitizer::get_processed_data_map(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    std::map<std::string, std::vector<double>> output_map(data_map);
    this->process_data_map(output_map);
    return output_map;
}


bool Digitizer::processed_data_map_contains_nan(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    for (const auto& [channel_name, channel_signal] : data_map) {
        if (channel_name == "Time") {
            continue;
        }

        for (const double sample : channel_signal) {
            if (std::isnan(sample)) {
                return true;
            }
        }
    }

    return false;
}


std::vector<double> Digitizer::get_time_series(const double run_time) const {
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
