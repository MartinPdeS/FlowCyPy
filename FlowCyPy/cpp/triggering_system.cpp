#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include "filter.h"

namespace py = pybind11;

class TriggeringSystem {
    /**
     * @brief Triggered acquisition system.
     * @param signal_map Map of signals for each detector.
     * @param time_map Map of time values for each detector.
     * @param trigger_detector_name Name of the detector to use for triggering.
     * @param threshold Threshold value for trigger detection.
     * @param pre_buffer Number of samples before the trigger (default 64).
     * @param post_buffer Number of samples after the trigger (default 64).
     * @param max_triggers Maximum number of triggers to process (-1 for unlimited).
     */
public:
    std::string scheme;
    std::map<std::string, py::array_t<double>> signal_map;
    std::map<std::string, py::array_t<double>> time_map;
    std::string trigger_detector_name;
    double threshold;
    int pre_buffer;
    int post_buffer;
    int max_triggers;

    TriggeringSystem(
        const std::string &scheme,
        const std::map<std::string, py::array_t<double>> &signal_map,
        const std::map<std::string, py::array_t<double>> &time_map,
        const std::string &trigger_detector_name,
        const double threshold,
        const int pre_buffer = 64,
        const int post_buffer = 64,
        const int max_triggers = -1)
        : scheme(scheme), signal_map(signal_map), time_map(time_map), trigger_detector_name(trigger_detector_name), threshold(threshold),
        pre_buffer(pre_buffer), post_buffer(post_buffer), max_triggers(max_triggers)
        {}


    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run()
    {
        if (this->scheme == "fixed-window")
            return this->run_fixed_window();
        else if (this->scheme == "dynamic")
            return this->run_dynamic();
        else
            PyErr_WarnEx(PyExc_UserWarning, "Invalid triggering scheme, options are: 'fixed-window' or 'dynamic'.", 1);
    }
    /**
     * @brief Fixed-window triggered acquisition.
     *
     * This is the original fixed-window method:
     * It finds threshold crossings and then applies fixed pre- and post-buffer constraints.
     *
     * @return Tuple of (times, signals, detector names, segment IDs).
     */
    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_fixed_window()
    {
        // Validate trigger detector existence.
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
        validate_detector_existence(time_map, trigger_detector_name, "Trigger detector not found in time map.");

        // Get trigger detector data.
        auto trigger_signal_array = signal_map.at(trigger_detector_name);
        auto trigger_time_array = time_map.at(trigger_detector_name);

        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);

        // (Optional baseline restoration could be done here.)
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);

        // Find trigger indices using fixed-window logic.
        std::vector<int> trigger_indices = find_trigger_indices(trigger_signal.data(), n_trigger, threshold);

        // Apply buffer constraints.
        std::vector<std::pair<int, int>> valid_triggers = apply_buffer_constraints(
            trigger_indices,
            pre_buffer - 1,
            post_buffer,
            static_cast<int>(n_trigger),
            max_triggers
        );

        if (valid_triggers.empty())
        {
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found after baseline restoration. Returning empty arrays.", 1);
            return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
        }

        // Extract and return signal segments.
        return extract_signal_segments(signal_map, time_map, valid_triggers);
    }

    /**
     * @brief Dynamic triggered acquisition.
     *
     * In the dynamic mode:
     *  - When the signal crosses the threshold, the pre_buffer points before are included.
     *  - The window extends until the signal falls below threshold.
     *  - post_buffer points after the falling edge are included.
     *  - This results in a total window length of pre_buffer + width + post_buffer - 1.
     *  - Overlapping triggers are not allowed.
     *
     * @return Tuple of (times, signals, detector names, segment IDs).
     */
    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_dynamic()
    {
        // Validate trigger detector existence.
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
        validate_detector_existence(time_map, trigger_detector_name, "Trigger detector not found in time map.");

        // Get trigger detector data.
        auto trigger_signal_array = signal_map.at(trigger_detector_name);
        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);

        // (Optional baseline restoration could be done here.)
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);

        std::vector<std::pair<int, int>> valid_triggers;
        int last_end = -1;

        // Traverse the signal for dynamic triggering.
        for (size_t i = 1; i < n_trigger; ++i) {
            // Detect rising edge.
            if (trigger_signal[i - 1] <= threshold && trigger_signal[i] > threshold) {
                int start = static_cast<int>(i) - pre_buffer;
                if (start < 0)
                    start = 0;
                // Determine the width: continue while above threshold.
                size_t j = i;
                while (j < n_trigger && trigger_signal[j] > threshold)
                    j++;
                int width = static_cast<int>(j - i);
                // End index: last index above threshold plus post_buffer.
                int end = static_cast<int>(j) - 1 + post_buffer;
                if (end >= static_cast<int>(n_trigger))
                    end = static_cast<int>(n_trigger) - 1;

                // Avoid overlapping triggers.
                if (start > last_end) {
                    valid_triggers.emplace_back(start, end);
                    last_end = end;
                }

                // Respect max triggers if set.
                if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                    break;

                // Skip ahead to j to avoid multiple detections within the same trigger.
                i = j;
            }
        }

        if (valid_triggers.empty())
        {
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found in dynamic mode. Returning empty arrays.", 1);
            return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
        }

        // Extract and return signal segments.
        return extract_signal_segments(signal_map, time_map, valid_triggers);
    }

