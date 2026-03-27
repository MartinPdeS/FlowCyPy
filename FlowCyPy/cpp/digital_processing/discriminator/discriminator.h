#pragma once

#include <cmath>
#include <optional>
#include <string>
#include <utility>
#include <vector>
#include <cstdio> // for printf

#include "threshold.h"
#include "trigger.h"



/**
 * @brief Abstract base class for threshold based trigger detectors.
 *
 * This class stores the common configuration and shared data structures used by
 * all trigger detection strategies. It provides:
 *
 * - the name of the signal channel used for trigger detection
 * - pre and post buffers applied around detected events
 * - a maximum number of accepted triggers
 * - the internal Trigger object that stores the time axis, input signals,
 *   and segmented outputs
 *
 * Derived classes implement the actual trigger detection policy in `run()`.
 */
class BaseDiscriminator {
public:
    /// Name of the signal channel used to detect trigger events.
    std::string trigger_channel;

    /// Number of samples to include before the detected trigger position.
    size_t pre_buffer = 0;

    /// Number of samples to include after the detected trigger position.
    size_t post_buffer = 0;

    /// Maximum number of accepted triggers. A value of -1 means no limit.
    int max_triggers = -1;

    /// Internal container storing time, signals, and segmented outputs.
    Trigger trigger;

    /// Default constructor.
    BaseDiscriminator() = default;

    /// Virtual destructor for polymorphic use.
    virtual ~BaseDiscriminator() = default;

    /**
     * @brief Construct a trigger detector with common trigger configuration.
     *
     * @param trigger_channel
     *     Name of the signal channel used for trigger detection.
     * @param pre_buffer
     *     Number of samples to include before each accepted trigger.
     * @param post_buffer
     *     Number of samples to include after each accepted trigger.
     * @param max_triggers
     *     Maximum number of accepted triggers. Use -1 for no limit.
     */
    BaseDiscriminator(
        const std::string &trigger_channel,
        size_t pre_buffer,
        size_t post_buffer,
        int max_triggers = -1
    )
        : trigger_channel(trigger_channel),
          pre_buffer(pre_buffer),
          post_buffer(post_buffer),
          max_triggers(max_triggers) {}

    /**
     * @brief Add the global time axis used by all signal channels.
     *
     * The time vector must contain one value per sample. All subsequently added
     * signals must have the same number of samples as this time axis.
     *
     * @param time
     *     One dimensional vector containing the time coordinates of the signal.
     */
    void add_time(const std::vector<double> &time);

    /**
     * @brief Add a signal channel to the trigger system.
     *
     * The provided signal is stored under `detector_name` and can later be used
     * either as the trigger channel or as one of the channels segmented around
     * the detected event windows.
     *
     * @param detector_name
     *     Name associated with the signal channel.
     * @param signal
     *     One dimensional vector containing the signal samples.
     */
    void add_signal(
        const std::string &detector_name,
        const std::vector<double> &signal
    );

    /**
     * @brief Resolve a threshold object into a numeric threshold value.
     *
     * A threshold may be defined either as:
     *
     * - a numeric voltage threshold
     * - a symbolic threshold string such as `"3sigma"`
     *
     * If the threshold is symbolic, it is interpreted using statistics
     * computed from the configured trigger channel.
     *
     * @param threshold
     *     Threshold descriptor to resolve.
     *
     * @return
     *     Numeric threshold value expressed in volts.
     */
    double parse_threshold(const Threshold &threshold) const;

    /**
     * @brief Execute trigger detection and segmentation.
     *
     * This method must be implemented by derived classes and is responsible for:
     *
     * - validating the configuration
     * - resolving stored threshold values
     * - detecting valid trigger windows
     * - segmenting the stored signals around those windows
     */
    virtual void run() = 0;

protected:
    /**
     * @brief Validate that a signal channel exists in the internal signal map.
     *
     * Throws an exception if `detector_name` is not present in the stored
     * signal map.
     *
     * @param detector_name
     *     Name of the signal channel to validate.
     */
    void validate_detector_existence(const std::string &detector_name) const;

