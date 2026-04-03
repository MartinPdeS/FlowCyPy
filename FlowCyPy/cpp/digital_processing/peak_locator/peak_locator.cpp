#include "peak_locator.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>


// -------------------- FullWindowSupport --------------------
/**
 * @brief Return whether this support mode uses the full interval.
 *
 * Returns
 * -------
 * bool
 *     Always true for FullWindowSupport.
 */
bool FullWindowSupport::is_full_window() const {
    return true;
}


/**
 * @brief Return whether this support mode uses independent per-channel support.
 *
 * Returns
 * -------
 * bool
 *     Always false for FullWindowSupport.
 */
bool FullWindowSupport::is_independent() const {
    return false;
}


/**
 * @brief Return the channel specifier associated with this support mode.
 *
 * Returns
 * -------
 * std::string
 *     The literal string "full_window".
 */
std::string FullWindowSupport::get_channel() const {
    return "full_window";
}


/**
 * @brief Return the relative threshold of this support mode.
 *
 * Returns
 * -------
 * double
 *     Always 0.0 for FullWindowSupport.
 */
double FullWindowSupport::get_threshold() const {
    return 0.0;
}


/**
 * @brief Return a short human-readable support mode name.
 *
 * Returns
 * -------
 * std::string
 *     The literal string "full_window".
 */
std::string FullWindowSupport::get_name() const {
    return "full_window";
}


// -------------------- PulseSupport --------------------
/**
 * @brief Construct a pulse-based support specification.
 *
 * Parameters
 * ----------
 * channel :
 *     Support channel selector. Accepted values are:
 *     - "default"
 *     - "independent"
 *     - any detector name
 *
 * threshold :
 *     Relative threshold in the interval [0, 1].
 */
PulseSupport::PulseSupport(
    const std::string& channel,
    double threshold
)
    : channel(channel),
      threshold(threshold)
{
    if (this->threshold < 0.0 || this->threshold > 1.0) {
        throw std::runtime_error("PulseSupport threshold must lie in the interval [0, 1].");
    }

    if (this->channel.empty()) {
        throw std::runtime_error("PulseSupport channel must not be empty.");
    }
}


/**
 * @brief Return whether this support mode uses the full interval.
 *
 * Returns
 * -------
 * bool
 *     Always false for PulseSupport.
 */
bool PulseSupport::is_full_window() const {
    return false;
}


/**
 * @brief Return whether each channel computes its own support.
 *
 * Returns
 * -------
 * bool
 *     True when channel == "independent".
 */
bool PulseSupport::is_independent() const {
    return this->channel == "independent";
}


/**
 * @brief Return the configured support channel selector.
 *
 * Returns
 * -------
 * std::string
 *     The channel selector string.
 */
std::string PulseSupport::get_channel() const {
    return this->channel;
}


/**
 * @brief Return the relative threshold used for pulse support expansion.
 *
 * Returns
 * -------
 * double
 *     Relative threshold in [0, 1].
 */
double PulseSupport::get_threshold() const {
    return this->threshold;
}


/**
 * @brief Return a short human-readable support mode name.
 *
 * Returns
 * -------
 * std::string
 *     The literal string "pulse_support".
 */
std::string PulseSupport::get_name() const {
    return "pulse_support";
}


// -------------------- BasePeakLocator --------------------
/**
 * @brief Construct a base peak locator.
 *
 * Parameters
 * ----------
 * compute_width :
 *     Whether to compute width.
 * compute_area :
 *     Whether to compute area.
 * allow_negative_area :
 *     Whether negative samples are allowed during area accumulation.
 * padding_value :
 *     Padding value used for unused outputs.
 * max_number_of_peaks :
 *     Maximum number of peaks stored in output buffers.
 * support :
 *     Support object controlling width and area semantics.
 * debug_mode :
 *     Whether to print debug information.
 */
