#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
namespace py = pybind11;


struct Trigger {
    const std::string detector_name;
    const py::buffer signal;
    std::vector<double> time_out;
    std::vector<double> signal_out;
    std::vector<int> segment_ids_out;
    double* buffer_ptr;
    size_t buffer_size;

    Trigger(const std::string &detector_name, const py::buffer signal): detector_name(detector_name), signal(signal)
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
     * The user must then add a global time array using add_time(py::buffer)
     * and add one or more signals using add_signal(string, py::buffer).
     *
     * Parameters:
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
    std::string trigger_detector_name;
    double threshold;
    double lower_threshold;
    int pre_buffer;
    int post_buffer;
    int max_triggers;
    bool debounce_enabled;
    int min_window_duration;

    std::vector<struct Trigger> triggers;
    py::buffer global_time;

    TriggeringSystem(
        const std::string &trigger_detector_name,
        const double threshold,
        const double lower_threshold,
        const int pre_buffer,
        const int post_buffer,
        const int max_triggers,
        const bool debounce_enabled,
        const int min_window_duration
    )
        : trigger_detector_name(trigger_detector_name), threshold(threshold), lower_threshold(lower_threshold),
          pre_buffer(pre_buffer), post_buffer(post_buffer), max_triggers(max_triggers),
          debounce_enabled(debounce_enabled), min_window_duration(min_window_duration)
    {}

    /**
     * @brief Adds a global time array.
     *
     * This time array will be used for all detectors unless a per-detector time array is provided.
     *
     * @param time The time array as a py::buffer.
     */
    void add_time(const py::buffer &time);

    /**
     * @brief Adds a new signal to the system.
     *
     * @param name The name of the detector/signal.
     * @param signal The signal as a py::buffer.
     */
    void add_signal(const std::string &detector_name, const py::buffer signal);

    void run(const std::string& algorithm);

    // Fixed-window triggered acquisition.
    std::vector<std::pair<int, int>> run_fixed_window();

    // Simple dynamic triggered acquisition.
    std::vector<std::pair<int, int>> run_dynamic();

    // Dynamic triggered acquisition with single threshold (with optional lower_threshold and debounce).
    std::vector<std::pair<int, int>> run_dynamic_single_threshold();

    struct Trigger get_trigger(const std::string &detector_name);

    std::vector<double> get_signals_py(const std::string &detector_name);

    std::vector<double> get_times_py(const std::string &detector_name);

    std::vector<int> get_segments_ID_py(const std::string &detector_name);


private:
    // Helper function: Validate that the detector exists in the map.
    void validate_detector_existence(const std::string &detector_name);

    // Helper function: Extract signal segments given valid trigger indices.
    void extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers);
};