    /**
     * @brief Extract segmented signal windows from validated trigger ranges.
     *
     * Each pair in `valid_triggers` represents a start and end sample index
     * defining one accepted event window.
     *
     * @param valid_triggers
     *     Vector of accepted trigger index ranges.
     */
    void extract_signal_segments(
        const std::vector<std::pair<int, int>> &valid_triggers
    );

    /**
     * @brief Parse a symbolic sigma threshold string.
     *
     * Supported expressions follow the pattern `"Nsigma"`, for example
     * `"3sigma"` or `"4.5sigma"`. The threshold is computed from the signal
     * stored in the configured trigger channel as:
     *
     *     median(signal) + N * sigma_mad(signal)
     *
     * where `sigma_mad` is a robust MAD based estimate of the standard deviation.
     *
     * @param threshold_string
     *     Symbolic sigma threshold string.
     *
     * @return
     *     Numeric threshold value expressed in volts.
     */
    double parse_sigma_threshold_string(
        const std::string &threshold_string
    ) const;

    /**
     * @brief Compute the median of a vector of values.
     *
     * The input vector is taken by value because the algorithm reorders the
     * content using `std::nth_element`.
     *
     * @param values
     *     Input values for which the median is computed.
     *
     * @return
     *     Median of the provided values.
     */
    double compute_median(std::vector<double> values) const;

    /**
     * @brief Compute a MAD based estimate of the signal standard deviation.
     *
     * The returned quantity is:
     *
     *     median(|x - median(x)|) / 0.6745
     *
     * which is a robust estimator of sigma for approximately Gaussian data.
     *
     * @param signal
     *     Input signal values.
     *
     * @return
     *     Robust sigma estimate of the signal.
     */
    double compute_mad_based_sigma(const std::vector<double> &signal) const;

    /**
     * @brief Print a warning when no segment satisfies the trigger criteria.
     *
     * This helper inspects the segmented output associated with the configured
     * trigger channel. If no segment was extracted, it prints a warning message
     * together with the minimum and maximum signal values observed on that
     * channel.
     *
     * This is intended as a lightweight diagnostic to help tune thresholds
     * during development or debugging.
     */
    void print_warning_if_no_signal_met_trigger_criteria() {
        const auto segmented_signal =
            this->trigger.get_segmented_signal(
                this->trigger_channel
            );

        if (!segmented_signal.empty()) {
            return;
        }

        const auto signal_iterator =
            this->trigger.signal_map.find(
                this->trigger_channel
            );

        if (signal_iterator == this->trigger.signal_map.end()) {
            return;
        }

        const std::vector<double> &signal = signal_iterator->second;

        if (signal.empty()) {
            return;
        }

        const auto [minimum_iterator, maximum_iterator] = std::minmax_element(
            signal.begin(),
            signal.end()
        );

        std::printf(
            "[TriggerWarning] No signal met the trigger criteria. "
            "Try adjusting the threshold. "
            "Signal min/max: %g V, %g V\n",
            *minimum_iterator,
            *maximum_iterator
        );
    }
};



/**
 * @brief Fixed window threshold detector.
 *
 * This detector identifies threshold crossings on the configured trigger
 * channel and extracts a fixed width window around each accepted event using
 * `pre_buffer` and `post_buffer`.
 */
class FixedWindow : public BaseDiscriminator {
public:
    /// Threshold used to detect trigger events.
    Threshold threshold;
    double resolved_threshold = std::nan("");


public:
    /**
     * @brief Construct a fixed window trigger detector.
     *
     * @param trigger_channel
     *     Name of the signal channel used for trigger detection.
     * @param pre_buffer
     *     Number of samples to include before each trigger.
     * @param post_buffer
     *     Number of samples to include after each trigger.
     * @param max_triggers
     *     Maximum number of accepted triggers. Use -1 for no limit.
     */
    FixedWindow(
        const std::string &trigger_channel,
        size_t pre_buffer,
        size_t post_buffer,
        int max_triggers = -1
    )
        : BaseDiscriminator(trigger_channel, pre_buffer, post_buffer, max_triggers) {}