BasePeakLocator::BasePeakLocator(
    bool compute_width,
    bool compute_area,
    bool allow_negative_area,
    int padding_value,
    int max_number_of_peaks,
    std::shared_ptr<BaseSupport> support,
    bool debug_mode
)
    : compute_width(compute_width),
      compute_area(compute_area),
      allow_negative_area(allow_negative_area),
      padding_value(padding_value),
      max_number_of_peaks(max_number_of_peaks),
      debug_mode(debug_mode),
      support(std::move(support))
{
    if (this->max_number_of_peaks <= 0) {
        throw std::runtime_error("max_number_of_peaks must be strictly positive.");
    }

    if (!this->support) {
        throw std::runtime_error("support must not be null.");
    }

    this->initialize_output_vectors();
}


/**
 * @brief Validate that an input signal is not empty.
 *
 * Parameters
 * ----------
 * array :
 *     Input signal values.
 */
void BasePeakLocator::validate_input_signal(const std::vector<double>& array) const {
    if (array.empty()) {
        throw std::runtime_error("signal must not be empty.");
    }
}


/**
 * @brief Find the index of the maximum value in [start, end).
 *
 * Parameters
 * ----------
 * ptr :
 *     Pointer to the signal data.
 * start :
 *     Inclusive interval start.
 * end :
 *     Exclusive interval end.
 *
 * Returns
 * -------
 * size_t
 *     Index of the maximum sample.
 */
size_t BasePeakLocator::find_local_peak(
    const double* ptr,
    size_t start,
    size_t end
) const {
    if (ptr == nullptr) {
        throw std::runtime_error("Input pointer must not be null.");
    }

    if (end <= start) {
        throw std::runtime_error("Invalid interval: end must be greater than start.");
    }

    size_t local_peak_index = start;
    double maximum_value = ptr[start];

    for (size_t index = start + 1; index < end; ++index) {
        if (ptr[index] > maximum_value) {
            maximum_value = ptr[index];
            local_peak_index = index;
        }
    }

    return local_peak_index;
}


/**
 * @brief Compute support boundaries around a selected peak.
 *
 * Parameters
 * ----------
 * ptr :
 *     Pointer to the support signal.
 * start :
 *     Inclusive interval start.
 * end :
 *     Exclusive interval end.
 * peak_index :
 *     Peak index used to define the support.
 * left_boundary :
 *     Output inclusive left boundary.
 * right_boundary :
 *     Output inclusive right boundary.
 */
void BasePeakLocator::compute_boundaries(
    const double* ptr,
    size_t start,
    size_t end,
    size_t peak_index,
    size_t& left_boundary,
    size_t& right_boundary
) const {
    if (ptr == nullptr) {
        throw std::runtime_error("Input pointer must not be null.");
    }

    if (end <= start) {
        throw std::runtime_error("Invalid interval: end must be greater than start.");
    }

    if (peak_index < start || peak_index >= end) {
        throw std::runtime_error("peak_index must lie inside [start, end).");
    }

    left_boundary = peak_index;
    right_boundary = peak_index;

    if (this->support->is_full_window()) {
        left_boundary = start;
        right_boundary = end - 1;

        if (this->debug_mode) {
            std::printf(
                "[BasePeakLocator] compute_boundaries | "
                "support=%s | start=%zu | end=%zu | peak_index=%zu | "
                "mode=full_window | left_boundary=%zu | right_boundary=%zu\n",
                this->support->get_name().c_str(),
                start,
                end,
                peak_index,
                left_boundary,
                right_boundary
            );
        }

        return;
    }

    const double peak_value = ptr[peak_index];

    if (peak_value <= 0.0) {
        if (this->debug_mode) {
            std::printf(
                "[BasePeakLocator] compute_boundaries | "
                "support=%s | start=%zu | end=%zu | peak_index=%zu | "
                "peak_value=%g | mode=non_positive_peak | "
                "left_boundary=%zu | right_boundary=%zu\n",
                this->support->get_name().c_str(),
                start,
                end,
                peak_index,
                peak_value,
                left_boundary,
                right_boundary
            );
        }

        return;
    }

    const double threshold_value = this->support->get_threshold() * peak_value;

    while (
        left_boundary > start &&
        ptr[left_boundary - 1] >= threshold_value
    ) {
        --left_boundary;
    }

    while (
        right_boundary + 1 < end &&
        ptr[right_boundary + 1] >= threshold_value
    ) {
        ++right_boundary;
    }

    if (this->debug_mode) {
        std::printf(
            "[BasePeakLocator] compute_boundaries | "
            "support=%s | start=%zu | end=%zu | peak_index=%zu | "
            "peak_value=%g | relative_threshold=%g | threshold_value=%g | "
            "left_boundary=%zu | right_boundary=%zu | "
            "left_touches_boundary=%d | right_touches_boundary=%d\n",
            this->support->get_name().c_str(),
            start,
            end,
            peak_index,
            peak_value,
            this->support->get_threshold(),
            threshold_value,
            left_boundary,
            right_boundary,
            static_cast<int>(left_boundary == start),
            static_cast<int>(right_boundary == end - 1)
        );
    }
}


