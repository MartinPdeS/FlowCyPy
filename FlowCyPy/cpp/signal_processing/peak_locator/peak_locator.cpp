#include "peak_locator.h"


// ----------- Implementation of BasePeakLocator -----------------
BasePeakLocator::BasePeakLocator(bool compute_width, bool compute_area, int padding_value, int max_number_of_peaks)
: compute_width(compute_width), compute_area(compute_area), padding_value(padding_value), max_number_of_peaks(max_number_of_peaks)
{}

size_t BasePeakLocator::find_local_peak(const double* ptr, size_t start, size_t end) {
    size_t local_peak_index = start;
    double max_val = ptr[start];
    for (size_t i = start; i < end; i++) {
        if (ptr[i] > max_val) {
            max_val = ptr[i];
            local_peak_index = i;
        }
    }
    return local_peak_index;
}

PeakMetrics BasePeakLocator::compute_segment_metrics(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold) {
    PeakMetrics metrics;
    size_t left_boundary, right_boundary;
    this->compute_boundaries(ptr, start, end, peak_index, threshold, left_boundary, right_boundary);
    metrics.width = static_cast<double>(right_boundary - left_boundary + 1);

    double area = 0.0;
    for (size_t i = left_boundary; i <= right_boundary; i++)
        area += ptr[i];

    metrics.area = area;
    return metrics;
}

void BasePeakLocator::pad_peaks(const std::vector<std::pair<int, double>>& peaks, size_t max_number_of_peaks, int padding_value, std::vector<int>& pad_index, std::vector<double>& pad_height) {
    size_t num_found = peaks.size();
    pad_index.assign(max_number_of_peaks, padding_value);
    pad_height.assign(max_number_of_peaks, padding_value);
    for (size_t i = 0; i < std::min(max_number_of_peaks, num_found); i++) {
        pad_index[i] = peaks[i].first;
        pad_height[i] = peaks[i].second;
    }
}


void BasePeakLocator::sort_peaks_descending(std::vector<PeakData>& peaks) {
    std::sort(peaks.begin(), peaks.end(), [](const PeakData &a, const PeakData &b) {
        return a.value > b.value;
    });
}

void BasePeakLocator::sort_peaks_descending(std::vector<std::pair<int, double>>& peaks) {
    std::sort(
        peaks.begin(),
        peaks.end(),
        [](const std::pair<int, double>& a, const std::pair<int, double>& b) { return a.second > b.second;}
    );
}

void BasePeakLocator::compute_boundaries(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold, size_t &left_boundary, size_t &right_boundary)
{
    double peak_value = ptr[peak_index];
    double thresh_val = threshold * peak_value;

    // Find left boundary.
    size_t left = peak_index;
    while (left > start && ptr[left] >= thresh_val)
        left--;
    left_boundary = left + 1;

    // Find right boundary.
    size_t right = peak_index;
    while (right < end - 1 && ptr[right] >= thresh_val)
        right++;
    right_boundary = (right > 0 ? right - 1 : 0);
}


std::vector<double> BasePeakLocator::get_metric_py(const std::string &metric_name){
    if (metric_name == "Index")
        return std::vector<double>(this->peak_indices.begin(), this->peak_indices.end());
    if (metric_name == "Height")
        return this->peak_heights;
    if (metric_name == "Width")
        return this->peak_widths;
    if (metric_name == "Area")
        return this->peak_areas;

    throw pybind11::value_error(std::string("No valid metric chosen: ") + metric_name);
}


std::unordered_map<std::string, std::vector<double>>
BasePeakLocator::get_metrics(const std::vector<double> &array){
    this->compute(array);
    std::unordered_map<std::string, std::vector<double>> output;

    output["Index"] = std::vector<double>(this->peak_indices.begin(), this->peak_indices.end());

    output["Height"] = this->peak_heights;

    if (this->compute_area)
        output["Area"] = this->peak_areas;

    if (this->compute_width)
        output["Width"] = this->peak_widths;

    return output;
}


// ----------- Implementation of the SlidingWindowPeakLocator -----------------
SlidingWindowPeakLocator::SlidingWindowPeakLocator(int window_size, int window_step, int max_number_of_peaks, int padding_value, bool compute_width, bool compute_area, double threshold)
:   BasePeakLocator(compute_width, compute_area, padding_value, max_number_of_peaks), window_size(window_size), threshold(threshold)
{
    this->window_step = (window_step == -1) ? window_size : window_step;
}

void SlidingWindowPeakLocator::compute(const std::vector<double> &signal) {
    if (signal.empty())
        throw std::runtime_error("Input array must be 1D.");

    size_t num_cols = signal.size();

    std::vector<PeakData> peaks;

    // Process each window using window_step.
    // This loop covers the entire signal even if the last window is incomplete.
    for (size_t start = 0; start < num_cols; start += window_step) {
        size_t end = std::min(start + static_cast<size_t>(window_size), num_cols);

        if (end <= start)
            continue;

        // Find the local maximum in this window.
        size_t local_peak_index = this->find_local_peak(signal.data(), start, end);
        double peak_value = signal[local_peak_index];

        double
            width = padding_value,
            area = padding_value;

        // Optionally compute width and area using the helper function.
        if (compute_width || compute_area) {
            PeakMetrics metrics = this->compute_segment_metrics(signal.data(), start, end, local_peak_index, threshold);
            if (compute_width)
                width = metrics.width;

            if (compute_area)
                area = metrics.area;

        }
        peaks.emplace_back(static_cast<int>(local_peak_index), peak_value, width, area);
    }

    // Sort peaks by amplitude in descending order.
    this->sort_peaks_descending(peaks);

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

// ----------- Implementation of the GlobalPeakLocator -----------------
GlobalPeakLocator::GlobalPeakLocator( int max_number_of_peaks, int padding_value, bool compute_width, bool compute_area, double threshold)
:   BasePeakLocator(compute_width, compute_area, padding_value, max_number_of_peaks), threshold(threshold)
{}

void GlobalPeakLocator::compute(const std::vector<double> &signal) {
    if (signal.empty())
        throw std::runtime_error("Input array must be 1D.");

    size_t num_cols = signal.size();

    // Find the global maximum using find_local_peak.
    size_t global_peak_index = this->find_local_peak(signal.data(), 0, num_cols);
    double
        width = padding_value,
        area = padding_value;

    // Use the helper function to compute width and area if requested.
    if (compute_width || compute_area) {
        PeakMetrics metrics = this->compute_segment_metrics(signal.data(), 0, num_cols, global_peak_index, threshold);

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
    peak_heights[0] = signal[global_peak_index];

    // Prepare width and area vectors for output.
    if (compute_width)
        this->peak_widths[0] = width;

    if (compute_area)
        this->peak_areas[0] = area;
}
