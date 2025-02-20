#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <algorithm>
#include <stdexcept>
#include <string>
#include <map>

namespace py = pybind11;

/**
 * @brief Execute triggered acquisition analysis for signal data, using a single detector as the trigger source.
 *
 * @param signal_map Dictionary of signals mapped to detector names.
 * @param time_map Dictionary of time values for each detector.
 * @param trigger_detector_name Detector name on which the trigger applies.
 * @param threshold Trigger threshold.
 * @param pre_buffer Number of points before the trigger.
 * @param post_buffer Number of points after the trigger.
 * @param max_triggers Maximum number of triggers to process (-1 = unlimited).
 * @return A tuple of NumPy arrays and a Python list (times, signals, detector names, segment IDs).
 */
std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_triggering(
    std::map<std::string, py::array_t<double>> signal_map,
    std::map<std::string, py::array_t<double>> time_map,
    const std::string &trigger_detector_name,
    double threshold,
    int pre_buffer = 64,
    int post_buffer = 64,
    int max_triggers = -1) // -1 means unlimited
{
    if (signal_map.find(trigger_detector_name) == signal_map.end())
        throw std::runtime_error("Trigger detector not found in signal map.");

    if (time_map.find(trigger_detector_name) == time_map.end())
        throw std::runtime_error("Trigger detector not found in time map.");

    std::vector<double> times_out, signals_out;
    std::vector<std::string> detectors_out;
    std::vector<int> segment_ids_out;

    // Get the trigger detector's signal and time
    auto trigger_signal_array = signal_map.at(trigger_detector_name);
    auto trigger_time_array = time_map.at(trigger_detector_name);

    py::buffer_info trigger_signal_buf = trigger_signal_array.request();
    py::buffer_info trigger_time_buf = trigger_time_array.request();

    if (trigger_signal_buf.ndim != 1 || trigger_time_buf.ndim != 1)
        throw std::runtime_error("Trigger signal and time arrays must be 1D");

    size_t n_trigger = trigger_signal_buf.shape[0];
    double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);
    double *trigger_time_ptr = static_cast<double *>(trigger_time_buf.ptr);

    // Find trigger points based on the specified detector
    std::vector<int> trigger_indices;
    for (size_t i = 1; i < n_trigger; ++i)
    {
        if (trigger_signal_ptr[i - 1] <= threshold && trigger_signal_ptr[i] > threshold)
            trigger_indices.push_back(i - 1);
    }

    // Apply pre/post buffer and suppress overlapping triggers
    std::vector<std::pair<int, int>> valid_triggers;
    int last_end = -1;
    for (int idx : trigger_indices)
    {
        int start = idx - pre_buffer;
        int end = idx + post_buffer;

        // Reject triggers if full buffer cannot be extracted
        if (start < 0 || end >= static_cast<int>(n_trigger))
            continue; // Skip this trigger

        if (start > last_end) // Ensure no overlapping triggers
        {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }
        if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
            break;
    }

    // If no valid triggers are found, return empty arrays
    if (valid_triggers.empty())
    {
        PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found (buffer too large or no signals met the criteria). Returning empty arrays.", 1);
        return std::make_tuple(
            py::array_t<double>(0), // Empty time array
            py::array_t<double>(0), // Empty signal array
            py::list(),             // Empty detector list
            py::array_t<int>(0)     // Empty segment IDs
        );
    }

    // Apply triggers to all detectors
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

        // Extract signal segments based on the trigger points
        size_t segment_id = 0;
        for (const auto &[start, end] : valid_triggers)
        {

            for (int i = start; i <= end; ++i)
            {
                if (i >= static_cast<int>(n)) // Ensure we don't go out of bounds
                    break;

                times_out.push_back(time_ptr[i]);
                signals_out.push_back(signal_ptr[i]);
                detectors_out.push_back(detector_name);
                segment_ids_out.push_back(segment_id);
            }
            segment_id++; // Increment only once per valid trigger
        }
    }

    // Convert vector of strings to Python list
    py::list detector_list;
    for (const auto &detector : detectors_out)
    {
        detector_list.append(detector);
    }

    // Convert vectors to NumPy arrays
    return std::make_tuple(
        py::array_t<double>(times_out.size(), times_out.data()),
        py::array_t<double>(signals_out.size(), signals_out.data()),
        detector_list,
        py::array_t<int>(segment_ids_out.size(), segment_ids_out.data()));
}
