#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include "filter.h"

namespace py = pybind11;

void dummy_function();


/**
 * @brief Validates if the specified detector exists in the given map.
 *
 * @param map The map containing detector data.
 * @param detector_name The name of the detector to check.
 * @param error_message The error message to throw if not found.
 * @throws std::runtime_error if the detector is not found in the map.
 */
void validate_detector_existence(const std::map<std::string, py::array_t<double>> &map, const std::string &detector_name, const std::string &error_message);



/**
 * @brief Identifies trigger points where the signal crosses a given threshold.
 *
 * @param trigger_signal Pointer to the signal array.
 * @param signal_size Number of samples in the signal.
 * @param threshold The trigger threshold.
 * @return A vector of indices where the signal crosses the threshold.
 */
std::vector<int> find_trigger_indices(double *trigger_signal, size_t signal_size, double threshold);


/**
 * @brief Applies pre-buffer and post-buffer constraints to trigger indices, ensuring no overlap.
 *
 * @param trigger_indices Vector of raw trigger indices.
 * @param pre_buffer Number of points before the trigger.
 * @param post_buffer Number of points after the trigger.
 * @param signal_size Total number of samples in the signal.
 * @param max_triggers Maximum number of allowed triggers.
 * @return A vector of valid (start, end) trigger segments.
 */
std::vector<std::pair<int, int>> apply_buffer_constraints(const std::vector<int> &trigger_indices, int pre_buffer, int post_buffer, int signal_size, int max_triggers);

/**
 * @brief Extracts signal segments based on trigger points for all detectors.
 *
 * @param signal_map Map of signals for each detector.
 * @param time_map Map of time values for each detector.
 * @param valid_triggers List of valid trigger segments (start, end).
 * @return Tuple containing NumPy arrays for times, signals, detector names, and segment IDs.
 */
std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> extract_signal_segments(const std::map<std::string, py::array_t<double>> &signal_map, const std::map<std::string, py::array_t<double>> &time_map, const std::vector<std::pair<int, int>> &valid_triggers);


/**
 * @brief Executes triggered acquisition analysis with optional baseline restoration and low-pass filtering.
 *
 * This function identifies trigger events in a signal using a specified threshold, applies pre/post-buffer constraints,
 * and extracts signal segments from multiple detectors based on detected triggers. Optionally, it performs baseline
 * restoration and applies a Bessel low-pass filter to the signals before thresholding.
 *
 * ## Workflow:
 * 1. **Validate Trigger Detector**: Ensures the specified trigger detector exists in `signal_map` and `time_map`.
 * 2. **Apply Baseline Restoration** *(Optional)*: Subtracts the rolling minimum of the last `baseline_window_size` points.
 * 3. **Apply Low-Pass Filtering** *(Optional)*: Uses a Bessel filter to smooth out high-frequency noise.
 * 4. **Detect Trigger Events**: Finds threshold crossings in the processed trigger signal.
 * 5. **Apply Buffer Constraints**: Ensures non-overlapping trigger events within the signal.
 * 6. **Extract Signal Segments**: Retrieves the relevant portions of signals for all detectors.
 *
 * @param signal_map
 *      A dictionary mapping detector names to their respective signal data (NumPy arrays).
 * @param time_map
 *      A dictionary mapping detector names to their corresponding time values (NumPy arrays).
 * @param trigger_detector_name
 *      The name of the detector whose signal is used for triggering events.
 * @param threshold
 *      The signal threshold value used to detect trigger events.
 * @param pre_buffer
 *      The number of samples to include before the trigger point (default: 64).
 * @param post_buffer
 *      The number of samples to include after the trigger point (default: 64).
 * @param filter_gain
 *      The gain factor applied to the filtered signal (default: 1).
 * @param filter_order
 *      The order of the Bessel low-pass filter (default: 4).
 * @param filter_lowpass_cutoff
 *      The cutoff frequency for the low-pass filter in Hz. If set to `-1`, filtering is skipped (default: -1).
 * @param baseline_window_size
 *      The number of previous samples to consider for baseline restoration. If set to `-1`, baseline restoration is skipped (default: 20).
 * @param max_triggers
 *      The maximum number of triggers to process. If set to `-1`, all triggers are processed (default: -1).
 *
 * @return
 *      A tuple containing:
 *      - **times** (`py::array_t<double>`): Extracted time values corresponding to the triggered segments.
 *      - **signals** (`py::array_t<double>`): Extracted signal values corresponding to the triggered segments.
 *      - **detector_names** (`py::list`): A list of detector names associated with each triggered segment.
 *      - **segment_ids** (`py::array_t<int>`): A list of segment IDs corresponding to each detected trigger.
 *
 * @throws std::runtime_error
 *      If the specified trigger detector is not found in `signal_map` or `time_map`.
 * @throws std::invalid_argument
 *      If the specified filter cutoff frequency is greater than the Nyquist frequency.
 *
 * @note
 *      - The function applies **baseline restoration** *before* thresholding.
 *      - The **low-pass filter** is applied to smooth the signal, but only if `filter_lowpass_cutoff` is specified.
 *      - If no valid triggers are found, the function returns empty arrays.
 */

 #include <iostream>
std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_triggering(std::map<std::string, py::array_t<double>> signal_map, std::map<std::string, py::array_t<double>> time_map, const std::string &trigger_detector_name, double threshold, int pre_buffer = 64, int post_buffer = 64, int max_triggers = -1);