/**
 * @brief Compute width and area on the support derived from a given peak.
 *
 * Parameters
 * ----------
 * ptr :
 *     Pointer to the value signal used for area accumulation.
 * start :
 *     Inclusive interval start.
 * end :
 *     Exclusive interval end.
 * peak_index :
 *     Peak index used to define the support.
 *
 * Returns
 * -------
 * PeakMetrics
 *     Width, area, and support boundary information.
 */
PeakMetrics BasePeakLocator::compute_segment_metrics(
    const double* value_ptr,
    const double* support_ptr,
    size_t start,
    size_t end,
    size_t peak_index
) const {
    if (value_ptr == nullptr) {
        throw std::runtime_error("value_ptr must not be null.");
    }

    if (support_ptr == nullptr) {
        throw std::runtime_error("support_ptr must not be null.");
    }

    if (end <= start) {
        throw std::runtime_error("Invalid interval: end must be greater than start.");
    }

    if (peak_index < start || peak_index >= end) {
        throw std::runtime_error("peak_index must lie inside [start, end).");
    }

    PeakMetrics metrics{};

    const double support_peak_value = support_ptr[peak_index];

    size_t left_boundary = peak_index;
    size_t right_boundary = peak_index;

    this->compute_boundaries(
        support_ptr,
        start,
        end,
        peak_index,
        left_boundary,
        right_boundary
    );

    metrics.left_boundary = left_boundary;
    metrics.right_boundary = right_boundary;
    metrics.left_touches_boundary = (left_boundary == start);
    metrics.right_touches_boundary = (right_boundary == end - 1);
    metrics.width = static_cast<double>(right_boundary - left_boundary + 1);

    double area = static_cast<double>(this->padding_value);

    const bool valid_event =
        this->support->is_full_window() || (support_peak_value > 0.0);

    size_t number_of_positive_samples = 0;
    size_t number_of_negative_samples = 0;
    size_t number_of_zero_samples = 0;

    double signed_sum = 0.0;
    double positive_sum = 0.0;
    double negative_sum = 0.0;
    double minimum_value = value_ptr[left_boundary];
    double maximum_value = value_ptr[left_boundary];

    if (valid_event) {
        area = 0.0;

        for (size_t index = left_boundary; index <= right_boundary; ++index) {
            const double current_value = value_ptr[index];

            signed_sum += current_value;
            positive_sum += std::max(0.0, current_value);
            negative_sum += std::min(0.0, current_value);

            if (current_value > 0.0) {
                ++number_of_positive_samples;
            }
            else if (current_value < 0.0) {
                ++number_of_negative_samples;
            }
            else {
                ++number_of_zero_samples;
            }

            if (current_value < minimum_value) {
                minimum_value = current_value;
            }

            if (current_value > maximum_value) {
                maximum_value = current_value;
            }

            if (this->allow_negative_area) {
                area += current_value;
            }
            else {
                area += std::max(0.0, current_value);
            }
        }
    }

    metrics.area = area;

    if (this->debug_mode) {
        std::printf(
            "[BasePeakLocator] compute_segment_metrics | "
            "support=%s | start=%zu | end=%zu | peak_index=%zu | "
            "support_peak_value=%g | left_boundary=%zu | right_boundary=%zu | "
            "width=%g | valid_event=%d | allow_negative_area=%d | "
            "area=%g | signed_sum=%g | positive_sum=%g | negative_sum=%g | "
            "n_positive=%zu | n_negative=%zu | n_zero=%zu | "
            "min_value=%g | max_value=%g\n",
            this->support->get_name().c_str(),
            start,
            end,
            peak_index,
            support_peak_value,
            left_boundary,
            right_boundary,
            metrics.width,
            static_cast<int>(valid_event),
            static_cast<int>(this->allow_negative_area),
            metrics.area,
            signed_sum,
            positive_sum,
            negative_sum,
            number_of_positive_samples,
            number_of_negative_samples,
            number_of_zero_samples,
            minimum_value,
            maximum_value
        );
    }

    return metrics;
}

