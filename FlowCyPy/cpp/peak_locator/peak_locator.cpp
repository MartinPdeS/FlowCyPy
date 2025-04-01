#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <algorithm>
#include <limits>

namespace py = pybind11;


// Helper namespace with common peak processing functions.
namespace PeakUtils {

    // Structure to hold computed metrics for a peak.
    struct PeakMetrics {
        double width;
        double area;
    };


    // Sorts a vector of PeakData in descending order by the peak's value.
    struct PeakData {
        int index;
        double value;
        double width;  // Will be NaN if not computed.
        double area;   // Will be NaN if not computed.

        PeakData(int idx, double val, double w = std::numeric_limits<double>::quiet_NaN(), double a = std::numeric_limits<double>::quiet_NaN())
            : index(idx), value(val), width(w), area(a) {}
    };

    inline void sort_peaks_descending(std::vector<PeakData>& peaks) {
        std::sort(peaks.begin(), peaks.end(), [](const PeakData &a, const PeakData &b) {
            return a.value > b.value;
        });
    }

    // Finds the index of the local maximum in the given window.
    inline size_t find_local_peak(const double* ptr, size_t start, size_t end) {
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

    // Computes the left and right boundaries for a peak given a threshold.
    inline void compute_boundaries(
        const double* ptr,
        size_t start,
        size_t end,
        size_t peak_index,
        double threshold,
        size_t &left_boundary,
        size_t &right_boundary)
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

    // Computes both the width and area for a given peak.
    inline PeakMetrics compute_peak_metrics(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold) {
        PeakMetrics metrics;
        size_t left_boundary, right_boundary;
        compute_boundaries(ptr, start, end, peak_index, threshold, left_boundary, right_boundary);
        metrics.width = static_cast<double>(right_boundary - left_boundary + 1);

        double area = 0.0;
        for (size_t i = left_boundary; i <= right_boundary; i++) {
        area += ptr[i];
        }
        metrics.area = area;
        return metrics;
    }

    // Sorts a vector of (index, value) pairs in descending order by value.
    inline void sort_peaks_descending(std::vector<std::pair<int, double>>& peaks) {
        std::sort(
            peaks.begin(),
            peaks.end(),
            [](const std::pair<int, double>& a, const std::pair<int, double>& b) { return a.second > b.second;}
        );
    }

    // Pads the given peaks (as (index,value) pairs) to fixed size.
    inline void pad_peaks(const std::vector<std::pair<int, double>>& peaks, size_t max_number_of_peaks, int padding_value, std::vector<int>& pad_index, std::vector<double>& pad_height) {
        size_t num_found = peaks.size();
        pad_index.assign(max_number_of_peaks, padding_value);
        pad_height.assign(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());
        for (size_t i = 0; i < std::min(max_number_of_peaks, num_found); i++) {
            pad_index[i] = peaks[i].first;
            pad_height[i] = peaks[i].second;
        }
    }
}


class SlidingWindowPeakLocator {
    public:
        int window_size;
        int window_step;
        int max_number_of_peaks;
        int padding_value;
        bool compute_width;
        bool compute_area;
        double threshold;

        // If window_step is not provided (or provided as -1), default to window_size.
        SlidingWindowPeakLocator(
            int window_size,
            int window_step = -1,
            int max_number_of_peaks = 5,
            int padding_value = -1,
            bool compute_width = false,
            bool compute_area = false,
            double threshold = 0.5)
            : window_size(window_size), max_number_of_peaks(max_number_of_peaks), padding_value(padding_value),
              compute_width(compute_width), compute_area(compute_area), threshold(threshold)
        {
            this->window_step = (window_step == -1) ? window_size : window_step;
        }

        py::dict operator()(py::array_t<double> input_array) {
            // Ensure the input is 1D.
            if (input_array.ndim() != 1)
                throw std::runtime_error("Input array must be 1D.");

            auto buf = input_array.request();
            double* ptr = static_cast<double*>(buf.ptr);
            size_t num_cols = buf.shape[0];

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

                double width = std::numeric_limits<double>::quiet_NaN();
                double area = std::numeric_limits<double>::quiet_NaN();

                // Optionally compute width and area using the helper function.
                if (compute_width || compute_area) {
                    PeakUtils::PeakMetrics metrics = PeakUtils::compute_peak_metrics(ptr, start, end, local_peak_index, threshold);
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
            size_t num_found = peaks.size();
            std::vector<int> pad_index(max_number_of_peaks, padding_value);
            std::vector<double> pad_height(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());
            std::vector<double> pad_width(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());
            std::vector<double> pad_area(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());

            for (size_t i = 0; i < std::min(static_cast<size_t>(max_number_of_peaks), num_found); i++) {
                pad_index[i] = peaks[i].index;
                pad_height[i] = peaks[i].value;
                if (compute_width)
                    pad_width[i] = peaks[i].width;

                if (compute_area)
                    pad_area[i] = peaks[i].area;
            }

            // Build the output dictionary.
            py::dict result;
            result["Index"] = py::array_t<int>(pad_index.size(), pad_index.data());
            result["Height"] = py::array_t<double>(pad_height.size(), pad_height.data());
            if (compute_width)
                result["Width"] = py::array_t<double>(pad_width.size(), pad_width.data());

            if (compute_area)
                result["Area"] = py::array_t<double>(pad_area.size(), pad_area.data());


            return result;
        }
    };



// GlobalPeakLocator class that uses the PeakUtils helper functions.
class GlobalPeakLocator {
    public:
        int max_number_of_peaks;
        int padding_value;
        bool compute_width;
        bool compute_area;
        double threshold;

