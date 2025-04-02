#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include <cmath>      // for std::isnan
namespace py = pybind11;


struct trigger {
    const std::string detector_name;
    const py::array_t<double> signal;
    std::vector<double> time_out;
    std::vector<double> signal_out;
    std::vector<int> segment_ids_out;
    double* buffer_ptr;
    size_t buffer_size;

    trigger(const std::string &detector_name, const py::array_t<double> &signal): detector_name(detector_name), signal(signal)
    {
        this->buffer_ptr = static_cast<double *>(signal.request().ptr);
        this->buffer_size = static_cast<size_t>(signal.request().shape[0]);
    }
};

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
    double lower_threshold;
    int pre_buffer;
    int post_buffer;
    int max_triggers;
    bool debounce_enabled;
    int min_window_duration;

    std::vector<struct trigger> triggers;

    // The maps will be filled using the add_signal method.
    std::map<std::string, py::array_t<double>> signal_map;
    // For time arrays, the user can add a global one.
    py::array_t<double> global_time;
    // Optionally, a per-detector time map can be supported.
    std::map<std::string, py::array_t<double>> time_map;
    std::vector<double> times_out, signals_out;

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
        if (time.request().ndim != 1)
            throw std::runtime_error("Time arrays must be 1D");

        global_time = time;
    }

    /**
     * @brief Adds a new signal to the system.
     *
     * @param name The name of the detector/signal.
     * @param signal The signal as a py::array_t<double>.
     */
    void add_signal(const std::string &detector_name, const py::array_t<double> &signal) {
        if (signal.request().ndim != 1)
            throw std::runtime_error("Signal arrays must be 1D");

        this->triggers.emplace_back(detector_name, signal);
        signal_map[detector_name] = signal;
    }

    void run() {
        // Validate that the trigger detector exists.
        validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");

        // For time, try the per-detector map; if not found, check global_time.
        if (time_map.find(trigger_detector_name) == time_map.end() && global_time.size() == 0)
            throw std::runtime_error("No time array found. Please add a time array using add_time().");

        std::vector<std::pair<int, int>> valid_triggers;

        if (this->scheme == "fixed-window")
            valid_triggers = this->run_fixed_window();
        else if (this->scheme == "dynamic")
            valid_triggers = this->run_dynamic_single_threshold();
        else if (this->scheme == "dynamic-simple")
            valid_triggers = this->run_dynamic();
        else
            PyErr_WarnEx(PyExc_UserWarning, "Invalid triggering scheme, options are: 'fixed-window', 'dynamic', or 'dynamic-simple'.", 1);

        if (valid_triggers.empty())
            PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found in dynamic mode (single threshold). Returning empty arrays.", 1);


        // Use per-detector time if available, otherwise use global_time.
        py::array_t<double> trigger_time_array;
        if (this->time_map.find(trigger_detector_name) != this->time_map.end())
            trigger_time_array = this->time_map.at(trigger_detector_name);
        else
            trigger_time_array = global_time;

        extract_signal_segments(valid_triggers);
    }

    // Fixed-window triggered acquisition.
    std::vector<std::pair<int, int>> run_fixed_window() {

        auto trigger_signal_array = this->signal_map.at(trigger_detector_name);

        py::buffer_info trigger_signal_buf = trigger_signal_array.request();
        size_t n_trigger = trigger_signal_buf.shape[0];
        double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);
        std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);

        std::vector<int> trigger_indices = find_trigger_indices(trigger_signal.data(), n_trigger, threshold);
        std::vector<std::pair<int, int>> valid_triggers = apply_buffer_constraints(
            trigger_indices, pre_buffer - 1, post_buffer, static_cast<int>(n_trigger), max_triggers
        );

        return valid_triggers;
    }

    // Simple dynamic triggered acquisition.
    std::vector<std::pair<int, int>> run_dynamic() {
        auto trigger_signal_array = this->signal_map.at(trigger_detector_name);
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

        return valid_triggers;
    }

    // Dynamic triggered acquisition with single threshold (with optional lower_threshold and debounce).
    std::vector<std::pair<int, int>> run_dynamic_single_threshold() {
        if (std::isnan(lower_threshold))
            this->lower_threshold = this->threshold;

        auto trigger_signal_array = this->signal_map.at(trigger_detector_name);
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

        return valid_triggers;
    }

    std::vector<double> get_signal_out(const std::string &detector_name) {
        for (struct trigger &trigger : this->triggers)
            if (trigger.detector_name == detector_name)
                return trigger.signal_out;
    }

    std::vector<double> get_time_out(const std::string &detector_name) {
        for (struct trigger &trigger : this->triggers)
            if (trigger.detector_name == detector_name)
                return trigger.time_out;
    }

    std::vector<int> get_segment_ID(const std::string &detector_name) {
        for (struct trigger &trigger : this->triggers)
            if (trigger.detector_name == detector_name)
                return trigger.segment_ids_out;
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
    void extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers)
    {
        std::vector<std::string> detectors_out;
        std::vector<int> segment_ids_out;

        double* time_ptr = static_cast<double *>(global_time.request().ptr);

        for (struct trigger &trigger : this->triggers) {
            size_t segment_id = 0;
            for (const auto &[start, end] : valid_triggers) {
                for (int i = start; i <= end; ++i) {
                    if (i >= static_cast<int>(trigger.buffer_size))
                        break;

                    trigger.signal_out.push_back(trigger.buffer_ptr[i]);
                    trigger.time_out.push_back(time_ptr[i]);
                    trigger.segment_ids_out.push_back(segment_id);
                }
                segment_id++;
            }
        }
    }





};
