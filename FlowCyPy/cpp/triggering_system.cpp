#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include "filter.h"
#include <cmath>      // for std::isnan
#include <limits>     // for quiet_NaN

namespace py = pybind11;

class TriggeringSystem {
    /**
     * @brief Triggered acquisition system.
     *
     * The class is now initialized only with parameters.
     * The user must then add a global time array using add_time(py::array_t<double>)
     * and add one or more signals using add_signal(string, py::array_t<double>).
     *
     * Parameters:
     *  - scheme: Triggering scheme ("fixed-window", "dynamic", etc.).
     *  - trigger_detector_name: Name of the detector to use for triggering.
     *  - threshold: Threshold value for trigger detection.
     *  - pre_buffer: Number of samples before the trigger (default 64).
     *  - post_buffer: Number of samples after the trigger (default 64).
     *  - max_triggers: Maximum number of triggers to process (-1 for unlimited).
     *  - lower_threshold: Optional lower threshold; if not provided, uses 'threshold'.
     *  - debounce_enabled: If false, debounce check is skipped entirely.
     *  - min_window_duration: Minimum number of consecutive samples above threshold; set to -1 to disable duration check.
     */
public:
    std::string scheme;
    std::string trigger_detector_name;
    double threshold;
    int pre_buffer;
    int post_buffer;
    int max_triggers;
    double lower_threshold;
    bool debounce_enabled;
    int min_window_duration;

    // The maps will be filled using the add_signal method.
    std::map<std::string, py::array_t<double>> signal_map;
    // For time arrays, the user can add a global one.
    py::array_t<double> global_time;
    // Optionally, a per-detector time map can be supported.
    std::map<std::string, py::array_t<double>> time_map;

    TriggeringSystem(
        const std::string &scheme,
        const std::string &trigger_detector_name,
        const double threshold,
        const double lower_threshold,
        const int pre_buffer,
        const int post_buffer,
        const int max_triggers,
        const bool debounce_enabled,
        const int min_window_duration
    )
        : scheme(scheme), trigger_detector_name(trigger_detector_name), threshold(threshold), lower_threshold(lower_threshold),
          pre_buffer(pre_buffer), post_buffer(post_buffer), max_triggers(max_triggers),
          debounce_enabled(debounce_enabled), min_window_duration(min_window_duration)
    {}

    /**
     * @brief Adds a global time array.
     *
     * This time array will be used for all detectors unless a per-detector time array is provided.
     *
     * @param time The time array as a py::array_t<double>.
     */
    void add_time(const py::array_t<double> &time) {
        global_time = time;
    }

    /**
     * @brief Adds a new signal to the system.
     *
     * @param name The name of the detector/signal.
     * @param signal The signal as a py::array_t<double>.
     */
    void add_signal(const std::string &name, const py::array_t<double> &signal) {
        signal_map[name] = signal;
    }

    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run() {
        if (this->scheme == "fixed-window")
            return this->run_fixed_window();
        else if (this->scheme == "dynamic")
            return this->run_dynamic_single_threshold();
        else if (this->scheme == "dynamic-simple")
            return this->run_dynamic();
        else
            PyErr_WarnEx(PyExc_UserWarning, "Invalid triggering scheme, options are: 'fixed-window', 'dynamic', or 'dynamic-simple'.", 1);
    }

    // Fixed-window triggered acquisition.
    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_fixed_window() {
        // Validate that the trigger detector exists.
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
        // For time, try the per-detector map; if not found, check global_time.
        if (time_map.find(trigger_detector_name) == time_map.end() && global_time.size() == 0)
            throw std::runtime_error("No time array found. Please add a time array using add_time().");

        auto trigger_signal_array = signal_map.at(trigger_detector_name);
        // Use per-detector time if available, otherwise use global_time.
        py::array_t<double> trigger_time_array;
        if (time_map.find(trigger_detector_name) != time_map.end())
            trigger_time_array = time_map.at(trigger_detector_name);
        else
            trigger_time_array = global_time;

        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);

        std::vector<int> trigger_indices = find_trigger_indices(trigger_signal.data(), n_trigger, threshold);
        std::vector<std::pair<int, int>> valid_triggers = apply_buffer_constraints(
            trigger_indices, pre_buffer - 1, post_buffer, static_cast<int>(n_trigger), max_triggers
        );

