#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <cmath>      // for std::isnan

namespace py = pybind11;

// Represents a single trigger event, including its source signal and extracted segments.
struct Trigger {
    const std::string detector_name;   // Identifier for this detector's signal
    const py::buffer signal;           // Raw input signal buffer from Python

    // Output vectors filled after processing:
    std::vector<double> time_out;      // Time stamps corresponding to each segment sample
    std::vector<double> signal_out;    // Signal values extracted for each segment
    std::vector<int> segment_ids_out;  // Mapping of sample indices to segment IDs

    double* buffer_ptr;                // Direct pointer into the signal buffer
    size_t buffer_size;                // Number of samples in the input signal

    // Construct from a detector name and Python buffer. Initializes pointers for fast access.
    Trigger(const std::string &detector_name, const py::buffer &signal)
        : detector_name(detector_name), signal(signal)
    {
        auto info = signal.request();
        buffer_ptr = static_cast<double*>(info.ptr);
        buffer_size = static_cast<size_t>(info.shape[0]);
    }
};

// Main class for threshold-based and dynamic signal triggering.
// Users add a global time axis and one or more named signals, then
// run trigger detection to extract sample segments.
class TriggeringSystem {
public:
    std::string trigger_detector_name;        // Algorithm name, e.g. "fixed" or "sliding"
    int pre_buffer;                           // Samples to include before each trigger
    int post_buffer;                          // Samples to include after each trigger
    int max_triggers;                         // Cap on number of triggers (-1 = unlimited)

    std::vector<Trigger> triggers;            // Collection of all signals to process
    py::buffer global_time;                   // Shared time axis for all signals

    /**
     * @brief Construct a new TriggeringSystem with buffer and trigger limits.
     *
     * @param trigger_detector_name Name of the detection algorithm to apply.
     * @param pre_buffer           Samples to buffer before each detected event.
     * @param post_buffer          Samples to buffer after each detected event.
     * @param max_triggers         Maximum number of triggers to record (-1 = no limit).
     */
    TriggeringSystem(const std::string &trigger_detector_name,
                     size_t pre_buffer,
                     size_t post_buffer,
                     int max_triggers = -1)
        : trigger_detector_name(trigger_detector_name),
          pre_buffer(pre_buffer),
          post_buffer(post_buffer),
          max_triggers(max_triggers)
    {}

    /**
     * @brief Assign a global time axis used for all signals.
     *
     * The time stamps must be monotonically increasing and match the
     * length of any signals added to this system.
     *
     * @param time 1D NumPy array of time values.
     */
    void add_time(const py::buffer &time);

    /**
     * @brief Add a named signal buffer for triggering analysis.
     *
     * The length of the signal buffer must match the global time axis.
     *
     * @param detector_name Unique name for this signal (used for lookup).
     * @param signal        1D NumPy array of signal samples.
     */
    void add_signal(const std::string &detector_name, const py::buffer &signal);

    /**
     * @brief Execute the trigger detection algorithm.
     *
     * @param algorithm          Name of the algorithm to run.
     * @param threshold          Primary threshold for event detection.
     * @param lower_threshold    Secondary (hysteresis) threshold.
     * @param debounce_enabled   Enable or disable rapid-fire suppression.
     * @param min_window_duration Minimum samples between separate triggers.
     */
    void run(const std::string &algorithm,
             double threshold,
             double lower_threshold,
             bool debounce_enabled,
             int min_window_duration);

    /// Fixed-window detection (single threshold)
    std::vector<std::pair<int, int>> run_fixed_window(double threshold);

    /// Dynamic-window detection (threshold-based window sizing)
    std::vector<std::pair<int, int>> run_dynamic(double threshold);

    /**
     * @brief Dynamic detection with hysteresis and optional debouncing.
     *
     * @param threshold          Primary threshold for detection.
     * @param lower_threshold    Lower threshold to re-arm triggers.
     * @param debounce_enabled   Suppress triggers too close in time.
     * @param min_window_duration Minimum window length in samples.
     */
    std::vector<std::pair<int, int>> run_dynamic_double_threshold(
        double threshold,
        double lower_threshold = std::nan(""),
        bool debounce_enabled = true,
        int min_window_duration = -1);

    /**
     * @brief Retrieve the Trigger struct for a named detector.
     *
     * @param detector_name Name of the previously added signal.
     * @return Trigger&     Reference to the corresponding Trigger object.
     */
    Trigger get_trigger(const std::string &detector_name) const;

    /**
     * @brief Get the extracted signal segments for a detector.
     *
     * @param detector_name Name of the detector.
     * @return vector<double> Concatenated signal segments.
     */
    std::vector<double> get_signals_py(const std::string &detector_name) const;

    /**
     * @brief Get the time stamps for each extracted segment.
     *
     * @param detector_name Name of the detector.
     * @return vector<double> Concatenated time arrays for segments.
     */
    std::vector<double> get_times_py(const std::string &detector_name) const;

    /**
     * @brief Get segment ID mapping for each sample index.
     *
     * @param detector_name Name of the detector.
     * @return vector<int>   Segment ID per sample (-1 if none).
     */
    std::vector<int> get_segments_ID_py(const std::string &detector_name) const;

private:
    /**
     * @brief Ensure a signal with the given name has been added.
     *
     * Throws std::runtime_error if the detector_name is unrecognized.
     */
    void validate_detector_existence(const std::string &detector_name) const;

    /**
     * @brief Extract and store time/signal segments from trigger indices.
     *
     * @param valid_triggers Vector of (start, end) indices for each trigger.
     */
    void extract_signal_segments(const std::vector<std::pair<int, int>> &valid_triggers);
};