/**
 * @brief Sort peaks by descending height.
 *
 * Parameters
 * ----------
 * peaks :
 *     Vector of peaks to sort in place.
 */
void BasePeakLocator::sort_peaks_descending(std::vector<PeakData>& peaks) const {
    std::sort(
        peaks.begin(),
        peaks.end(),
        [](const PeakData& left_peak, const PeakData& right_peak) {
            return left_peak.value > right_peak.value;
        }
    );
}


/**
 * @brief Initialize output buffers using the configured padding value.
 */
void BasePeakLocator::initialize_output_vectors() {
    this->peak_indices.assign(this->max_number_of_peaks, this->padding_value);
    this->peak_heights.assign(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );
    this->peak_widths.assign(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );
    this->peak_areas.assign(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );
}


/**
 * @brief Compute metrics for one signal using the same signal for support.
 *
 * Parameters
 * ----------
 * array :
 *     Input signal.
 *
 * Returns
 * -------
 * MetricDictionary
 *     Computed metrics.
 */
MetricDictionary BasePeakLocator::compute_metric_dictionary(
    const std::vector<double>& array
) const {
    this->validate_input_signal(array);

    std::vector<PeakData> peaks = this->locate_peaks(array);
    this->sort_peaks_descending(peaks);

    MetricDictionary output;
    output["Index"] = std::vector<double>(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );
    output["Height"] = std::vector<double>(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );

    if (this->compute_area) {
        output["Area"] = std::vector<double>(
            this->max_number_of_peaks,
            static_cast<double>(this->padding_value)
        );
    }

    if (this->compute_width) {
        output["Width"] = std::vector<double>(
            this->max_number_of_peaks,
            static_cast<double>(this->padding_value)
        );
    }

    const size_t number_of_output_peaks = std::min(
        static_cast<size_t>(this->max_number_of_peaks),
        peaks.size()
    );

    for (size_t index = 0; index < number_of_output_peaks; ++index) {
        output["Index"][index] = static_cast<double>(peaks[index].index);
        output["Height"][index] = peaks[index].value;

        if (this->compute_width) {
            output["Width"][index] = peaks[index].width;
        }

        if (this->compute_area) {
            output["Area"][index] = peaks[index].area;
        }
    }

    return output;
}


/**
 * @brief Compute metrics for one signal using a separate support signal.
 *
 * Parameters
 * ----------
 * value_signal :
 *     Signal used to compute peak value and area.
 * support_signal :
 *     Signal used to define support boundaries.
 *
 * Returns
 * -------
 * MetricDictionary
 *     Computed metrics.
 */