        if (valid_triggers.empty()) {
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found after baseline restoration. Returning empty arrays.", 1);
            return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
        }
        return extract_signal_segments(signal_map, trigger_time_array, valid_triggers);
    }

    // Simple dynamic triggered acquisition.
    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_dynamic() {
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
        if (time_map.find(trigger_detector_name) == time_map.end() && global_time.size() == 0)
            throw std::runtime_error("No time array found. Please add a time array using add_time().");

        auto trigger_signal_array = signal_map.at(trigger_detector_name);
        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);
        std::vector<std::pair<int, int>> valid_triggers;
        int last_end = -1;

        for (size_t i = 1; i < n_trigger; ++i) {
            if (trigger_signal[i - 1] <= threshold && trigger_signal[i] > threshold) {
                int start = static_cast<int>(i) - pre_buffer;
                if (start < 0)
                    start = 0;
                size_t j = i;
                while (j < n_trigger && trigger_signal[j] > threshold)
                    j++;
                int end = static_cast<int>(j) - 1 + post_buffer;
                if (end >= static_cast<int>(n_trigger))
                    end = static_cast<int>(n_trigger) - 1;
                if (start > last_end) {
                    valid_triggers.emplace_back(start, end);
                    last_end = end;
                }
                if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                    break;
                i = j;
            }
        }

        if (valid_triggers.empty()) {
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found in dynamic mode. Returning empty arrays.", 1);
            return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
        }
        // Use per-detector time if available, otherwise use global_time.
        py::array_t<double> trigger_time_array;
        if (time_map.find(trigger_detector_name) != time_map.end())
            trigger_time_array = time_map.at(trigger_detector_name);
        else
            trigger_time_array = global_time;
        return extract_signal_segments(signal_map, trigger_time_array, valid_triggers);
    }

    // Dynamic triggered acquisition with single threshold (with optional lower_threshold and debounce).
    std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_dynamic_single_threshold() {
        if (std::isnan(lower_threshold)) {
            this->lower_threshold = this->threshold;
        }
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
        if (time_map.find(trigger_detector_name) == time_map.end() && global_time.size() == 0)
            throw std::runtime_error("No time array found. Please add a time array using add_time().");

        auto trigger_signal_array = signal_map.at(trigger_detector_name);
        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);
        std::vector<std::pair<int, int>> valid_triggers;
        int last_end = -1;

        for (size_t i = 1; i < n_trigger; ++i) {
            if (trigger_signal[i - 1] <= this->threshold && trigger_signal[i] > this->threshold) {
                size_t j = i;
                if (debounce_enabled && min_window_duration != -1) {
                    size_t count = 0;
                    while (j < n_trigger && trigger_signal[j] > this->threshold) {
                        ++count;
                        ++j;
                        if (count >= static_cast<size_t>(min_window_duration))
                            break;
                    }
                    if (count < static_cast<size_t>(min_window_duration)) {
                        i = j;
                        continue;
                    }
                } else {
                    while (j < n_trigger && trigger_signal[j] > this->threshold)
                        ++j;
                }
                int start = static_cast<int>(i) - pre_buffer;
                if (start < 0)
                    start = 0;
                size_t k = j;
                while (k < n_trigger && trigger_signal[k] > this->lower_threshold)
                    ++k;
                int end = static_cast<int>(k) - 1 + post_buffer;
                if (end >= static_cast<int>(n_trigger))
                    end = static_cast<int>(n_trigger) - 1;
                if (start > last_end) {
                    valid_triggers.emplace_back(start, end);
                    last_end = end;
                }
                if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
                    break;
                i = k;
            }
        }

        if (valid_triggers.empty()) {
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found in dynamic mode (single threshold). Returning empty arrays.", 1);
            return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
        }
        // Use per-detector time if available, otherwise use global_time.
        py::array_t<double> trigger_time_array;
        if (time_map.find(trigger_detector_name) != time_map.end())
            trigger_time_array = time_map.at(trigger_detector_name);
        else
            trigger_time_array = global_time;
        return extract_signal_segments(signal_map, trigger_time_array, valid_triggers);
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
        for (int idx : trigger_indices) {
            int start = idx - pre_buffer;
            int end = idx + post_buffer;
            if (start < 0 || end >= signal_size)
                continue;
            if (start > last_end) {
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
        const py::array_t<double> &time_array,
        const std::vector<std::pair<int, int>> &valid_triggers)
    {
        std::vector<double> times_out, signals_out;
        std::vector<std::string> detectors_out;
        std::vector<int> segment_ids_out;
        for (const auto &[detector_name, signal_array] : signal_map) {
            // Use per-detector time if available; otherwise, use the provided time_array.
            py::array_t<double> t_array;
            if (time_array.size() > 0)
                t_array = time_array;
            else
                throw std::runtime_error("No time array available for extraction.");

            py::buffer_info signal_buf = signal_array.request();
            py::buffer_info time_buf = t_array.request();
            if (signal_buf.ndim != 1 || time_buf.ndim != 1)
                throw std::runtime_error("Signal and time arrays must be 1D");
            size_t signal_size = signal_buf.shape[0];
            double *signal_ptr = static_cast<double *>(signal_buf.ptr);
            double *time_ptr = static_cast<double *>(time_buf.ptr);
            size_t segment_id = 0;
            for (const auto &[start, end] : valid_triggers) {
                for (int i = start; i <= end; ++i) {
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
        .def(py::init<const std::string&, const std::string&, const double, const double, const int, const int, const int, const bool, const int>(),
            py::arg("scheme"),
            py::arg("trigger_detector_name"),
            py::arg("threshold"),
            py::arg("lower_threshold"),
            py::arg("pre_buffer") = 64,
            py::arg("post_buffer") = 64,
            py::arg("max_triggers") = -1,
            py::arg("debounce_enabled") = true,
            py::arg("min_window_duration") = -1
        )
        .def("add_time", &TriggeringSystem::add_time, "Adds a global time array to the system.")
        .def("add_signal", &TriggeringSystem::add_signal, "Adds a new signal to the system.")
        .def("run", &TriggeringSystem::run, "Executes the triggered acquisition analysis.")
        .def_readonly("global_time", &TriggeringSystem::global_time, "Time vector used for computation")
        .def("run_dynamic", &TriggeringSystem::run_dynamic, "Executes dynamic triggered acquisition analysis.");
}
