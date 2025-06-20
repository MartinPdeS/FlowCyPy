#include <pybind11/pybind11.h>
#include <vector>
#include <string>
#include <cmath>      // for std::isnan
#include "trigger.cpp"


class BaseTrigger {
public:
    std::string trigger_detector_name;        // Name of the detection algorithm
    size_t pre_buffer;                        // Samples to include before each trigger
    size_t post_buffer;                       // Samples to include after each trigger
    int max_triggers;                         // Cap on number of triggers (-1 = unlimited)
    std::vector<double> global_time;          // Global time axis for all signals
    std::vector<Trigger> triggers;            // Collection of all signals to process

public:
    BaseTrigger() = default;


    BaseTrigger(const std::string& trigger_detector_name, size_t pre_buffer, size_t post_buffer, int max_triggers = -1)
        : trigger_detector_name(trigger_detector_name), pre_buffer(pre_buffer), post_buffer(post_buffer), max_triggers(max_triggers) {}


    /**
     * @brief Assign a global time axis used for all signals.
     *
     * The time stamps must be monotonically increasing and match the
     * length of any signals added to this system.
     *
     * @param time 1D NumPy array of time values.
     */
    void add_time(const std::vector<double> &time);

    /**
     * @brief Add a named signal buffer for triggering analysis.
     *
     * The length of the signal buffer must match the global time axis.
     *
     * @param detector_name Unique name for this signal (used for lookup).
     * @param signal        1D NumPy array of signal samples.
     */
    void add_signal(const std::string &detector_name, const std::vector<double> &signal);


    /**
     * @brief Retrieve the Trigger struct for a named detector.
     *
     * @param detector_name Name of the previously added signal.
     * @return Trigger&     Reference to the corresponding Trigger object.
     */
    Trigger get_trigger(const std::string &detector_name) const;


protected:
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


public:
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

};





class FixedWindow: public BaseTrigger {
public:

    /**
     * @brief Construct a new TriggeringSystem with buffer and trigger limits.
     *
     * @param trigger_detector_name Name of the detection algorithm to apply.
     * @param pre_buffer           Samples to buffer before each detected event.
     * @param post_buffer          Samples to buffer after each detected event.
     * @param max_triggers         Maximum number of triggers to record (-1 = no limit).
     */
    FixedWindow(const std::string &trigger_detector_name, size_t pre_buffer, size_t post_buffer, int max_triggers)
        : BaseTrigger(trigger_detector_name, pre_buffer, post_buffer, max_triggers) {}


    /**
     * @brief Execute the trigger detection algorithm.
     *
     * @param threshold          Primary threshold for event detection.
     * @note This uses a fixed window size based on pre/post buffers.
     * @note The algorithm is simple: detect when the signal crosses the threshold.
     */
    void run(const double threshold);

};



class DynamicWindow: public BaseTrigger {
public:

    /**
     * @brief Construct a new TriggeringSystem with buffer and trigger limits.
     *
     * @param trigger_detector_name Name of the detection algorithm to apply.
     * @param pre_buffer           Samples to buffer before each detected event.
     * @param post_buffer          Samples to buffer after each detected event.
     * @param max_triggers         Maximum number of triggers to record (-1 = no limit).
     */
    DynamicWindow(const std::string &trigger_detector_name, size_t pre_buffer, size_t post_buffer, int max_triggers = -1)
        : BaseTrigger(trigger_detector_name, pre_buffer, post_buffer, max_triggers) {}


    /**
     * @brief Execute the trigger detection algorithm with dynamic window sizing.
     * @param threshold          Primary threshold for event detection.
     * @note This uses a dynamic window size based on signal behavior.
     * @note The algorithm detects when the signal crosses the threshold,
     *       then expands the window until the signal falls below the threshold.
     */
    void run(const double threshold);

};


class DoubleThreshold: public BaseTrigger {
public:

    /**
     * @brief Construct a new TriggeringSystem with buffer and trigger limits.
     *
     * @param trigger_detector_name Name of the detection algorithm to apply.
     * @param pre_buffer           Samples to buffer before each detected event.
     * @param post_buffer          Samples to buffer after each detected event.
     * @param max_triggers         Maximum number of triggers to record (-1 = no limit).
     */
    DoubleThreshold(const std::string &trigger_detector_name, size_t pre_buffer, size_t post_buffer, int max_triggers = -1)
        : BaseTrigger(trigger_detector_name, pre_buffer, post_buffer, max_triggers) {}


    /**
     * @brief Execute the trigger detection algorithm with hysteresis.
     * @param threshold          Primary threshold for event detection.
     * @param lower_threshold    Secondary threshold to re-arm triggers.
     * @param debounce_enabled   Enable or disable rapid-fire suppression.
     * @param min_window_duration Minimum samples between separate triggers.
     * @note This uses a dynamic window size based on signal behavior.
     * @note The algorithm detects when the signal crosses the primary threshold,
     *       then waits for it to fall below the lower threshold before re-arming.
     */
    void run(const double threshold, const double lower_threshold, const bool debounce_enabled, const int min_window_duration = -1);

};

