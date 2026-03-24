#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif


/**
 * @brief Metrics computed over the support of a detected peak.
 *
 * The peak width is expressed in number of samples. The peak area is the raw
 * sum of the signal values inside the detected peak boundaries.
 */
struct PeakMetrics {
    double width;
    double area;
};


/**
 * @brief Temporary container used to store a detected peak before final output.
 *
 * Instances of this structure are used internally to gather peak candidates,
 * sort them by descending amplitude, and then copy the strongest ones into the
 * fixed size output vectors of the locator.
 */
struct PeakData {
    int index;
    double value;
    double width;
    double area;

    /**
     * @brief Construct a peak description.
     *
     * @param index
     *     Index of the detected peak in the signal.
     * @param value
     *     Peak height.
     * @param width
     *     Peak width in samples. May remain equal to the padding value when
     *     width computation is disabled.
     * @param area
     *     Peak area. May remain equal to the padding value when area
     *     computation is disabled.
     */
    PeakData(
        int index,
        double value,
        double width,
        double area
    )
        : index(index),
          value(value),
          width(width),
          area(area)
    {}
};


/**
 * @brief Metric dictionary for one processed signal.
 *
 * Typical keys are:
 *     - "Index"
 *     - "Height"
 *     - "Width"
 *     - "Area"
 *
 * Width and area are only present when explicitly requested.
 */
using MetricDictionary = std::unordered_map<std::string, std::vector<double>>;


/**
 * @brief Dictionary of signal channels for one segment.
 *
 * The key is the channel name, for example "forward" or "side", and the value
 * is the corresponding 1D signal.
 */
using ChannelDictionary = std::unordered_map<std::string, std::vector<double>>;


/**
 * @brief Dictionary of segmented input signals.
 *
 * The top level key is the segment identifier. Each segment contains a channel
 * dictionary with one 1D signal per channel.
 */
using SegmentedSignalDictionary = std::unordered_map<int, ChannelDictionary>;


/**
 * @brief Dictionary of computed metrics for segmented signals.
 *
 * Structure:
 *
 *     segment_id -> channel_name -> metric_name -> values
 */
using SegmentedMetricDictionary = std::unordered_map<
    int,
    std::unordered_map<std::string, MetricDictionary>
>;


/**
 * @brief Flat dictionary of signal channels.
 *
 * This container stores only actual signal channels from the flat
 * discriminator output. Metadata such as "segment_id" and "Time" must not be
 * stored here.
 */
using FlatSignalDictionary = std::unordered_map<std::string, std::vector<double>>;


/**
 * @brief Base class for 1D peak locators.
 *
 * This class owns the common parameters, internal output buffers, and utility
 * methods shared by different peak locator strategies. Derived classes must
 * implement a stateless peak search method for one 1D signal.
 *
 * Single signal processing keeps the original stateful behavior through the
 * fixed size output buffers:
 *     - peak_indices
 *     - peak_heights
 *     - peak_widths
 *     - peak_areas
 *
 * Segmented batch processing uses a stateless internal path so it can be
 * parallelized safely.
 */
class BasePeakLocator {
public:
    bool compute_width;
    bool compute_area;
    int padding_value;
    int max_number_of_peaks;

    std::vector<int> peak_indices;
    std::vector<double> peak_heights;
    std::vector<double> peak_widths;
    std::vector<double> peak_areas;

    /**
     * @brief Construct a base peak locator.
     *
     * @param compute_width
     *     If true, compute the width of each detected peak.
     * @param compute_area
     *     If true, compute the area of each detected peak.
     * @param padding_value
     *     Value used to pad unused output entries when fewer than
     *     `max_number_of_peaks` peaks are available.
     * @param max_number_of_peaks
     *     Maximum number of peaks to report.
     */
    BasePeakLocator(
        bool compute_width,
        bool compute_area,
        int padding_value,
        int max_number_of_peaks
    );

    /**
     * @brief Virtual destructor.
     */
    virtual ~BasePeakLocator() = default;

    /**
     * @brief Locate peak candidates for a single 1D signal.
     *
     * Derived classes must return peak candidates for the provided signal.
     * The base class is responsible for sorting them and formatting the final
     * fixed size metric outputs.
     *
     * @param array
     *     Input 1D signal.
     *
     * @return
     *     Peak candidate list.
     */
    virtual std::vector<PeakData> locate_peaks(
        const std::vector<double>& array
    ) const = 0;

