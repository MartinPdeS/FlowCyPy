#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include <cmath>      // for std::isnan
namespace py = pybind11;


struct Trigger {
    const std::string detector_name;
    const py::array_t<double> signal;
    std::vector<double> time_out;
    std::vector<double> signal_out;
    std::vector<int> segment_ids_out;
    double* buffer_ptr;
    size_t buffer_size;

    Trigger(const std::string &detector_name, const py::array_t<double> &signal): detector_name(detector_name), signal(signal)
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

    std::vector<struct Trigger> triggers;
    // For time arrays, the user can add a global one.
    py::array_t<double> global_time;

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
    }

    void run() {
        // Validate that the trigger detector exists.
        this->validate_detector_existence(trigger_detector_name);

        // For time, try the per-detector map; if not found, check global_time.
        if (global_time.size() == 0)
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

        extract_signal_segments(valid_triggers);
    }

    // Fixed-window triggered acquisition.
    std::vector<std::pair<int, int>> run_fixed_window() {
        struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

        std::vector<std::pair<int, int>> valid_triggers;

        std::vector<int> trigger_indices;
        for (size_t i = 1; i < trigger_channel.buffer_size; ++i)
            if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold)
                trigger_indices.push_back(i - 1);

        int last_end = -1;
        for (int idx : trigger_indices) {
            int start = idx - pre_buffer - 1;
            int end = idx + post_buffer;
            if (start < 0 || end >= static_cast<int>(trigger_channel.buffer_size))
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

    // Simple dynamic triggered acquisition.
    std::vector<std::pair<int, int>> run_dynamic() {
        struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

        std::vector<std::pair<int, int>> valid_triggers;

        int last_end = -1;
        for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
            if (trigger_channel.buffer_ptr[i - 1] <= threshold && trigger_channel.buffer_ptr[i] > threshold) {
                int start = static_cast<int>(i) - pre_buffer;
                if (start < 0)
                    start = 0;
                size_t j = i;
                while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > threshold)
                    j++;
                int end = static_cast<int>(j) - 1 + post_buffer;
                if (end >= static_cast<int>(trigger_channel.buffer_size))
                    end = static_cast<int>(trigger_channel.buffer_size) - 1;
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
        struct Trigger trigger_channel = this->get_trigger(trigger_detector_name);

        std::vector<std::pair<int, int>> valid_triggers;

        if (std::isnan(lower_threshold))
            this->lower_threshold = this->threshold;

        int last_end = -1;
        for (size_t i = 1; i < trigger_channel.buffer_size; ++i) {
            if (trigger_channel.buffer_ptr[i - 1] <= this->threshold && trigger_channel.buffer_ptr[i] > this->threshold) {
                size_t j = i;
                if (debounce_enabled && min_window_duration != -1) {
                    size_t count = 0;
                    while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > this->threshold) {
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
                    while (j < trigger_channel.buffer_size && trigger_channel.buffer_ptr[j] > this->threshold)
                        ++j;
                }
                int start = static_cast<int>(i) - pre_buffer;
                if (start < 0)
                    start = 0;
                size_t k = j;
                while (k < trigger_channel.buffer_size && trigger_channel.buffer_ptr[k] > this->lower_threshold)
                    ++k;
                int end = static_cast<int>(k) - 1 + post_buffer;
                if (end >= static_cast<int>(trigger_channel.buffer_size))
                    end = static_cast<int>(trigger_channel.buffer_size) - 1;
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

    struct Trigger get_trigger(const std::string &detector_name) {
        for (struct Trigger &trigger : this->triggers)
            if (trigger.detector_name == detector_name)
                return trigger;

        throw std::runtime_error("Detector not found");
    }

    template <typename T>
    py::array_t<T> to_numpy_array(const std::vector<T>& vector) {
        // Transfer ownership of the vector by moving it into a new heap allocation.
        auto* vec_ptr = new std::vector<T>(std::move(vector));
        // Create a capsule that will free the vector when the array is destroyed.
        py::capsule free_when_done(vec_ptr, [](void *v) {
            delete reinterpret_cast<std::vector<T>*>(v);
        });
        // Construct a py::array_t<double> that wraps the vector's data.
        return py::array_t<T>(
            {vec_ptr->size()},            // shape: one dimension of length = vector size
            {sizeof(T)},                  // stride: size of double in bytes
            vec_ptr->data(),              // pointer to the data
            free_when_done                // capsule holding our vector pointer
        );
    }

    py::array_t<double> get_signal_out_py(const std::string &detector_name) {
        struct Trigger trigger = this->get_trigger(detector_name);

        return this->to_numpy_array(trigger.signal_out);
    }

    py::array_t<double> get_time_out_py(const std::string &detector_name) {
        struct Trigger trigger = this->get_trigger(detector_name);

        return this->to_numpy_array(trigger.time_out);
    }

    py::array_t<int> get_segment_ID_py(const std::string &detector_name) {
        struct Trigger trigger = this->get_trigger(detector_name);

        return this->to_numpy_array(trigger.segment_ids_out);
    }


private:
    // Helper function: Validate that the detector exists in the map.
    void validate_detector_existence(const std::string &detector_name)
    {
        for (struct Trigger trigger: this->triggers)
            if (detector_name == trigger.detector_name)
                return;

        std::runtime_error("Trigger detector not found in signal map.");
    }

    // Helper function: Extract signal segments given valid trigger indices.
    void extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers)
    {
        double* time_ptr = static_cast<double *>(global_time.request().ptr);

        for (struct Trigger &trigger : this->triggers) {
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