private:
    // Helper function: Validate that the detector exists in the map.
    static void validate_detector_existence(
        const std::map<std::string, py::array_t<double>> &map,
        const std::string &detector_name,
        const std::string &error_message)
    {
        if (map.find(detector_name) == map.end())
            throw std::runtime_error(error_message);
    }

    // Helper function: Find trigger indices based on fixed-window threshold crossing.
    static std::vector<int> find_trigger_indices(
        double *trigger_signal,
        size_t signal_size,
        double threshold)
    {
        std::vector<int> trigger_indices;
        for (size_t i = 1; i < signal_size; ++i)
            if (trigger_signal[i - 1] <= threshold && trigger_signal[i] > threshold)
                trigger_indices.push_back(i - 1);
        return trigger_indices;
    }

    // Helper function: Apply pre- and post-buffer constraints (fixed-window mode).
    static std::vector<std::pair<int, int>> apply_buffer_constraints(
        const std::vector<int> &trigger_indices,
        int pre_buffer,
        int post_buffer,
        int signal_size,
        int max_triggers)
    {
        std::vector<std::pair<int, int>> valid_triggers;
        int last_end = -1;
        for (int idx : trigger_indices)
        {
            int start = idx - pre_buffer;
            int end = idx + post_buffer;
            if (start < 0 || end >= signal_size)
                continue;
            if (start > last_end)
            {
                valid_triggers.emplace_back(start, end);
                last_end = end;
            }
            if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                break;
        }
        return valid_triggers;
    }

    // Helper function: Extract signal segments given valid trigger indices.
    static std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>>
    extract_signal_segments(
        const std::map<std::string, py::array_t<double>> &signal_map,
        const std::map<std::string, py::array_t<double>> &time_map,
        const std::vector<std::pair<int, int>> &valid_triggers)
    {
        std::vector<double> times_out, signals_out;
        std::vector<std::string> detectors_out;
        std::vector<int> segment_ids_out;
        for (const auto &[detector_name, signal_array] : signal_map)
        {
            auto time_array = time_map.at(detector_name);
            py::buffer_info signal_buf = signal_array.request();
            py::buffer_info time_buf = time_array.request();
            if (signal_buf.ndim != 1 || time_buf.ndim != 1)
                throw std::runtime_error("Signal and time arrays must be 1D");
            size_t signal_size = signal_buf.shape[0];
            double *signal_ptr = static_cast<double *>(signal_buf.ptr);
            double *time_ptr = static_cast<double *>(time_buf.ptr);
            size_t segment_id = 0;
            for (const auto &[start, end] : valid_triggers)
            {
                for (int i = start; i <= end; ++i)
                {
                    if (i >= static_cast<int>(signal_size))
                        break;
                    times_out.push_back(time_ptr[i]);
                    signals_out.push_back(signal_ptr[i]);
                    detectors_out.push_back(detector_name);
                    segment_ids_out.push_back(segment_id);
                }
                segment_id++;
            }
        }
        py::list detector_list;
        for (const auto &detector : detectors_out)
            detector_list.append(detector);
        return std::make_tuple(
            py::array_t<double>(times_out.size(), times_out.data()),
            py::array_t<double>(signals_out.size(), signals_out.data()),
            detector_list,
            py::array_t<int>(segment_ids_out.size(), segment_ids_out.data()));
    }
};

PYBIND11_MODULE(triggering_system, module) {
    module.doc() = "Module for efficient signal processing and triggered acquisition using C++";
    py::class_<TriggeringSystem>(module, "TriggeringSystem")
        .def(py::init<const std::string&, const std::map<std::string, py::array_t<double>>&, const std::map<std::string, py::array_t<double>>&,
            const std::string&, const double, const int, const int, const int>(),
            py::arg("scheme"),
            py::arg("signal_map"),
            py::arg("time_map"),
            py::arg("trigger_detector_name"),
            py::arg("threshold"),
            py::arg("pre_buffer") = 64,
            py::arg("post_buffer") = 64,
            py::arg("max_triggers") = -1
        )
        .def("run", &TriggeringSystem::run, "Executes fixed-window triggered acquisition analysis.")
        .def("run_dynamic", &TriggeringSystem::run_dynamic, "Executes dynamic triggered acquisition analysis.");
}