    /**
     * @brief Compute peaks for a single 1D signal.
     *
     * Derived classes are not required to override this method. It uses the
     * stateless `locate_peaks(...)` path, then updates the internal fixed size
     * output buffers.
     *
     * @param array
     *     Input 1D signal.
     */
    virtual void compute(const std::vector<double>& array);

    /**
     * @brief Return one already computed metric as a vector of doubles.
     *
     * @param metric_name
     *     Name of the requested metric. Must be one of:
     *         - "Index"
     *         - "Height"
     *         - "Width"
     *         - "Area"
     *
     * @return
     *     Requested metric vector.
     */
    std::vector<double> get_metric_py(const std::string& metric_name) const;

    /**
     * @brief Compute all enabled metrics for a single 1D signal.
     *
     * This method executes the locator on one signal and returns the metrics as
     * a dictionary.
     *
     * @param array
     *     Input 1D signal.
     *
     * @return
     *     Dictionary containing at least "Index" and "Height", and optionally
     *     "Width" and "Area".
     */
    MetricDictionary get_metrics(const std::vector<double>& array);

    /**
     * @brief Compute peak metrics for all channels of all segments.
     *
     * This batch method keeps the main loops in C++. Each channel is processed
     * independently using a stateless internal path, which makes the method
     * safe to parallelize.
     *
     * @param segmented_signals
     *     Nested segmented signal dictionary.
     *
     * @return
     *     Nested segmented metric dictionary:
     *
     *         segment_id -> channel_name -> metric_name -> values
     */
    SegmentedMetricDictionary run_segmented_signals(
        const SegmentedSignalDictionary& segmented_signals
    ) const;

    /**
     * @brief Compute peak metrics for the flat segmented signal format.
     *
     * The flat input format is:
     *
     *     "segment_id" -> one segment id per sample
     *     "channel_name" -> one signal value per sample
     *
     * The regrouping is handled in C++, then batch processing is delegated to
     * `run_segmented_signals(...)`.
     *
     * @param segment_ids
     *     Segment identifier for each sample.
     * @param flat_signals
     *     Flat dictionary containing only actual signal channels.
     *
     * @return
     *     Nested segmented metric dictionary:
     *
     *         segment_id -> channel_name -> metric_name -> values
     */
    SegmentedMetricDictionary run_flat_segmented_signals(
        const std::vector<int>& segment_ids,
        const FlatSignalDictionary& flat_signals
    ) const;

    /**
     * @brief Initialize all internal output vectors with padded default values.
     *
     * The vectors are resized to `max_number_of_peaks`. Index vectors are
     * padded with `padding_value`, while floating point outputs are padded with
     * the same value cast to double.
     */
    void initialize_output_vectors();

    /**
     * @brief Sort peaks by descending peak height.
     *
     * @param peaks
     *     Peak container to sort in place.
     */
    void sort_peaks_descending(std::vector<PeakData>& peaks) const;

    /**
     * @brief Find the index of the maximum element inside a half open interval.
     *
     * The interval follows the convention [start, end).
     *
     * @param ptr
     *     Pointer to the signal data.
     * @param start
     *     Inclusive start index.
     * @param end
     *     Exclusive end index.
     *
     * @return
     *     Index of the maximum element in the requested interval.
     */
    size_t find_local_peak(
        const double* ptr,
        size_t start,
        size_t end
    ) const;

    /**
     * @brief Compute width and area for a detected peak.
     *
     * Peak boundaries are obtained from `compute_boundaries`, then the width and
     * area are computed over that support.
     *
     * @param ptr
     *     Pointer to the signal data.
     * @param start
     *     Inclusive start index of the valid region.
     * @param end
     *     Exclusive end index of the valid region.
     * @param peak_index
     *     Index of the detected peak.
     * @param threshold
     *     Fraction of peak height used to determine the boundaries.
     *
     * @return
     *     Structure containing width and area.
     */
    PeakMetrics compute_segment_metrics(
        const double* ptr,
        size_t start,
        size_t end,
        size_t peak_index,
        double threshold
    ) const;

