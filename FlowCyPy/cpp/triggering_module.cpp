#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <algorithm>
#include <stdexcept>

namespace py = pybind11;

/**
 * @brief Execute triggered acquisition analysis for signal data.
 *
 * @param signal_map Dictionary of signals mapped to detector names.
 * @param time_map Dictionary of time values for each detector.
 * @param threshold Trigger threshold.
 * @param pre_buffer Number of points before the trigger.
 * @param post_buffer Number of points after the trigger.
 * @param max_triggers Maximum number of triggers to process (-1 = unlimited).
 * @return A tuple of NumPy arrays (times, signals, detector labels, segment IDs).
 */
std::tuple<py::array_t<double>, py::array_t<double>, py::array_t<int>, py::array_t<int>> run_triggering(
    std::map<std::string, py::array_t<double>> signal_map,
    std::map<std::string, py::array_t<double>> time_map,
    double threshold,
    int pre_buffer = 64,
    int post_buffer = 64,
    int max_triggers = -1) // -1 means unlimited
{
    std::vector<double> times_out, signals_out;
    std::vector<int> detectors_out, segment_ids_out;

    int global_segment_id = 0; // Unique segment index across all detectors

    for (const auto &[detector_name, signal_array] : signal_map)
    {
        auto time_array = time_map.at(detector_name); // Fetch corresponding time data

        py::buffer_info signal_buf = signal_array.request();
        py::buffer_info time_buf = time_array.request();

        if (signal_buf.ndim != 1 || time_buf.ndim != 1)
            throw std::runtime_error("Signal and time arrays must be 1D");

        size_t n = signal_buf.shape[0];
        double *signal_ptr = static_cast<double *>(signal_buf.ptr);
        double *time_ptr = static_cast<double *>(time_buf.ptr);

        // Find trigger points
        std::vector<int> trigger_indices;
        for (size_t i = 1; i < n; ++i)
        {
            if (signal_ptr[i - 1] <= threshold && signal_ptr[i] > threshold)
                trigger_indices.push_back(i - 1);
        }

        // Apply pre/post buffer and suppress overlapping triggers
        std::vector<std::pair<int, int>> valid_triggers;
        int last_end = -1;
        for (int idx : trigger_indices)
        {
            int start = std::max(0, idx - pre_buffer);
            int end = std::min(static_cast<int>(n - 1), idx + post_buffer);
            if (start > last_end)
            {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }
            if (max_triggers > 0 && valid_triggers.size() >= (size_t)max_triggers)
                break;
        }

        // Extract signal segments
        for (const auto &[start, end] : valid_triggers)
        {
            for (int i = start; i <= end; ++i)
            {
                times_out.push_back(time_ptr[i]);
                signals_out.push_back(signal_ptr[i]);
                detectors_out.push_back(global_segment_id); // Assign segment ID
                segment_ids_out.push_back(global_segment_id);
            }
            global_segment_id++; // Increment segment ID for the next one
        }
    }

    if (times_out.empty())
    {
        PyErr_WarnEx(PyExc_UserWarning, "No signals met the trigger criteria. Consider adjusting the threshold.", 1);
    }

    // Convert vectors to NumPy arrays
    return std::make_tuple(
        py::array_t<double>(times_out.size(), times_out.data()),
        py::array_t<double>(signals_out.size(), signals_out.data()),
        py::array_t<int>(detectors_out.size(), detectors_out.data()),
        py::array_t<int>(segment_ids_out.size(), segment_ids_out.data()));
}