    /**
     * @brief Set the trigger threshold from a numeric value.
     *
     * @param threshold_value
     *     Numeric voltage threshold.
     */
    void set_threshold(const double threshold_value) {
        this->threshold.set_numeric(threshold_value);
    }

    /**
     * @brief Set the trigger threshold from a symbolic expression.
     *
     * Typical examples include strings such as `"3sigma"`.
     *
     * @param threshold_string
     *     Symbolic threshold expression.
     */
    void set_threshold(const std::string &threshold_string) {
        this->threshold.set_symbolic(threshold_string);
    }

    /**
     * @brief Clear the stored trigger threshold.
     *
     * After calling this function, `run()` will fail until a new threshold
     * is configured.
     */
    void clear_threshold() {
        this->threshold.clear();
        this->resolved_threshold = std::nan("");
    }

    /**
     * @brief Execute fixed window trigger detection.
     *
     * This method resolves the stored threshold, detects rising threshold
     * crossings on `trigger_channel`, builds fixed width event windows, and
     * segments the stored signals accordingly.
     */
    void run() override;
};



/**
 * @brief Dynamic window threshold detector.
 *
 * This detector identifies threshold crossings on the configured trigger
 * channel and extends each event window dynamically while the signal remains
 * above threshold, then applies the configured pre and post buffers.
 */
class DynamicWindow : public BaseDiscriminator {
public:
    /// Threshold used to detect trigger events.
    Threshold threshold;
    double resolved_threshold = std::nan("");

public:
    /**
     * @brief Construct a dynamic window trigger detector.
     *
     * @param trigger_channel
     *     Name of the signal channel used for trigger detection.
     * @param pre_buffer
     *     Number of samples to include before each trigger.
     * @param post_buffer
     *     Number of samples to include after each trigger.
     * @param max_triggers
     *     Maximum number of accepted triggers. Use -1 for no limit.
     */
    DynamicWindow(
        const std::string &trigger_channel,
        size_t pre_buffer,
        size_t post_buffer,
        int max_triggers = -1
    )
        : BaseDiscriminator(trigger_channel, pre_buffer, post_buffer, max_triggers) {}

    /**
     * @brief Set the trigger threshold from a numeric value.
     *
     * @param threshold_value
     *     Numeric voltage threshold.
     */
    void set_threshold(const double threshold_value) {
        this->threshold.set_numeric(threshold_value);
    }

    /**
     * @brief Set the trigger threshold from a symbolic expression.
     *
     * Typical examples include strings such as `"3sigma"`.
     *
     * @param threshold_string
     *     Symbolic threshold expression.
     */
    void set_threshold(const std::string &threshold_string) {
        this->threshold.set_symbolic(threshold_string);
    }

    /**
     * @brief Clear the stored trigger threshold.
     *
     * After calling this function, `run()` will fail until a new threshold
     * is configured.
     */
    void clear_threshold() {
        this->threshold.clear();
        this->resolved_threshold = std::nan("");
    }

    /**
     * @brief Execute dynamic window trigger detection.
     *
     * This method resolves the stored threshold, detects rising threshold
     * crossings on `trigger_channel`, extends each event until the signal
     * drops below threshold, and segments the stored signals accordingly.
     */
    void run() override;
};



/**
 * @brief Double threshold detector with hysteresis and optional debouncing.
 *
 * This detector uses:
 *
 * - a primary threshold to start an event
 * - an optional lower threshold to determine when the event is considered ended
 * - an optional debounce mode with a minimum window duration requirement
 *
 * This is useful when a simple single threshold would be too sensitive to
 * noise or oscillations around the threshold level.
 */
