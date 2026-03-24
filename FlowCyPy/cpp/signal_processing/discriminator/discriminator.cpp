#include "discriminator.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <stdexcept>


// =============================
// BaseDiscriminator implementation
// =============================

void BaseDiscriminator::add_time(const std::vector<double> &time) {
    if (time.empty()) {
        throw std::runtime_error("Time vector must not be empty.");
    }

    this->trigger.add_time(time);
}


void BaseDiscriminator::add_signal(
    const std::string &detector_name,
    const std::vector<double> &signal
) {
    if (signal.empty()) {
        throw std::runtime_error("Signal vector must not be empty.");
    }

    this->trigger.add_signal(detector_name, signal);
}


void BaseDiscriminator::validate_detector_existence(
    const std::string &detector_name
) const {
    if (this->trigger.signal_map.find(detector_name) == this->trigger.signal_map.end()) {
        throw std::runtime_error(
            "Trigger detector '" + detector_name + "' was not found in the signal map."
        );
    }
}


double BaseDiscriminator::parse_threshold(const Threshold &threshold) const {
    if (!threshold.is_defined()) {
        throw std::runtime_error("Threshold is undefined.");
    }

    if (threshold.is_numeric()) {
        return threshold.get_numeric();
    }

    return this->parse_sigma_threshold_string(threshold.get_symbolic());
}


double BaseDiscriminator::parse_sigma_threshold_string(
    const std::string &threshold_string
) const {
    std::string compact_threshold_string = threshold_string;

    compact_threshold_string.erase(
        std::remove_if(
            compact_threshold_string.begin(),
            compact_threshold_string.end(),
            [](unsigned char character) {
                return std::isspace(character);
            }
        ),
        compact_threshold_string.end()
    );

    const std::string sigma_suffix = "sigma";

    if (
        compact_threshold_string.size() <= sigma_suffix.size() ||
        compact_threshold_string.substr(
            compact_threshold_string.size() - sigma_suffix.size()
        ) != sigma_suffix
    ) {
        throw std::runtime_error(
            "Unknown threshold format: '" + threshold_string +
            "'. Expected a numeric value or a string like '4sigma'."
        );
    }

    const std::string sigma_multiplier_string =
        compact_threshold_string.substr(
            0,
            compact_threshold_string.size() - sigma_suffix.size()
        );

    double number_of_sigma;
    try {
        number_of_sigma = std::stod(sigma_multiplier_string);
    } catch (...) {
        throw std::runtime_error(
            "Failed to parse sigma threshold from '" + threshold_string + "'."
        );
    }

    this->validate_detector_existence(this->trigger_channel);

    const std::vector<double> &signal =
        this->trigger.signal_map.at(this->trigger_channel);

    const double median_value = this->compute_median(signal);
    const double sigma_mad = this->compute_mad_based_sigma(signal);

    return median_value + number_of_sigma * sigma_mad;
}


double BaseDiscriminator::compute_median(std::vector<double> values) const {
    if (values.empty()) {
        throw std::runtime_error("Cannot compute median of an empty signal.");
    }

    const size_t number_of_values = values.size();
    const size_t middle_index = number_of_values / 2;

    std::nth_element(
        values.begin(),
        values.begin() + middle_index,
        values.end()
    );

    const double upper_middle_value = values[middle_index];

    if (number_of_values % 2 != 0) {
        return upper_middle_value;
    }

    std::nth_element(
        values.begin(),
        values.begin() + middle_index - 1,
        values.begin() + middle_index
    );

    const double lower_middle_value = values[middle_index - 1];

    return 0.5 * (lower_middle_value + upper_middle_value);
}


double BaseDiscriminator::compute_mad_based_sigma(
    const std::vector<double> &signal
) const {
    if (signal.empty()) {
        throw std::runtime_error(
            "Cannot compute MAD based sigma of an empty signal."
        );
    }

    const double median_value = this->compute_median(signal);

    std::vector<double> absolute_deviations;
    absolute_deviations.reserve(signal.size());

    for (const double value : signal) {
        absolute_deviations.push_back(std::abs(value - median_value));
    }

    const double mad = this->compute_median(std::move(absolute_deviations));

    return mad / 0.6745;
}



// =============================
// FixedWindow implementation
// =============================

void FixedWindow::run() {
    if (!this->threshold.is_defined()) {
        throw std::runtime_error(
            "FixedWindow threshold must be set before calling run()."
        );
    }

    this->trigger.clear();

    if (this->trigger.global_time.empty()) {
        throw std::runtime_error(
            "Global time axis must be set before running triggers."
        );
    }

    if (this->trigger_channel.empty()) {
        throw std::runtime_error(
            "Trigger detector name must be set before running triggers."
        );
    }

    this->validate_detector_existence(this->trigger_channel);

    this->resolved_threshold = this->parse_threshold(this->threshold);

    const std::vector<double> &signal =
        this->trigger.signal_map.at(this->trigger_channel);

    std::vector<std::pair<int, int>> valid_triggers;
    std::vector<int> trigger_indices;

    for (size_t index = 1; index < signal.size(); ++index) {
        if (
            signal[index - 1] <= this->resolved_threshold &&
            signal[index] > this->resolved_threshold
        ) {
            trigger_indices.push_back(static_cast<int>(index) - 1);
        }
    }

    int last_end = -1;

    for (const int index : trigger_indices) {
        const int start = index - static_cast<int>(this->pre_buffer) - 1;
        const int end = index + static_cast<int>(this->post_buffer);

        if (start < 0 || end >= static_cast<int>(signal.size())) {
            continue;
        }

        if (start > last_end) {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }

        if (
            this->max_triggers > 0 &&
            valid_triggers.size() >= static_cast<size_t>(this->max_triggers)
        ) {
            break;
        }
    }

    this->trigger.run_segmentation(valid_triggers);
    this->print_warning_if_no_signal_met_trigger_criteria();
}