MetricDictionary BasePeakLocator::compute_metric_dictionary_with_shared_support(
    const std::vector<double>& value_signal,
    const std::vector<double>& support_signal
) const {
    this->validate_input_signal(value_signal);
    this->validate_input_signal(support_signal);

    std::vector<PeakData> peaks = this->locate_peaks_with_support(value_signal, support_signal);
    this->sort_peaks_descending(peaks);

    MetricDictionary output;
    output["Index"] = std::vector<double>(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );
    output["Height"] = std::vector<double>(
        this->max_number_of_peaks,
        static_cast<double>(this->padding_value)
    );

    if (this->compute_area) {
        output["Area"] = std::vector<double>(
            this->max_number_of_peaks,
            static_cast<double>(this->padding_value)
        );
    }

    if (this->compute_width) {
        output["Width"] = std::vector<double>(
            this->max_number_of_peaks,
            static_cast<double>(this->padding_value)
        );
    }

    const size_t number_of_output_peaks = std::min(
        static_cast<size_t>(this->max_number_of_peaks),
        peaks.size()
    );

    for (size_t index = 0; index < number_of_output_peaks; ++index) {
        output["Index"][index] = static_cast<double>(peaks[index].index);
        output["Height"][index] = peaks[index].value;

        if (this->compute_width) {
            output["Width"][index] = peaks[index].width;
        }

        if (this->compute_area) {
            output["Area"][index] = peaks[index].area;
        }
    }

    return output;
}


/**
 * @brief Compute metrics for a single signal and update internal buffers.
 *
 * Parameters
 * ----------
 * array :
 *     Input signal.
 */
void BasePeakLocator::compute(const std::vector<double>& array) {
    const MetricDictionary output = this->compute_metric_dictionary(array);

    this->initialize_output_vectors();

    const std::vector<double>& index_values = output.at("Index");
    const std::vector<double>& height_values = output.at("Height");

    for (size_t index = 0; index < index_values.size(); ++index) {
        this->peak_indices[index] = static_cast<int>(std::llround(index_values[index]));
        this->peak_heights[index] = height_values[index];
    }

    if (this->compute_width) {
        const std::vector<double>& width_values = output.at("Width");

        for (size_t index = 0; index < width_values.size(); ++index) {
            this->peak_widths[index] = width_values[index];
        }
    }

    if (this->compute_area) {
        const std::vector<double>& area_values = output.at("Area");

        for (size_t index = 0; index < area_values.size(); ++index) {
            this->peak_areas[index] = area_values[index];
        }
    }
}


/**
 * @brief Return one stored metric vector.
 *
 * Parameters
 * ----------
 * metric_name :
 *     Name of the metric to return.
 *
 * Returns
 * -------
 * std::vector<double>
 *     Stored metric values.
 */
std::vector<double> BasePeakLocator::get_metric_py(const std::string& metric_name) const {
    if (metric_name == "Index") {
        return std::vector<double>(this->peak_indices.begin(), this->peak_indices.end());
    }

    if (metric_name == "Height") {
        return this->peak_heights;
    }

    if (metric_name == "Width") {
        return this->peak_widths;
    }

    if (metric_name == "Area") {
        return this->peak_areas;
    }

    throw std::runtime_error("No valid metric chosen: " + metric_name);
}


/**
 * @brief Compute and return metrics for a single signal.
 *
 * Parameters
 * ----------
 * array :
 *     Input signal.
 *
 * Returns
 * -------
 * MetricDictionary
 *     Computed metrics.
 */
MetricDictionary BasePeakLocator::get_metrics(const std::vector<double>& array) {
    this->compute(array);

    MetricDictionary output;
    output["Index"] = std::vector<double>(this->peak_indices.begin(), this->peak_indices.end());
    output["Height"] = this->peak_heights;

    if (this->compute_area) {
        output["Area"] = this->peak_areas;
    }

    if (this->compute_width) {
        output["Width"] = this->peak_widths;
    }

    return output;
}


/**
 * @brief Resolve the support channel name for a given current channel.
 *
 * Parameters
 * ----------
 * channel_dictionary :
 *     Channels available in the current segment.
 * current_channel_name :
 *     Channel currently being processed.
 * trigger_channel :
 *     Trigger channel provided by the caller.
 *
 * Returns
 * -------
 * std::string
 *     Resolved support channel name.
 */
