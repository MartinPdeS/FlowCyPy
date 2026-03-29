#pragma once

#include <map>
#include <memory>
#include <string>
#include <vector>


/**
 * @brief Dictionary mapping metric names to arrays of numeric values.
 *
 * Typical keys are
 * - "Index"
 * - "Height"
 * - "Width"
 * - "Area"
 */
using MetricDictionary = std::map<std::string, std::vector<double>>;

/**
 * @brief Dictionary mapping channel names to flat signal vectors.
 *
 * This representation is used before regrouping samples by segment id.
 */
using FlatSignalDictionary = std::map<std::string, std::vector<double>>;

/**
 * @brief Dictionary mapping segment id to per-channel segmented vectors.
 *
 * The nested structure is:
 *
 *     {
 *         segment_id: {
 *             channel_name: [samples...],
 *             ...
 *         },
 *         ...
 *     }
 */
using SegmentedSignalDictionary = std::map<int, std::map<std::string, std::vector<double>>>;

/**
 * @brief Dictionary mapping segment id to per-channel metric dictionaries.
 *
 * The nested structure is:
 *
 *     {
 *         segment_id: {
 *             channel_name: {
 *                 "Index": [...],
 *                 "Height": [...],
 *                 "Width": [...],
 *                 "Area": [...],
 *             },
 *             ...
 *         },
 *         ...
 *     }
 */
using SegmentedMetricDictionary = std::map<int, std::map<std::string, MetricDictionary>>;


/**
 * @brief Container storing one detected peak and its optional metrics.
 *
 * Parameters
 * ----------
 * index :
 *     Sample index of the detected peak.
 * value :
 *     Peak height.
 * width :
 *     Peak width in samples.
 * area :
 *     Peak area.
 */
struct PeakData {
    int index;
    double value;
    double width;
    double area;

    PeakData(int index, double value, double width, double area)
        : index(index), value(value), width(width), area(area) {}
};


/**
 * @brief Internal container describing the support used for width and area.
 *
 * Fields
 * ------
 * width :
 *     Width of the selected support in samples.
 * area :
 *     Area integrated on the selected support.
 * left_boundary :
 *     Inclusive left support boundary.
 * right_boundary :
 *     Inclusive right support boundary.
 * left_touches_boundary :
 *     Whether the support reaches the left edge of the analyzed interval.
 * right_touches_boundary :
 *     Whether the support reaches the right edge of the analyzed interval.
 */
struct PeakMetrics {
    double width;
    double area;
    size_t left_boundary;
    size_t right_boundary;
    bool left_touches_boundary;
    bool right_touches_boundary;
};


/**
 * @brief Abstract base class describing how width and area support is defined.
 *
 * A support object is responsible for determining the semantics of width and
 * area computations.
 *
 * Two concrete implementations are provided:
 * - FullWindowSupport
 * - PulseSupport
 */
class BaseSupport {
public:
    virtual ~BaseSupport() = default;

    /**
     * @brief Whether this support mode uses the full analyzed interval.
     *
     * Returns
     * -------
     * bool
     *     True for full-window support, False otherwise.
     */
    virtual bool is_full_window() const = 0;

    /**
     * @brief Whether this support mode is channel independent.
     *
     * Returns
     * -------
     * bool
     *     True when each channel computes its own support independently.
     */
    virtual bool is_independent() const = 0;

    /**
     * @brief Return the configured support channel specifier.
     *
     * Returns
     * -------
     * std::string
     *     One of:
     *     - "full_window"
     *     - "default"
     *     - "independent"
     *     - a detector or channel name
     */
    virtual std::string get_channel() const = 0;

    /**
     * @brief Return the relative threshold associated with the support.
     *
     * Returns
     * -------
     * double
     *     Threshold value in the interval [0, 1] for pulse support.
     *     For full-window support, this is conventionally 0.
     */
    virtual double get_threshold() const = 0;

    /**
     * @brief Return a short support mode name.
     *
     * Returns
     * -------
     * std::string
     *     Human readable support mode identifier.
     */
    virtual std::string get_name() const = 0;
};


/**
 * @brief Support strategy that uses the full analyzed interval.
 *
 * Width and area are computed on the full segment or full sliding window.
 * No threshold expansion is used.
 */
class FullWindowSupport : public BaseSupport {
public:
    FullWindowSupport() = default;
    ~FullWindowSupport() override = default;

    bool is_full_window() const override;
    bool is_independent() const override;
    std::string get_channel() const override;
    double get_threshold() const override;
    std::string get_name() const override;
};


/**
 * @brief Support strategy based on a positive pulse support around a peak.
 *
 * The support is defined by first identifying a positive peak on a support
 * signal, then expanding left and right while the neighboring samples remain
 * above
 *
 *     threshold * peak_height
 *
 * Parameters
 * ----------
 * channel :
 *     Support channel selection rule.
 *
 *     Accepted values are:
 *     - "default"
 *         In segmented mode, use the provided trigger channel.
 *         In single-array mode, fall back to the current signal.
 *     - "independent"
 *         Each channel computes its own support independently.
 *     - "<detector_name>"
 *         Use the named detector or channel as a shared support channel.
 *
 * threshold :
 *     Relative threshold in the interval [0, 1].
 */