// =============================
// DynamicWindow implementation
// =============================

void DynamicWindow::run() {
    if (!this->threshold.is_defined()) {
        throw std::runtime_error(
            "DynamicWindow threshold must be set before calling run()."
        );
    }

    this->trigger.clear();

    if (this->trigger.global_time.empty()) {
        throw std::runtime_error(
            "Global time axis must be set before running triggers."
        );
    }

    if (this->trigger_channel.empty()) {
        throw std::runtime_error(
            "Trigger detector name must be set before running triggers."
        );
    }

    this->validate_detector_existence(this->trigger_channel);

    this->resolved_threshold = this->parse_threshold(this->threshold);

    const std::vector<double> &signal =
        this->trigger.signal_map.at(this->trigger_channel);

    std::vector<std::pair<int, int>> valid_triggers;

    int last_end = -1;

    for (size_t index = 1; index < signal.size(); ++index) {
        if (
            signal[index - 1] <= this->resolved_threshold &&
            signal[index] > resolved_threshold
        ) {
            int start = static_cast<int>(index) - static_cast<int>(this->pre_buffer);

            if (start < 0) {
                start = 0;
            }

            size_t end_index = index;

            while (
                end_index < signal.size() &&
                signal[end_index] > this->resolved_threshold
            ) {
                ++end_index;
            }

            int end =
                static_cast<int>(end_index) - 1 +
                static_cast<int>(this->post_buffer);

            if (end >= static_cast<int>(signal.size())) {
                end = static_cast<int>(signal.size()) - 1;
            }

            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }

            if (
                this->max_triggers > 0 &&
                valid_triggers.size() >= static_cast<size_t>(this->max_triggers)
            ) {
                break;
            }

            index = end_index;
        }
    }

    this->trigger.run_segmentation(valid_triggers);
    this->print_warning_if_no_signal_met_trigger_criteria();
}



// =============================
// DoubleThreshold implementation
// =============================
void DoubleThreshold::run() {
    if (!this->threshold.is_defined()) {
        throw std::runtime_error(
            "DoubleThreshold primary threshold must be set before calling run()."
        );
    }

    this->trigger.clear();

    if (this->trigger.global_time.empty()) {
        throw std::runtime_error(
            "Global time axis must be set before running triggers."
        );
    }

    if (this->trigger_channel.empty()) {
        throw std::runtime_error(
            "Trigger detector name must be set before running triggers."
        );
    }

    this->validate_detector_existence(this->trigger_channel);

    this->resolved_upper_threshold = this->parse_threshold(this->threshold);

    this->resolved_lower_threshold =
        this->lower_threshold.is_defined()
            ? this->parse_threshold(this->lower_threshold)
            : this->resolved_upper_threshold;

    const std::vector<double> &signal =
        this->trigger.signal_map.at(this->trigger_channel);

    std::vector<std::pair<int, int>> valid_triggers;

    int last_end = -1;

    for (size_t index = 1; index < signal.size(); ++index) {
        if (
            signal[index - 1] <= this->resolved_upper_threshold &&
            signal[index] > this->resolved_upper_threshold
        ) {
            size_t threshold_crossing_end = index;

            if (this->debounce_enabled && this->min_window_duration != -1) {
                size_t above_threshold_count = 0;

                while (
                    threshold_crossing_end < signal.size() &&
                    signal[threshold_crossing_end] > this->resolved_upper_threshold
                ) {
                    ++above_threshold_count;
                    ++threshold_crossing_end;

                    if (
                        above_threshold_count >=
                        static_cast<size_t>(this->min_window_duration)
                    ) {
                        break;
                    }
                }

                if (
                    above_threshold_count <
                    static_cast<size_t>(this->min_window_duration)
                ) {
                    index = threshold_crossing_end;
                    continue;
                }
            } else {
                while (
                    threshold_crossing_end < signal.size() &&
                    signal[threshold_crossing_end] > this->resolved_upper_threshold
                ) {
                    ++threshold_crossing_end;
                }
            }

            int start = static_cast<int>(index) - static_cast<int>(this->pre_buffer);

            if (start < 0) {
                start = 0;
            }

            size_t lower_threshold_crossing_end = threshold_crossing_end;

            while (
                lower_threshold_crossing_end < signal.size() &&
                signal[lower_threshold_crossing_end] > this->resolved_lower_threshold
            ) {
                ++lower_threshold_crossing_end;
            }

            int end =
                static_cast<int>(lower_threshold_crossing_end) - 1 +
                static_cast<int>(this->post_buffer);

            if (end >= static_cast<int>(signal.size())) {
                end = static_cast<int>(signal.size()) - 1;
            }

            if (start > last_end) {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }

            if (
                this->max_triggers > 0 &&
                valid_triggers.size() >= static_cast<size_t>(this->max_triggers)
            ) {
                break;
            }

            index = lower_threshold_crossing_end;
        }
    }

    this->trigger.run_segmentation(valid_triggers);
    this->print_warning_if_no_signal_met_trigger_criteria();
}