std::string BasePeakLocator::resolve_support_channel_name(
    const std::map<std::string, std::vector<double>>& channel_dictionary,
    const std::string& current_channel_name,
    const std::string& trigger_channel
) const {
    if (this->support->is_full_window()) {
        return current_channel_name;
    }

    const std::string support_channel = this->support->get_channel();

    if (support_channel == "independent") {
        return current_channel_name;
    }

    if (support_channel == "default") {
        if (!trigger_channel.empty()) {
            if (channel_dictionary.find(trigger_channel) == channel_dictionary.end()) {
                throw std::runtime_error(
                    "Trigger channel '" + trigger_channel + "' is not present in the segmented data."
                );
            }
            return trigger_channel;
        }

        return current_channel_name;
    }

    if (channel_dictionary.find(support_channel) == channel_dictionary.end()) {
        throw std::runtime_error(
            "Support channel '" + support_channel + "' is not present in the segmented data."
        );
    }

    return support_channel;
}


/**
 * @brief Compute metrics for segmented multi-channel data.
 *
 * Parameters
 * ----------
 * segmented_signals :
 *     Segmented per-channel data.
 * trigger_channel :
 *     Trigger channel used when PulseSupport(channel="default") is configured.
 *
 * Returns
 * -------
 * SegmentedMetricDictionary
 *     Computed metrics.
 */
SegmentedMetricDictionary BasePeakLocator::run_segmented_signals(
    const SegmentedSignalDictionary& segmented_signals,
    const std::string& trigger_channel
) const {
    SegmentedMetricDictionary output_dictionary;

    for (const auto& [segment_id, channel_dictionary] : segmented_signals) {
        for (const auto& [channel_name, signal_vector] : channel_dictionary) {
            const std::string support_channel_name = this->resolve_support_channel_name(
                channel_dictionary,
                channel_name,
                trigger_channel
            );

            const std::vector<double>& support_signal =
                channel_dictionary.at(support_channel_name);

            if (support_channel_name == channel_name) {
                output_dictionary[segment_id][channel_name] =
                    this->compute_metric_dictionary(signal_vector);
            }
            else {
                output_dictionary[segment_id][channel_name] =
                    this->compute_metric_dictionary_with_shared_support(
                        signal_vector,
                        support_signal
                    );
            }
        }
    }

    return output_dictionary;
}


/**
 * @brief Regroup flat signals by segment id, then compute metrics.
 *
 * Parameters
 * ----------
 * segment_ids :
 *     Segment id associated with each sample.
 * flat_signals :
 *     Flat per-channel signal arrays.
 * trigger_channel :
 *     Trigger channel used when PulseSupport(channel="default") is configured.
 *
 * Returns
 * -------
 * SegmentedMetricDictionary
 *     Computed segmented metrics.
 */
SegmentedMetricDictionary BasePeakLocator::run_flat_segmented_signals(
    const std::vector<int>& segment_ids,
    const FlatSignalDictionary& flat_signals,
    const std::string& trigger_channel
) const {
    if (segment_ids.empty()) {
        throw std::runtime_error("segment_ids must not be empty.");
    }

    if (flat_signals.empty()) {
        throw std::runtime_error(
            "flat_signals must contain at least one signal channel."
        );
    }

    const size_t number_of_samples = segment_ids.size();

    SegmentedSignalDictionary segmented_signals;

    for (const auto& [channel_name, signal_vector] : flat_signals) {
        if (signal_vector.size() != number_of_samples) {
            throw std::runtime_error(
                "Channel '" + channel_name + "' has length " +
                std::to_string(signal_vector.size()) +
                " but segment_ids has length " +
                std::to_string(number_of_samples) + "."
            );
        }

        for (size_t sample_index = 0; sample_index < number_of_samples; ++sample_index) {
            segmented_signals[segment_ids[sample_index]][channel_name].push_back(
                signal_vector[sample_index]
            );
        }
    }

    return this->run_segmented_signals(segmented_signals, trigger_channel);
}


// -------------------- SlidingWindowPeakLocator --------------------
/**
 * @brief Construct a sliding window peak locator.
 *
 * Parameters
 * ----------
 * window_size :
 *     Number of samples in each window.
 * window_step :
 *     Step between consecutive windows. If -1, it is set to window_size.
 * max_number_of_peaks :
 *     Maximum number of peaks stored in outputs.
 * padding_value :
 *     Padding value used for unused entries.
 * compute_width :
 *     Whether to compute width.
 * compute_area :
 *     Whether to compute area.
 * allow_negative_area :
 *     Whether negative samples are allowed during area accumulation.
 * support :
 *     Support object controlling width and area semantics.
 * debug_mode :
 *     Whether to print debug information.
 */
