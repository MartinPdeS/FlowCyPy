#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <tuple>
#include <algorithm>
#include <stdexcept>

namespace py = pybind11;

/**
 * @brief Calculate the start and end indices for triggered segments.
 *
 * This function computes rising-edge indices from a 1D signal array where the signal crosses
 * a specified threshold. It then applies pre- and post-buffer clipping and suppresses overlapping
 * triggers to avoid retriggering within an active buffer period.
 *
 * @param signal A 1D numpy array of doubles representing the signal.
 * @param threshold The threshold value for triggering.
 * @param pre_buffer Number of samples to include before the trigger point (default 64).
 * @param post_buffer Number of samples to include after the trigger point (default 64).
 * @return A tuple containing two numpy arrays (start_indices, end_indices).
 * @throws std::runtime_error if the input signal is not 1-dimensional.
 */
std::tuple<py::array_t<int>, py::array_t<int>> get_trigger_indices(
    py::array_t<double> signal,
    double threshold,
    int pre_buffer = 64,
    int post_buffer = 64)
{
    // Request a contiguous buffer from the input signal.
    auto buf = signal.request();
    if (buf.ndim != 1) {
        throw std::runtime_error("Input signal must be 1-dimensional");
    }
    size_t n = buf.shape[0];
    double* ptr = static_cast<double*>(buf.ptr);

    // Compute trigger_signal: true if signal value > threshold
    std::vector<bool> trigger_signal(n, false);
    for (size_t i = 0; i < n; i++) {
        trigger_signal[i] = (ptr[i] > threshold);
    }

    // Find rising edges: where the difference is 1 (i.e., transition from false to true)
    std::vector<int> crossings;
    for (size_t i = 1; i < n; i++) {
        if (!trigger_signal[i - 1] && trigger_signal[i]) {
            // Mimic np.where(np.diff(...)==1) by storing index i-1
            crossings.push_back(static_cast<int>(i - 1));
        }
    }

    // Compute start and end indices with buffers
    std::vector<int> start_indices, end_indices;
    for (int c : crossings) {
        int start_idx = std::max(0, c - pre_buffer);
        int end_idx = std::min(static_cast<int>(n - 1), c + post_buffer);
        start_indices.push_back(start_idx);
        end_indices.push_back(end_idx);
    }

    // Suppress retriggering: remove overlapping segments
    std::vector<int> suppressed_start, suppressed_end;
    int last_end = -1;
    for (size_t i = 0; i < start_indices.size(); i++) {
        if (start_indices[i] > last_end) {
            suppressed_start.push_back(start_indices[i]);
            suppressed_end.push_back(end_indices[i]);
            last_end = end_indices[i];
        }
    }

    // Create numpy arrays to return
    auto np_start = py::array_t<int>(suppressed_start.size());
    auto np_end = py::array_t<int>(suppressed_end.size());
    auto buf_start = np_start.request();
    auto buf_end = np_end.request();
    int* start_ptr = static_cast<int*>(buf_start.ptr);
    int* end_ptr = static_cast<int*>(buf_end.ptr);
    for (size_t i = 0; i < suppressed_start.size(); i++) {
        start_ptr[i] = suppressed_start[i];
    }
    for (size_t i = 0; i < suppressed_end.size(); i++) {
        end_ptr[i] = suppressed_end[i];
    }

    return std::make_tuple(np_start, np_end);
}