class DoubleThreshold : public BaseDiscriminator {
public:
    /// Primary threshold used to start an event.
    Threshold threshold;

    /// Secondary threshold used to terminate or re arm an event.
    Threshold lower_threshold;

    /// Indicates whether a lower threshold has been explicitly configured.
    bool has_lower_threshold = false;

    /// Enables or disables debounce logic.
    bool debounce_enabled = true;

    /// Minimum number of samples required for a valid trigger window. A value of -1 disables this constraint.
    int min_window_duration = -1;

    double resolved_upper_threshold = std::nan("");
    double resolved_lower_threshold = std::nan("");

public:
    /**
     * @brief Construct a double threshold trigger detector.
     *
     * @param trigger_channel
     *     Name of the signal channel used for trigger detection.
     * @param pre_buffer
     *     Number of samples to include before each trigger.
     * @param post_buffer
     *     Number of samples to include after each trigger.
     * @param max_triggers
     *     Maximum number of accepted triggers. Use -1 for no limit.
     */
    DoubleThreshold(
        const std::string &trigger_channel,
        size_t pre_buffer,
        size_t post_buffer,
        int max_triggers = -1
    )
        : BaseDiscriminator(trigger_channel, pre_buffer, post_buffer, max_triggers) {}

    /**
     * @brief Set the primary threshold from a numeric value.
     *
     * @param threshold_value
     *     Numeric voltage threshold used to start an event.
     */
    void set_threshold(const double threshold_value) {
        this->threshold.set_numeric(threshold_value);
    }

    /**
     * @brief Set the primary threshold from a symbolic expression.
     *
     * Typical examples include strings such as `"3sigma"`.
     *
     * @param threshold_string
     *     Symbolic threshold expression used to start an event.
     */
    void set_threshold(const std::string &threshold_string) {
        this->threshold.set_symbolic(threshold_string);
    }

    /**
     * @brief Set the lower threshold from a numeric value.
     *
     * The lower threshold is used for hysteresis. Once an event has started,
     * the detector keeps the event active until the signal drops below this
     * lower threshold.
     *
     * @param threshold_value
     *     Numeric voltage threshold used as the lower hysteresis threshold.
     */
    void set_lower_threshold(const double threshold_value) {
        this->lower_threshold.set_numeric(threshold_value);
        this->has_lower_threshold = true;
    }

    /**
     * @brief Set the lower threshold from a symbolic expression.
     *
     * @param threshold_string
     *     Symbolic lower threshold expression.
     */
    void set_lower_threshold(const std::string &threshold_string) {
        this->lower_threshold.set_symbolic(threshold_string);
        this->has_lower_threshold = true;
    }

    /**
     * @brief Clear the lower threshold configuration.
     *
     * After clearing, the detector behaves as if no explicit lower threshold
     * was provided.
     */
    void clear_lower_threshold() {
        this->lower_threshold.clear();
        this->has_lower_threshold = false;
        this->resolved_lower_threshold = std::nan("");
    }

    /**
     * @brief Enable or disable debounce logic.
     *
     * @param debounce_enabled
     *     Boolean flag controlling debounce behavior.
     */
    void set_debounce_enabled(const bool debounce_enabled) {
        this->debounce_enabled = debounce_enabled;
    }

    /**
     * @brief Set the minimum window duration for accepted events.
     *
     * When debounce is enabled, events shorter than this duration are rejected.
     * A value of -1 disables this constraint.
     *
     * @param min_window_duration
     *     Minimum number of samples required for a valid event.
     */
    void set_min_window_duration(const int min_window_duration) {
        this->min_window_duration = min_window_duration;
    }

    /**
     * @brief Execute double threshold trigger detection.
     *
     * This method resolves the stored primary threshold and optional lower
     * threshold, detects threshold crossings on `trigger_channel`, applies
     * hysteresis and optional debounce logic, and segments the stored signals
     * around the accepted event windows.
     */
    void run() override;
};