SlidingWindowPeakLocator::SlidingWindowPeakLocator(
    int window_size,
    int window_step,
    int max_number_of_peaks,
    int padding_value,
    bool compute_width,
    bool compute_area,
    bool allow_negative_area,
    std::shared_ptr<BaseSupport> support,
    bool debug_mode
)
    : BasePeakLocator(
          compute_width,
          compute_area,
          allow_negative_area,
          padding_value,
          max_number_of_peaks,
          std::move(support),
          debug_mode
      ),
      window_size(window_size),
      window_step((window_step == -1) ? window_size : window_step)
{
    if (this->window_size <= 0) {
        throw std::runtime_error("window_size must be strictly positive.");
    }

    if (this->window_step <= 0) {
        throw std::runtime_error("window_step must be strictly positive.");
    }
}


/**
 * @brief Detect peaks using the same signal for value and support.
 *
 * Parameters
 * ----------
 * signal :
 *     Input signal.
 *
 * Returns
 * -------
 * std::vector<PeakData>
 *     Detected peaks.
 */
std::vector<PeakData> SlidingWindowPeakLocator::locate_peaks(
    const std::vector<double>& signal
) const {
    return this->locate_peaks_with_support(signal, signal);
}


/**
 * @brief Detect peaks using a value signal and a separate support signal.
 *
 * Parameters
 * ----------
 * value_signal :
 *     Signal used for peak values and area accumulation.
 * support_signal :
 *     Signal used to define support boundaries.
 *
 * Returns
 * -------
 * std::vector<PeakData>
 *     Detected peaks.
 */
std::vector<PeakData> SlidingWindowPeakLocator::locate_peaks_with_support(
    const std::vector<double>& value_signal,
    const std::vector<double>& support_signal
) const {
    this->validate_input_signal(value_signal);
    this->validate_input_signal(support_signal);

    if (value_signal.size() != support_signal.size()) {
        throw std::runtime_error("value_signal and support_signal must have the same size.");
    }

    const size_t number_of_samples = value_signal.size();

    std::vector<PeakData> peaks;
    peaks.reserve(
        (number_of_samples + static_cast<size_t>(this->window_step) - 1) /
        static_cast<size_t>(this->window_step)
    );

    for (size_t start = 0; start < number_of_samples; start += static_cast<size_t>(this->window_step)) {
        const size_t end = std::min(
            start + static_cast<size_t>(this->window_size),
            number_of_samples
        );

        if (end <= start) {
            continue;
        }

        const size_t support_peak_index = this->find_local_peak(support_signal.data(), start, end);
        const size_t value_peak_index = this->find_local_peak(value_signal.data(), start, end);
        const double peak_value = value_signal[value_peak_index];

        double width = static_cast<double>(this->padding_value);
        double area = static_cast<double>(this->padding_value);

        const bool should_compute_metrics =
            (this->compute_width || this->compute_area) &&
            (
                this->support->is_full_window() ||
                support_signal[support_peak_index] > 0.0
            );

        if (should_compute_metrics) {
            const PeakMetrics metrics = this->compute_segment_metrics(
                value_signal.data(),
                support_signal.data(),
                start,
                end,
                support_peak_index
            );

            if (this->compute_width) {
                width = metrics.width;
            }

            if (this->compute_area) {
                area = metrics.area;
            }
        }

        peaks.emplace_back(
            static_cast<int>(value_peak_index),
            peak_value,
            width,
            area
        );
    }

    return peaks;
}


// -------------------- GlobalPeakLocator --------------------
/**
 * @brief Construct a global peak locator.
 *
 * Parameters
 * ----------
 * max_number_of_peaks :
 *     Maximum number of peaks stored in outputs.
 * padding_value :
 *     Padding value used for unused entries.
 * compute_width :
 *     Whether to compute width.
 * compute_area :
 *     Whether to compute area.
 * allow_negative_area :
 *     Whether negative samples are allowed during area accumulation.
 * support :
 *     Support object controlling width and area semantics.
 * debug_mode :
 *     Whether to print debug information.
 */