class PulseSupport : public BaseSupport {
public:
    std::string channel;
    double threshold;

    PulseSupport(
        const std::string& channel = "default",
        double threshold = 0.5
    );

    ~PulseSupport() override = default;

    bool is_full_window() const override;
    bool is_independent() const override;
    std::string get_channel() const override;
    double get_threshold() const override;
    std::string get_name() const override;
};


/**
 * @brief Abstract base class for peak detection on 1D signals.
 *
 * This class provides:
 * - validation utilities
 * - metric storage
 * - metric computation helpers
 * - segmented batch processing
 *
 * Concrete subclasses define how the peak index is chosen.
 */
class BasePeakLocator {
public:
    bool compute_width;
    bool compute_area;
    bool allow_negative_area;
    int padding_value;
    int max_number_of_peaks;
    bool debug_mode;
    std::shared_ptr<BaseSupport> support;

    std::vector<int> peak_indices;
    std::vector<double> peak_heights;
    std::vector<double> peak_widths;
    std::vector<double> peak_areas;

    BasePeakLocator(
        bool compute_width,
        bool compute_area,
        bool allow_negative_area,
        int padding_value,
        int max_number_of_peaks,
        std::shared_ptr<BaseSupport> support,
        bool debug_mode
    );

    virtual ~BasePeakLocator() = default;

    /**
     * @brief Validate that an input signal is not empty.
     *
     * Parameters
     * ----------
     * array :
     *     Input signal values.
     *
     * Throws
     * ------
     * std::runtime_error
     *     If the signal is empty.
     */
    void validate_input_signal(const std::vector<double>& array) const;

    /**
     * @brief Find the index of the maximum value in [start, end).
     *
     * Parameters
     * ----------
     * ptr :
     *     Pointer to the signal data.
     * start :
     *     Inclusive interval start.
     * end :
     *     Exclusive interval end.
     *
     * Returns
     * -------
     * size_t
     *     Index of the maximum sample inside the interval.
     */
    size_t find_local_peak(
        const double* ptr,
        size_t start,
        size_t end
    ) const;

    /**
     * @brief Compute support boundaries around a peak.
     *
     * Behavior depends on the configured support object.
     *
     * - FullWindowSupport
     *     The support is the full interval [start, end).
     *
     * - PulseSupport
     *     The support is expanded around a positive peak while neighboring
     *     samples remain above
     *
     *         threshold * peak_height
     *
     * Parameters
     * ----------
     * ptr :
     *     Pointer to the support signal data.
     * start :
     *     Inclusive interval start.
     * end :
     *     Exclusive interval end.
     * peak_index :
     *     Index of the peak used to define the support.
     * left_boundary :
     *     Output inclusive left support boundary.
     * right_boundary :
     *     Output inclusive right support boundary.
     */
    void compute_boundaries(
        const double* ptr,
        size_t start,
        size_t end,
        size_t peak_index,
        size_t& left_boundary,
        size_t& right_boundary
    ) const;

    /**
     * @brief Compute width and area metrics inside a selected support.
     *
     * Parameters
     * ----------
     * ptr :
     *     Pointer to the value signal used for area accumulation.
     * start :
     *     Inclusive interval start.
     * end :
     *     Exclusive interval end.
     * peak_index :
     *     Peak index used to build the support.
     *
     * Returns
     * -------
     * PeakMetrics
     *     Width, area, and support boundary information.
     */
    PeakMetrics compute_segment_metrics(
        const double* ptr,
        const double* support_ptr,
        size_t start,
        size_t end,
        size_t peak_index
    ) const;

    /**
     * @brief Compute metrics for a single 1D signal using the same signal for
     * both value and support logic.
     *
     * Parameters
     * ----------
     * array :
     *     Input signal.
     *
     * Returns
     * -------
     * MetricDictionary
     *     Dictionary containing Index, Height, and optionally Width and Area.
     */
    MetricDictionary compute_metric_dictionary(
        const std::vector<double>& array
    ) const;

    /**
     * @brief Compute metrics for a value signal using a separate support signal.
     *
     * Parameters
     * ----------
     * value_signal :
     *     Signal used for height extraction and area accumulation.
     * support_signal :
     *     Signal used to define the support boundaries.
     *
     * Returns
     * -------
     * MetricDictionary
     *     Dictionary containing Index, Height, and optionally Width and Area.
     */
    MetricDictionary compute_metric_dictionary_with_shared_support(
        const std::vector<double>& value_signal,
        const std::vector<double>& support_signal
    ) const;

    /**
     * @brief Sort detected peaks by descending height.
     *
     * Parameters
     * ----------
     * peaks :
     *     Vector of detected peaks to sort in place.
     */
    void sort_peaks_descending(std::vector<PeakData>& peaks) const;

    /**
     * @brief Initialize the fixed-size output buffers with padding values.
     */
    void initialize_output_vectors();

    /**
     * @brief Compute metrics for a single signal and update internal buffers.
     *
     * Parameters
     * ----------
     * array :
     *     Input signal.
     */
    void compute(const std::vector<double>& array);