    /**
     * @brief Compute left and right boundaries of a peak.
     *
     * The boundaries are expanded away from the peak until the signal falls
     * below `threshold * peak_value`.
     *
     * @param ptr
     *     Pointer to the signal data.
     * @param start
     *     Inclusive start index of the valid region.
     * @param end
     *     Exclusive end index of the valid region.
     * @param peak_index
     *     Index of the peak.
     * @param threshold
     *     Fraction of the peak height used as the cutoff.
     * @param left_boundary
     *     Output left boundary index.
     * @param right_boundary
     *     Output right boundary index.
     */
    void compute_boundaries(
        const double* ptr,
        size_t start,
        size_t end,
        size_t peak_index,
        double threshold,
        size_t& left_boundary,
        size_t& right_boundary
    ) const;

protected:
    /**
     * @brief Validate one input signal.
     *
     * @param array
     *     Input signal.
     */
    void validate_input_signal(const std::vector<double>& array) const;

    /**
     * @brief Compute a fixed size metric dictionary from one signal.
     *
     * This is the stateless path used internally by segmented batch execution.
     *
     * @param array
     *     Input signal.
     *
     * @return
     *     Fixed size metric dictionary.
     */
    MetricDictionary compute_metric_dictionary(
        const std::vector<double>& array
    ) const;
};


/**
 * @brief Peak locator based on sliding windows.
 *
 * The signal is split into successive windows. One local maximum is extracted
 * per window, optional peak metrics are computed within that window, and the
 * resulting peaks are ranked by descending height.
 */
class SlidingWindowPeakLocator : public BasePeakLocator {
public:
    int window_size;
    int window_step;
    double threshold;

    /**
     * @brief Construct a sliding window peak locator.
     *
     * @param window_size
     *     Number of samples per window.
     * @param window_step
     *     Step between consecutive windows. If set to -1, it defaults to
     *     `window_size`, which gives non overlapping windows.
     * @param max_number_of_peaks
     *     Maximum number of peaks to report.
     * @param padding_value
     *     Padding value for unused output entries.
     * @param compute_width
     *     If true, compute the width of each detected peak.
     * @param compute_area
     *     If true, compute the area of each detected peak.
     * @param threshold
     *     Fraction of peak height used to determine the support of the peak
     *     when computing width and area.
     */
    SlidingWindowPeakLocator(
        int window_size,
        int window_step = -1,
        int max_number_of_peaks = 5,
        int padding_value = -1,
        bool compute_width = false,
        bool compute_area = false,
        double threshold = 0.5
    );

    /**
     * @brief Locate peaks for one 1D signal using a sliding window strategy.
     *
     * @param array
     *     Input 1D signal.
     *
     * @return
     *     Peak candidate list.
     */
    std::vector<PeakData> locate_peaks(
        const std::vector<double>& array
    ) const override;
};


/**
 * @brief Peak locator that finds the global maximum of a signal.
 *
 * Only one physical peak is searched in the full signal. The first output entry
 * stores that peak, and the remaining entries are padded if
 * `max_number_of_peaks` is larger than one.
 */
class GlobalPeakLocator : public BasePeakLocator {
public:
    double threshold;

    /**
     * @brief Construct a global peak locator.
     *
     * @param max_number_of_peaks
     *     Maximum number of peaks to report. Only one actual peak is detected,
     *     so remaining entries are padded.
     * @param padding_value
     *     Padding value for unused output entries.
     * @param compute_width
     *     If true, compute the width of the detected peak.
     * @param compute_area
     *     If true, compute the area of the detected peak.
     * @param threshold
     *     Fraction of peak height used to determine the support of the peak
     *     when computing width and area.
     */
    GlobalPeakLocator(
        int max_number_of_peaks = 1,
        int padding_value = -1,
        bool compute_width = false,
        bool compute_area = false,
        double threshold = 0.5
    );

    /**
     * @brief Locate the global peak of one 1D signal.
     *
     * @param array
     *     Input 1D signal.
     *
     * @return
     *     Peak candidate list containing one peak.
     */
    std::vector<PeakData> locate_peaks(
        const std::vector<double>& array
    ) const override;
};
