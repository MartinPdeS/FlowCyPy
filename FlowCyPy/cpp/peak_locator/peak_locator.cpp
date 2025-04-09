#include "peak_locator.h"
#include "peak_utils.h"
#include <limits>

namespace py = pybind11;


void SlidingWindowPeakLocator::compute(const py::buffer signal) {
    if (signal.request().ndim != 1)
        throw std::runtime_error("Input array must be 1D.");

    auto buffer = signal.request();
    double* ptr = static_cast<double*>(buffer.ptr);
    size_t num_cols = buffer.shape[0];

    std::vector<PeakUtils::PeakData> peaks;

    // Process each window using window_step.
    // This loop covers the entire signal even if the last window is incomplete.
    for (size_t start = 0; start < num_cols; start += window_step) {
        size_t end = std::min(start + static_cast<size_t>(window_size), num_cols);
        if (end <= start)
            continue;

        // Find the local maximum in this window.
        size_t local_peak_index = PeakUtils::find_local_peak(ptr, start, end);
        double peak_value = ptr[local_peak_index];

        double
            width = padding_value,
            area = padding_value;

        // Optionally compute width and area using the helper function.
        if (compute_width || compute_area) {
            PeakUtils::PeakMetrics metrics = PeakUtils::compute_segment_metrics(ptr, start, end, local_peak_index, threshold);
            if (compute_width)
                width = metrics.width;

            if (compute_area)
                area = metrics.area;

        }
        peaks.emplace_back(static_cast<int>(local_peak_index), peak_value, width, area);
    }

    // Sort peaks by amplitude in descending order.
    PeakUtils::sort_peaks_descending(peaks);

    // Pad the results to a fixed size.
    size_t number_of_windows = peaks.size();
    peak_indices = std::vector<int>(max_number_of_peaks, padding_value);
    peak_heights = std::vector<double>(max_number_of_peaks, padding_value);
    peak_widths = std::vector<double>(max_number_of_peaks, padding_value);
    peak_areas = std::vector<double>(max_number_of_peaks, padding_value);

    for (size_t i = 0; i < std::min(static_cast<size_t>(max_number_of_peaks), number_of_windows); i++) {
        this->peak_indices[i] = peaks[i].index;
        this->peak_heights[i] = peaks[i].value;

        if (compute_width)
            this->peak_widths[i] = peaks[i].width;

        if (compute_area)
            this->peak_areas[i] = peaks[i].area;
    }
}

void GlobalPeakLocator::compute(const py::buffer signal) {
    if (signal.request().ndim != 1)
        throw std::runtime_error("Input array must be 1D.");

    auto buffer = signal.request();
    double* ptr = static_cast<double*>(buffer.ptr);
    size_t num_cols = buffer.shape[0];

    // Find the global maximum using PeakUtils::find_local_peak.
    size_t global_peak_index = PeakUtils::find_local_peak(ptr, 0, num_cols);
    double
        width = padding_value,
        area = padding_value;

    // Use the helper function to compute width and area if requested.
    if (compute_width || compute_area) {
        PeakUtils::PeakMetrics metrics = PeakUtils::compute_segment_metrics(ptr, 0, num_cols, global_peak_index, threshold);

        if (compute_width)
            width = metrics.width;

        if (compute_area)
            area = metrics.area;

    }

    peak_indices = std::vector<int>(max_number_of_peaks, padding_value);
    peak_heights = std::vector<double>(max_number_of_peaks, padding_value);
    peak_widths = std::vector<double>(max_number_of_peaks, padding_value);
    peak_areas = std::vector<double>(max_number_of_peaks, padding_value);

    peak_indices[0] = global_peak_index;
    peak_heights[0] = ptr[global_peak_index];

    // Prepare width and area vectors for output.
    if (compute_width)
        this->peak_widths[0] = width;

    if (compute_area)
        this->peak_areas[0] = area;
}