    /**
     * @brief Return one stored metric buffer.
     *
     * Parameters
     * ----------
     * metric_name :
     *     One of "Index", "Height", "Width", or "Area".
     *
     * Returns
     * -------
     * std::vector<double>
     *     Stored metric values.
     */
    std::vector<double> get_metric_py(const std::string& metric_name) const;

    /**
     * @brief Compute and return metrics for a single signal.
     *
     * Parameters
     * ----------
     * array :
     *     Input signal.
     *
     * Returns
     * -------
     * MetricDictionary
     *     Dictionary containing computed metrics.
     */
    MetricDictionary get_metrics(const std::vector<double>& array);

    /**
     * @brief Compute metrics for all channels in segmented multi-channel data.
     *
     * Parameters
     * ----------
     * segmented_signals :
     *     Nested segmented dictionary.
     * trigger_channel :
     *     Trigger channel name used when PulseSupport(channel="default") is
     *     configured.
     *
     * Returns
     * -------
     * SegmentedMetricDictionary
     *     Nested metric dictionary.
     */
    SegmentedMetricDictionary run_segmented_signals(
        const SegmentedSignalDictionary& segmented_signals,
        const std::string& trigger_channel = ""
    ) const;

    /**
     * @brief Regroup flat per-sample signals by segment id, then compute metrics.
     *
     * Parameters
     * ----------
     * segment_ids :
     *     Segment id associated with each sample.
     * flat_signals :
     *     Per-channel flat sample arrays.
     * trigger_channel :
     *     Trigger channel name used when PulseSupport(channel="default") is
     *     configured.
     *
     * Returns
     * -------
     * SegmentedMetricDictionary
     *     Nested metric dictionary.
     */
    SegmentedMetricDictionary run_flat_segmented_signals(
        const std::vector<int>& segment_ids,
        const FlatSignalDictionary& flat_signals,
        const std::string& trigger_channel = ""
    ) const;

    /**
     * @brief Resolve the support channel name for a given current channel.
     *
     * Parameters
     * ----------
     * channel_dictionary :
     *     Map of channels available in the current segment.
     * current_channel_name :
     *     Channel currently being evaluated.
     * trigger_channel :
     *     Trigger channel name supplied by the caller.
     *
     * Returns
     * -------
     * std::string
     *     Resolved support channel name.
     */
    std::string resolve_support_channel_name(
        const std::map<std::string, std::vector<double>>& channel_dictionary,
        const std::string& current_channel_name,
        const std::string& trigger_channel
    ) const;

    /**
     * @brief Detect peaks using one signal for both peak selection and support.
     *
     * Parameters
     * ----------
     * signal :
     *     Input signal.
     *
     * Returns
     * -------
     * std::vector<PeakData>
     *     Detected peaks.
     */
    virtual std::vector<PeakData> locate_peaks(
        const std::vector<double>& signal
    ) const = 0;

    /**
     * @brief Detect peaks using a value signal and a separate support signal.
     *
     * Parameters
     * ----------
     * value_signal :
     *     Signal used for peak value extraction and area accumulation.
     * support_signal :
     *     Signal used to define support boundaries.
     *
     * Returns
     * -------
     * std::vector<PeakData>
     *     Detected peaks.
     */
    virtual std::vector<PeakData> locate_peaks_with_support(
        const std::vector<double>& value_signal,
        const std::vector<double>& support_signal
    ) const = 0;
};


/**
 * @brief Peak locator that extracts one local maximum per sliding window.
 *
 * One peak is selected in each window and the resulting peaks are sorted by
 * descending height before being written to the fixed-size output buffers.
 */
class SlidingWindowPeakLocator : public BasePeakLocator {
public:
    int window_size;
    int window_step;

    SlidingWindowPeakLocator(
        int window_size,
        int window_step,
        int max_number_of_peaks,
        int padding_value,
        bool compute_width,
        bool compute_area,
        bool allow_negative_area,
        std::shared_ptr<BaseSupport> support,
        bool debug_mode
    );

    std::vector<PeakData> locate_peaks(
        const std::vector<double>& signal
    ) const override;

    std::vector<PeakData> locate_peaks_with_support(
        const std::vector<double>& value_signal,
        const std::vector<double>& support_signal
    ) const override;
};


/**
 * @brief Peak locator that extracts the single strongest sample in a signal.
 *
 * Only one physical peak is detected in the full signal. Output buffers still
 * honor the configured maximum number of peaks and are padded when needed.
 */
class GlobalPeakLocator : public BasePeakLocator {
public:
    GlobalPeakLocator(
        int max_number_of_peaks,
        int padding_value,
        bool compute_width,
        bool compute_area,
        bool allow_negative_area,
        std::shared_ptr<BaseSupport> support,
        bool debug_mode
    );

    std::vector<PeakData> locate_peaks(
        const std::vector<double>& signal
    ) const override;

    std::vector<PeakData> locate_peaks_with_support(
        const std::vector<double>& value_signal,
        const std::vector<double>& support_signal
    ) const override;
};