GlobalPeakLocator::GlobalPeakLocator(
    int max_number_of_peaks,
    int padding_value,
    bool compute_width,
    bool compute_area,
    bool allow_negative_area,
    std::shared_ptr<BaseSupport> support,
    bool debug_mode
)
    : BasePeakLocator(
          compute_width,
          compute_area,
          allow_negative_area,
          padding_value,
          max_number_of_peaks,
          std::move(support),
          debug_mode
      )
{
    if (this->debug_mode) {
        std::printf(
            "[GlobalPeakLocator] Initialized | support=%s | compute_width=%d | compute_area=%d | allow_negative_area=%d | padding_value=%d | max_number_of_peaks=%d\n",
            this->support->get_name().c_str(),
            static_cast<int>(this->compute_width),
            static_cast<int>(this->compute_area),
            static_cast<int>(this->allow_negative_area),
            this->padding_value,
            this->max_number_of_peaks
        );
    }
}


/**
 * @brief Detect a global peak using the same signal for value and support.
 *
 * Parameters
 * ----------
 * signal :
 *     Input signal.
 *
 * Returns
 * -------
 * std::vector<PeakData>
 *     Detected peak.
 */
std::vector<PeakData> GlobalPeakLocator::locate_peaks(const std::vector<double>& signal) const {
    return this->locate_peaks_with_support(signal, signal);
}


/**
 * @brief Detect a global peak using a value signal and a separate support signal.
 *
 * Parameters
 * ----------
 * value_signal :
 *     Signal used for peak value and area accumulation.
 * support_signal :
 *     Signal used to define support boundaries.
 *
 * Returns
 * -------
 * std::vector<PeakData>
 *     Detected peak.
 */
std::vector<PeakData> GlobalPeakLocator::locate_peaks_with_support(
    const std::vector<double>& value_signal,
    const std::vector<double>& support_signal
) const {
    this->validate_input_signal(value_signal);
    this->validate_input_signal(support_signal);

    if (value_signal.size() != support_signal.size()) {
        throw std::runtime_error("value_signal and support_signal must have the same size.");
    }

    const size_t signal_size = value_signal.size();

    const size_t support_peak_index = this->find_local_peak(
        support_signal.data(),
        0,
        signal_size
    );

    size_t left_boundary = support_peak_index;
    size_t right_boundary = support_peak_index;

    this->compute_boundaries(
        support_signal.data(),
        0,
        signal_size,
        support_peak_index,
        left_boundary,
        right_boundary
    );

    const size_t value_peak_index = this->find_local_peak(
        value_signal.data(),
        left_boundary,
        right_boundary + 1
    );

    const double peak_value = value_signal[value_peak_index];

    double width = static_cast<double>(this->padding_value);
    double area = static_cast<double>(this->padding_value);

    if (
        (this->compute_width || this->compute_area) &&
        (
            this->support->is_full_window() ||
            support_signal[support_peak_index] > 0.0
        )
    ) {
        const PeakMetrics metrics = this->compute_segment_metrics(
            value_signal.data(),
            support_signal.data(),
            0,
            signal_size,
            support_peak_index
        );

        if (this->compute_width) {
            width = metrics.width;
        }

        if (this->compute_area) {
            area = metrics.area;
        }
    }

    if (this->debug_mode) {
        std::printf(
            "[GlobalPeakLocator] locate_peaks | "
            "support=%s | signal_size=%zu | "
            "support_peak_index=%zu | value_peak_index=%zu | "
            "left_boundary=%zu | right_boundary=%zu | "
            "peak_value=%g | width=%g | area=%g\n",
            this->support->get_name().c_str(),
            signal_size,
            support_peak_index,
            value_peak_index,
            left_boundary,
            right_boundary,
            peak_value,
            width,
            area
        );
    }

    return std::vector<PeakData>{
        PeakData(
            static_cast<int>(value_peak_index),
            peak_value,
            width,
            area
        )
    };
}
