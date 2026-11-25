#include "digitizer.h"

#include <omp.h>
#include <cstdio>


namespace {

inline bool is_metadata_channel(const std::string& channel_name) {
    return channel_name == "Time" || channel_name == "segment_id";
}

}  // namespace


Digitizer::Digitizer(
    const double bandwidth,
    const double sampling_rate,
    const size_t bit_depth,
    const double min_voltage,
    const double max_voltage,
    const bool use_auto_range,
    const bool output_signed_codes,
    const bool debug_mode,
    const ChannelRangeMode channel_range_mode
)
    : bandwidth(bandwidth),
      sampling_rate(sampling_rate),
      bit_depth(bit_depth),
      min_voltage(min_voltage),
      max_voltage(max_voltage),
      use_auto_range(use_auto_range),
      output_signed_codes(output_signed_codes),
      debug_mode(debug_mode),
      channel_range_mode(channel_range_mode),
      channel_voltage_ranges()
{
    if (std::isnan(this->sampling_rate) || this->sampling_rate <= 0.0) {
        throw std::invalid_argument("Digitizer sampling_rate must be strictly positive.");
    }

    if (!std::isnan(this->bandwidth) && this->bandwidth <= 0.0) {
        throw std::invalid_argument("Digitizer bandwidth must be strictly positive when provided.");
    }

    this->validate_voltage_range_pair(
        this->min_voltage,
        this->max_voltage,
        "Digitizer voltage range"
    );

    if (this->bit_depth > 63) {
        throw std::invalid_argument(
            "Digitizer bit_depth must be smaller than or equal to 63."
        );
    }

    if (this->debug_mode) {
        std::printf(
            "[Digitizer] Initialized | bandwidth=%g Hz | sampling_rate=%g Hz | bit_depth=%zu | min_voltage=%g V | max_voltage=%g V | use_auto_range=%d | output_signed_codes=%d | channel_range_mode=%d\n",
            this->bandwidth,
            this->sampling_rate,
            this->bit_depth,
            this->min_voltage,
            this->max_voltage,
            static_cast<int>(this->use_auto_range),
            static_cast<int>(this->output_signed_codes),
            static_cast<int>(this->channel_range_mode)
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


void Digitizer::validate_voltage_range_pair(
    const double local_min_voltage,
    const double local_max_voltage,
    const std::string& range_name
) const {
    const bool minimum_is_defined = !std::isnan(local_min_voltage);
    const bool maximum_is_defined = !std::isnan(local_max_voltage);

    if (minimum_is_defined != maximum_is_defined) {
        throw std::invalid_argument(
            range_name + " requires both minimum and maximum to be defined together."
        );
    }

    if (minimum_is_defined && local_max_voltage <= local_min_voltage) {
        throw std::invalid_argument(
            range_name + " requires maximum_voltage to be greater than minimum_voltage."
        );
    }
}


void Digitizer::validate_voltage_range_for_digitization(
    const double local_min_voltage,
    const double local_max_voltage
) const {
    if (std::isnan(local_min_voltage) || std::isnan(local_max_voltage)) {
        throw std::runtime_error(
            "Digitization requires min_voltage and max_voltage to be defined."
        );
    }

    if (local_max_voltage <= local_min_voltage) {
        throw std::runtime_error(
            "Digitization requires max_voltage to be greater than min_voltage."
        );
    }
}


void Digitizer::clip_signal_with_range(
    std::vector<double>& signal,
    const double local_min_voltage,
    const double local_max_voltage
) const {
    if (std::isnan(local_min_voltage) || std::isnan(local_max_voltage)) {
        return;
    }

    for (auto& sample : signal) {
        if (std::isnan(sample)) {
            continue;
        }

        if (sample < local_min_voltage) {
            sample = local_min_voltage;
        }
        else if (sample > local_max_voltage) {
            sample = local_max_voltage;
        }
    }
}


void Digitizer::digitize_signal_with_range(
    std::vector<double>& signal,
    const double local_min_voltage,
    const double local_max_voltage
) const {
    if (!this->should_digitize()) {
        return;
    }

    this->validate_voltage_range_for_digitization(local_min_voltage, local_max_voltage);

    const double voltage_span = local_max_voltage - local_min_voltage;
    const int64_t minimum_code = this->get_minimum_code();
    const int64_t maximum_code = this->get_maximum_code();
    const double code_span = static_cast<double>(maximum_code - minimum_code);

    for (auto& sample : signal) {
        if (std::isnan(sample)) {
            continue;
        }

        const double clipped_sample = std::clamp(sample, local_min_voltage, local_max_voltage);
        const double normalized_value = (clipped_sample - local_min_voltage) / voltage_span;
        const double floating_code = static_cast<double>(minimum_code) + normalized_value * code_span;

        const int64_t quantized_code = std::clamp(
            static_cast<int64_t>(std::llround(floating_code)),
            minimum_code,
            maximum_code
        );

        sample = static_cast<double>(quantized_code);
    }
}


void Digitizer::process_signal_with_range(
    std::vector<double>& signal,
    const double local_min_voltage,
    const double local_max_voltage
) const {
    this->clip_signal_with_range(signal, local_min_voltage, local_max_voltage);
    this->digitize_signal_with_range(signal, local_min_voltage, local_max_voltage);
}


void Digitizer::clip_signal(std::vector<double>& signal) const {
    this->clip_signal_with_range(signal, this->min_voltage, this->max_voltage);
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
    this->digitize_signal_with_range(signal, this->min_voltage, this->max_voltage);
}


std::pair<double, double> Digitizer::resolve_fixed_or_auto_range_for_signal(
    const std::vector<double>& signal
) const {
    if (this->use_auto_range) {
        return this->get_min_max(signal);
    }

    return {this->min_voltage, this->max_voltage};
}


void Digitizer::process_signal(std::vector<double>& signal) {
    const auto [local_min_voltage, local_max_voltage] =
        this->resolve_fixed_or_auto_range_for_signal(signal);

    if (this->use_auto_range) {
        this->min_voltage = local_min_voltage;
        this->max_voltage = local_max_voltage;
    }

    this->process_signal_with_range(signal, local_min_voltage, local_max_voltage);
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


std::pair<double, double> Digitizer::get_shared_min_max_from_data_map(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    double global_minimum_value = std::numeric_limits<double>::infinity();
    double global_maximum_value = -std::numeric_limits<double>::infinity();
    bool found_valid_sample = false;

    for (const auto& [channel_name, channel_signal] : data_map) {
        if (is_metadata_channel(channel_name)) {
            continue;
        }

        if (this->channel_voltage_ranges.contains(channel_name)) {
            continue;
        }

        for (const double sample : channel_signal) {
            if (std::isnan(sample)) {
                continue;
            }

            found_valid_sample = true;
            global_minimum_value = std::min(global_minimum_value, sample);
            global_maximum_value = std::max(global_maximum_value, sample);
        }
    }

    if (!found_valid_sample) {
        if (this->has_voltage_range()) {
            return {this->min_voltage, this->max_voltage};
        }

        throw std::runtime_error(
            "Cannot compute shared min and max from channels containing only NaN values."
        );
    }

    return {global_minimum_value, global_maximum_value};
}


std::pair<double, double> Digitizer::resolve_channel_voltage_range(
    const std::string& channel_name,
    const std::vector<double>& channel_signal,
    const std::pair<double, double>& shared_auto_range
) const {
    if (this->channel_voltage_ranges.contains(channel_name)) {
        return this->channel_voltage_ranges.at(channel_name);
    }

    if (!this->use_auto_range) {
        return {this->min_voltage, this->max_voltage};
    }

    if (this->channel_range_mode == ChannelRangeMode::shared) {
        return shared_auto_range;
    }

    return this->get_min_max(channel_signal);
}


void Digitizer::process_data_map(
    std::map<std::string, std::vector<double>>& data_map
) const {
    std::vector<std::string> channel_names;
    channel_names.reserve(data_map.size());

    for (const auto& [channel_name, channel_signal] : data_map) {
        (void)channel_signal;

        if (is_metadata_channel(channel_name)) {
            continue;
        }

        channel_names.push_back(channel_name);
    }

    std::pair<double, double> shared_auto_range = {
        std::numeric_limits<double>::quiet_NaN(),
        std::numeric_limits<double>::quiet_NaN()
    };

    if (this->use_auto_range && this->channel_range_mode == ChannelRangeMode::shared) {
        shared_auto_range = this->get_shared_min_max_from_data_map(data_map);

        if (this->debug_mode) {
            std::printf(
                "[Digitizer::process_data_map] shared_auto_range | min=%g V | max=%g V\n",
                shared_auto_range.first,
                shared_auto_range.second
            );
        }
    }

    if (this->debug_mode) {
        std::printf(
            "[Digitizer::process_data_map] channels=%zu | digitize=%d | use_auto_range=%d | has_voltage_range=%d | channel_range_mode=%d | explicit_channel_ranges=%zu\n",
            channel_names.size(),
            static_cast<int>(this->should_digitize()),
            static_cast<int>(this->use_auto_range),
            static_cast<int>(this->has_voltage_range()),
            static_cast<int>(this->channel_range_mode),
            this->channel_voltage_ranges.size()
        );
    }

    #pragma omp parallel for
    for (ptrdiff_t index = 0; index < static_cast<ptrdiff_t>(channel_names.size()); ++index) {
        const std::string& channel_name = channel_names[static_cast<size_t>(index)];
        std::vector<double>& channel_signal = data_map.at(channel_name);

        const auto [local_min_voltage, local_max_voltage] =
            this->resolve_channel_voltage_range(
                channel_name,
                channel_signal,
                shared_auto_range
            );

        this->process_signal_with_range(
            channel_signal,
            local_min_voltage,
            local_max_voltage
        );
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
        if (is_metadata_channel(channel_name)) {
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


std::vector<int64_t> Digitizer::convert_signal_to_signed_codes(
    const std::vector<double>& signal
) const {
    std::vector<int64_t> output_signal(signal.size());

    for (size_t index = 0; index < signal.size(); ++index) {
        const double sample = signal[index];

        if (std::isnan(sample)) {
            throw std::runtime_error(
                "Digitized integer output cannot represent NaN values."
            );
        }

        output_signal[index] = static_cast<int64_t>(std::llround(sample));
    }

    return output_signal;
}


std::vector<uint64_t> Digitizer::convert_signal_to_unsigned_codes(
    const std::vector<double>& signal
) const {
    std::vector<uint64_t> output_signal(signal.size());

    for (size_t index = 0; index < signal.size(); ++index) {
        const double sample = signal[index];

        if (std::isnan(sample)) {
            throw std::runtime_error(
                "Digitized integer output cannot represent NaN values."
            );
        }

        const int64_t code_value = static_cast<int64_t>(std::llround(sample));

        if (code_value < 0) {
            throw std::runtime_error(
                "Unsigned digitizer output encountered a negative code."
            );
        }

        output_signal[index] = static_cast<uint64_t>(code_value);
    }

    return output_signal;
}


std::map<std::string, std::vector<int64_t>> Digitizer::get_processed_signed_data_map(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    const std::map<std::string, std::vector<double>> processed_data_map =
        this->get_processed_data_map(data_map);

    std::map<std::string, std::vector<int64_t>> output_map;

    for (const auto& [channel_name, channel_signal] : processed_data_map) {
        if (is_metadata_channel(channel_name)) {
            continue;
        }

        output_map[channel_name] = this->convert_signal_to_signed_codes(channel_signal);
    }

    return output_map;
}


std::map<std::string, std::vector<uint64_t>> Digitizer::get_processed_unsigned_data_map(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    const std::map<std::string, std::vector<double>> processed_data_map =
        this->get_processed_data_map(data_map);

    std::map<std::string, std::vector<uint64_t>> output_map;

    for (const auto& [channel_name, channel_signal] : processed_data_map) {
        if (is_metadata_channel(channel_name)) {
            continue;
        }

        output_map[channel_name] = this->convert_signal_to_unsigned_codes(channel_signal);
    }

    return output_map;
}


std::map<std::string, std::vector<double>> Digitizer::process_flat_acquisition_data(
    const std::map<std::string, std::vector<double>>& data_map
) const {
    if (!data_map.contains("Time")) {
        throw std::runtime_error("Input dictionary must contain a 'Time' key.");
    }

    return this->get_processed_data_map(data_map);
}


std::map<std::string, std::map<std::string, std::vector<double>>> Digitizer::process_nested_acquisition_data(
    const std::map<std::string, std::map<std::string, std::vector<double>>>& data_map
) const {
    std::map<std::string, std::map<std::string, std::vector<double>>> output_map;

    for (const auto& [segment_id, segment_data_map] : data_map) {
        if (!segment_data_map.contains("Time")) {
            throw std::runtime_error(
                "Each triggered segment dictionary must contain a 'Time' key."
            );
        }

        output_map[segment_id] = this->get_processed_data_map(segment_data_map);
    }

    return output_map;
}


void Digitizer::set_channel_voltage_range(
    const std::string& channel_name,
    const double minimum_voltage,
    const double maximum_voltage
) {
    this->validate_voltage_range_pair(
        minimum_voltage,
        maximum_voltage,
        "Channel voltage range for '" + channel_name + "'"
    );

    if (std::isnan(minimum_voltage) || std::isnan(maximum_voltage)) {
        throw std::invalid_argument(
            "Channel voltage range for '" + channel_name + "' cannot be undefined."
        );
    }

    this->channel_voltage_ranges[channel_name] = {minimum_voltage, maximum_voltage};
}


void Digitizer::clear_channel_voltage_range(const std::string& channel_name) {
    this->channel_voltage_ranges.erase(channel_name);
}


void Digitizer::clear_all_channel_voltage_ranges() {
    this->channel_voltage_ranges.clear();
}


bool Digitizer::has_channel_voltage_range(const std::string& channel_name) const {
    return this->channel_voltage_ranges.contains(channel_name);
}


std::pair<double, double> Digitizer::get_channel_voltage_range(
    const std::string& channel_name
) const {
    if (!this->channel_voltage_ranges.contains(channel_name)) {
        throw std::runtime_error(
            "No explicit channel voltage range is defined for channel '" + channel_name + "'."
        );
    }

    return this->channel_voltage_ranges.at(channel_name);
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


std::string Digitizer::repr() const {
    std::string channel_range_mode_string = "shared";

    if (this->channel_range_mode == ChannelRangeMode::per_channel) {
        channel_range_mode_string = "per_channel";
    }

    return
        "Digitizer("
        "bandwidth=" + (
            std::isnan(this->bandwidth) ? std::string("None") : std::to_string(this->bandwidth)
        ) +
        ", sampling_rate=" + std::to_string(this->sampling_rate) +
        ", bit_depth=" + std::to_string(this->bit_depth) +
        ", min_voltage=" + (
            std::isnan(this->min_voltage) ? std::string("None") : std::to_string(this->min_voltage)
        ) +
        ", max_voltage=" + (
            std::isnan(this->max_voltage) ? std::string("None") : std::to_string(this->max_voltage)
        ) +
        ", use_auto_range=" + std::string(this->use_auto_range ? "True" : "False") +
        ", output_signed_codes=" + std::string(this->output_signed_codes ? "True" : "False") +
        ", channel_range_mode='" + channel_range_mode_string + "'" +
        ", explicit_channel_range_count=" + std::to_string(this->channel_voltage_ranges.size()) +
        ")";
}