        /// Constructor.
        ///
        /// \param max_number_of_peaks Maximum number of peaks to report (only one peak is found here,
        ///                            so additional entries are padded).
        /// \param padding_value        Value used for padding indices when fewer peaks are detected.
        /// \param compute_width        If true, compute the peak's width (number of samples above threshold).
        /// \param compute_area         If true, compute the peak's area (sum of values above threshold).
        /// \param threshold            Fraction of the peak height used to determine boundaries.
        GlobalPeakLocator(
            int max_number_of_peaks = 1,
            int padding_value = -1,
            bool compute_width = false,
            bool compute_area = false,
            double threshold = 0.5)
            : max_number_of_peaks(max_number_of_peaks),
              padding_value(padding_value),
              compute_width(compute_width),
              compute_area(compute_area),
              threshold(threshold)
        {}

        /// Finds the global (largest) peak in a 1D array.
        ///
        /// The function scans the input array to locate the highest value. Optionally, it computes the
        /// width and area of the peak using the given threshold via PeakUtils::compute_peak_metrics.
        /// The results are returned as a dictionary containing fixed-length arrays for the peak index,
        /// height, and optionally width and area.
        ///
        /// \param input_array A 1D NumPy array of doubles representing the signal.
        /// \returns A Python dictionary with the following keys:
        ///          - "Index": An array of length `max_number_of_peaks` with the index of the global peak (padded).
        ///          - "Height": An array of length `max_number_of_peaks` with the peak value (padded).
        ///          - "Width": (optional) The computed width, if `compute_width` is true.
        ///          - "Area": (optional) The computed area, if `compute_area` is true.
        py::dict operator()(py::array_t<double> input_array) {
            // Validate input dimension.
            if (input_array.ndim() != 1)
                throw std::runtime_error("Input array must be 1D.");

            auto buf = input_array.request();
            double* ptr = static_cast<double*>(buf.ptr);
            size_t num_cols = buf.shape[0];

            // Find the global maximum using PeakUtils::find_local_peak.
            size_t global_peak_index = PeakUtils::find_local_peak(ptr, 0, num_cols);
            double max_val = ptr[global_peak_index];

            double width = std::numeric_limits<double>::quiet_NaN();
            double area = std::numeric_limits<double>::quiet_NaN();

            // Use the helper function to compute width and area if requested.
            if (compute_width || compute_area) {
                PeakUtils::PeakMetrics metrics = PeakUtils::compute_peak_metrics(ptr, 0, num_cols, global_peak_index, threshold);
                if (compute_width) {
                    width = metrics.width;
                }
                if (compute_area) {
                    area = metrics.area;
                }
            }

            // Build a vector of (index, value) pairs for padding.
            std::vector<std::pair<int, double>> peaks;
            peaks.emplace_back(static_cast<int>(global_peak_index), max_val);

            // Sort the peaks (trivial here, but for consistency).
            PeakUtils::sort_peaks_descending(peaks);

            // Pad the results to fixed size.
            std::vector<int> pad_index;
            std::vector<double> pad_height;
            PeakUtils::pad_peaks(peaks, max_number_of_peaks, padding_value, pad_index, pad_height);

            // Prepare width and area vectors for output.
            std::vector<double> pad_width(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());
            std::vector<double> pad_area(max_number_of_peaks, std::numeric_limits<double>::quiet_NaN());
            if (compute_width) {
                pad_width[0] = width;
            }
            if (compute_area) {
                pad_area[0] = area;
            }

            // Build the output dictionary.
            py::dict result;
            result["Index"] = py::array_t<int>(pad_index.size(), pad_index.data());
            result["Height"] = py::array_t<double>(pad_height.size(), pad_height.data());
            if (compute_width) {
                result["Width"] = py::array_t<double>(pad_width.size(), pad_width.data());
            }
            if (compute_area) {
                result["Area"] = py::array_t<double>(pad_area.size(), pad_area.data());
            }
            return result;
        }
    };


