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

    this->initialize_output_vectors();
}


void BasePeakLocator::validate_input_signal(const std::vector<double>& array) const {
    if (array.empty()) {
        throw std::runtime_error("signal must not be empty.");
    }
}


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


PeakMetrics BasePeakLocator::compute_segment_metrics(
    const double* ptr,
    size_t start,
    size_t end,
    size_t peak_index,
    double threshold
) const {
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


void BasePeakLocator::sort_peaks_descending(std::vector<PeakData>& peaks) const {
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
) const {
    struct Task {
        int segment_id;
        std::string channel_name;
        const std::vector<double>* signal_vector;
    };

    struct TaskResult {
        int segment_id;
        std::string channel_name;
        MetricDictionary metrics;
    };

    std::vector<Task> tasks;
    tasks.reserve(segmented_signals.size() * 4);

    for (const auto& [segment_id, channel_dictionary] : segmented_signals) {
        for (const auto& [channel_name, signal_vector] : channel_dictionary) {
            tasks.push_back(Task{
                segment_id,
                channel_name,
                &signal_vector
            });
        }
    }

    std::vector<TaskResult> results(tasks.size());

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (int task_index = 0; task_index < static_cast<int>(tasks.size()); ++task_index) {
        const Task& task = tasks[static_cast<size_t>(task_index)];

        results[static_cast<size_t>(task_index)] = TaskResult{
            task.segment_id,
            task.channel_name,
            this->compute_metric_dictionary(*task.signal_vector)
        };
    }

    SegmentedMetricDictionary output_dictionary;

    for (TaskResult& result : results) {
        output_dictionary[result.segment_id][result.channel_name] =
            std::move(result.metrics);
    }

    return output_dictionary;
}


SegmentedMetricDictionary BasePeakLocator::run_flat_segmented_signals(
    const std::vector<int>& segment_ids,
    const FlatSignalDictionary& flat_signals
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

    return this->run_segmented_signals(segmented_signals);
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
      window_step((window_step == -1) ? window_size : window_step),
      threshold(threshold)
{
    if (this->window_size <= 0) {
        throw std::runtime_error("window_size must be strictly positive.");
    }

    if (this->threshold < 0.0) {
        throw std::runtime_error("threshold must be non negative.");
    }

    if (this->window_step <= 0) {
        throw std::runtime_error("window_step must be strictly positive.");
    }
}


std::vector<PeakData> SlidingWindowPeakLocator::locate_peaks(
    const std::vector<double>& signal
) const {
    this->validate_input_signal(signal);

    const size_t number_of_samples = signal.size();

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

    return peaks;
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


std::vector<PeakData> GlobalPeakLocator::locate_peaks(
    const std::vector<double>& signal
) const {
    this->validate_input_signal(signal);

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

    return std::vector<PeakData>{
        PeakData(
            static_cast<int>(global_peak_index),
            signal[global_peak_index],
            width,
            area
        )
    };
}
