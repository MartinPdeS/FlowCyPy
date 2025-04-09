#include <vector>
#include <algorithm>



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
    inline PeakMetrics compute_segment_metrics(const double* ptr, size_t start, size_t end, size_t peak_index, double threshold) {
        PeakMetrics metrics;
        size_t left_boundary, right_boundary;
        compute_boundaries(ptr, start, end, peak_index, threshold, left_boundary, right_boundary);
        metrics.width = static_cast<double>(right_boundary - left_boundary + 1);

        double area = 0.0;
        for (size_t i = left_boundary; i <= right_boundary; i++)
            area += ptr[i];

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
        pad_height.assign(max_number_of_peaks, padding_value);
        for (size_t i = 0; i < std::min(max_number_of_peaks, num_found); i++) {
            pad_index[i] = peaks[i].first;
            pad_height[i] = peaks[i].second;
        }
    }
}
