#include "peak_locator.h"

#include <algorithm>
#include <stdexcept>


BasePeakLocator::BasePeakLocator(
    bool compute_width,
    bool compute_area,
    int padding_value,
    int max_number_of_peaks
)
    : compute_width(compute_width),
      compute_area(compute_area),
      padding_value(padding_value),
      max_number_of_peaks(max_number_of_peaks)
{
    if (this->max_number_of_peaks <= 0) {
        throw std::runtime_error("max_number_of_peaks must be strictly positive.");
    }
}


size_t BasePeakLocator::find_local_peak(
    const double* ptr,
    size_t start,
    size_t end
) {
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


PeakMetrics BasePeakLocator::compute_segment_metrics(
    const double* ptr,
    size_t start,
    size_t end,
    size_t peak_index,
    double threshold
) {
    PeakMetrics metrics{};

    size_t left_boundary = peak_index;
    size_t right_boundary = peak_index;

    this->compute_boundaries(
        ptr,
        start,
        end,
        peak_index,
        threshold,
        left_boundary,
        right_boundary
    );

    metrics.width = static_cast<double>(right_boundary - left_boundary + 1);

    double area = 0.0;
    for (size_t index = left_boundary; index <= right_boundary; ++index) {
        area += ptr[index];
    }

    metrics.area = area;

    return metrics;
}


void BasePeakLocator::sort_peaks_descending(std::vector<PeakData>& peaks) {
    std::sort(
        peaks.begin(),
        peaks.end(),
        [](const PeakData& left_peak, const PeakData& right_peak) {
            return left_peak.value > right_peak.value;
        }
    );
}


void BasePeakLocator::compute_boundaries(
    const double* ptr,
    size_t start,
    size_t end,
    size_t peak_index,
    double threshold,
    size_t& left_boundary,
    size_t& right_boundary
) {
    if (ptr == nullptr) {
        throw std::runtime_error("Input pointer must not be null.");
    }

    if (end <= start) {
        throw std::runtime_error("Invalid interval: end must be greater than start.");
    }

    if (peak_index < start || peak_index >= end) {
        throw std::runtime_error("peak_index must lie inside [start, end).");
    }

    if (threshold < 0.0) {
        throw std::runtime_error("threshold must be non negative.");
    }

    const double peak_value = ptr[peak_index];
    const double threshold_value = threshold * peak_value;

    left_boundary = peak_index;
    while (
        left_boundary > start &&
        ptr[left_boundary - 1] >= threshold_value
    ) {
        --left_boundary;
    }

    right_boundary = peak_index;
    while (
        right_boundary + 1 < end &&
        ptr[right_boundary + 1] >= threshold_value
    ) {
        ++right_boundary;
    }
}


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


SegmentedMetricDictionary BasePeakLocator::run_segmented_signals(
    const SegmentedSignalDictionary& segmented_signals
) {
    SegmentedMetricDictionary output_dictionary;

    for (const auto& [segment_id, channel_dictionary] : segmented_signals) {
        std::unordered_map<std::string, MetricDictionary> segment_output_dictionary;

        for (const auto& [channel_name, signal_vector] : channel_dictionary) {
            segment_output_dictionary[channel_name] = this->get_metrics(signal_vector);
        }

        output_dictionary[segment_id] = segment_output_dictionary;
    }

    return output_dictionary;
}


void BasePeakLocator::initialize_output_vectors() {
    this->peak_indices.assign(this->max_number_of_peaks, this->padding_value);
    this->peak_heights.assign(this->max_number_of_peaks, static_cast<double>(this->padding_value));
    this->peak_widths.assign(this->max_number_of_peaks, static_cast<double>(this->padding_value));
    this->peak_areas.assign(this->max_number_of_peaks, static_cast<double>(this->padding_value));
}


SlidingWindowPeakLocator::SlidingWindowPeakLocator(
    int window_size,
    int window_step,
    int max_number_of_peaks,
    int padding_value,
    bool compute_width,
    bool compute_area,
    double threshold
)
    : BasePeakLocator(compute_width, compute_area, padding_value, max_number_of_peaks),
      window_size(window_size),
      threshold(threshold)
{
    if (this->window_size <= 0) {
        throw std::runtime_error("window_size must be strictly positive.");
    }

    if (this->threshold < 0.0) {
        throw std::runtime_error("threshold must be non negative.");
    }

    this->window_step = (window_step == -1) ? this->window_size : window_step;

    if (this->window_step <= 0) {
        throw std::runtime_error("window_step must be strictly positive.");
    }
}


void SlidingWindowPeakLocator::compute(const std::vector<double>& signal) {
    if (signal.empty()) {
        throw std::runtime_error("signal must not be empty.");
    }

    const size_t number_of_samples = signal.size();

    std::vector<PeakData> peaks;
    peaks.reserve(
        (number_of_samples + static_cast<size_t>(this->window_step) - 1) /
        static_cast<size_t>(this->window_step)
    );

    for (size_t start = 0; start < number_of_samples; start += static_cast<size_t>(this->window_step)) {
        const size_t end = std::min(start + static_cast<size_t>(this->window_size), number_of_samples);

        if (end <= start) {
            continue;
        }

        const size_t local_peak_index = this->find_local_peak(signal.data(), start, end);
        const double peak_value = signal[local_peak_index];

        double width = static_cast<double>(this->padding_value);
        double area = static_cast<double>(this->padding_value);

        if (this->compute_width || this->compute_area) {
            const PeakMetrics metrics = this->compute_segment_metrics(
                signal.data(),
                start,
                end,
                local_peak_index,
                this->threshold
            );

            if (this->compute_width) {
                width = metrics.width;
            }

            if (this->compute_area) {
                area = metrics.area;
            }
        }

        peaks.emplace_back(
            static_cast<int>(local_peak_index),
            peak_value,
            width,
            area
        );
    }

    this->sort_peaks_descending(peaks);
    this->initialize_output_vectors();

    const size_t number_of_output_peaks = std::min(
        static_cast<size_t>(this->max_number_of_peaks),
        peaks.size()
    );

    for (size_t index = 0; index < number_of_output_peaks; ++index) {
        this->peak_indices[index] = peaks[index].index;
        this->peak_heights[index] = peaks[index].value;

        if (this->compute_width) {
            this->peak_widths[index] = peaks[index].width;
        }

        if (this->compute_area) {
            this->peak_areas[index] = peaks[index].area;
        }
    }
}


GlobalPeakLocator::GlobalPeakLocator(
    int max_number_of_peaks,
    int padding_value,
    bool compute_width,
    bool compute_area,
    double threshold
)
    : BasePeakLocator(compute_width, compute_area, padding_value, max_number_of_peaks),
      threshold(threshold)
{
    if (this->threshold < 0.0) {
        throw std::runtime_error("threshold must be non negative.");
    }
}


void GlobalPeakLocator::compute(const std::vector<double>& signal) {
    if (signal.empty()) {
        throw std::runtime_error("signal must not be empty.");
    }

    const size_t global_peak_index = this->find_local_peak(signal.data(), 0, signal.size());

    double width = static_cast<double>(this->padding_value);
    double area = static_cast<double>(this->padding_value);

    if (this->compute_width || this->compute_area) {
        const PeakMetrics metrics = this->compute_segment_metrics(
            signal.data(),
            0,
            signal.size(),
            global_peak_index,
            this->threshold
        );

        if (this->compute_width) {
            width = metrics.width;
        }

        if (this->compute_area) {
            area = metrics.area;
        }
    }

    this->initialize_output_vectors();

    this->peak_indices[0] = static_cast<int>(global_peak_index);
    this->peak_heights[0] = signal[global_peak_index];

    if (this->compute_width) {
        this->peak_widths[0] = width;
    }

    if (this->compute_area) {
        this->peak_areas[0] = area;
    }
}
