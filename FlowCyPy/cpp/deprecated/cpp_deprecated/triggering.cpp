#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <tuple>
#include <string>
#include <map>
#include "filter.h"

namespace py = pybind11;


/**
 * @brief Validates if the specified detector exists in the given map.
 *
 * @param map The map containing detector data.
 * @param detector_name The name of the detector to check.
 * @param error_message The error message to throw if not found.
 * @throws std::runtime_error if the detector is not found in the map.
 */
void validate_detector_existence(
    const std::map<std::string, py::array_t<double>> &map,
    const std::string &detector_name,
    const std::string &error_message)
{
    if (map.find(detector_name) == map.end())
        throw std::runtime_error(error_message);
}

/**
 * @brief Identifies trigger points where the signal crosses a given threshold.
 *
 * @param trigger_signal Pointer to the signal array.
 * @param signal_size Number of samples in the signal.
 * @param threshold The trigger threshold.
 * @return A vector of indices where the signal crosses the threshold.
 */
std::vector<int> find_trigger_indices(
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
std::vector<std::pair<int, int>> apply_buffer_constraints(
    const std::vector<int> &trigger_indices,
    int pre_buffer,
    int post_buffer,
    int signal_size,
    int max_triggers)
{
    std::vector<std::pair<int, int>> valid_triggers;
    int last_end = -1;

    for (int idx : trigger_indices)
    {
        int start = idx - pre_buffer;
        int end = idx + post_buffer;

        // Ensure valid trigger range
        if (start < 0 || end >= signal_size)
            continue;

        // Avoid overlapping triggers
        if (start > last_end)
        {
            valid_triggers.emplace_back(start, end);
            last_end = end;
        }

        if (max_triggers > 0 && valid_triggers.size() >= static_cast<size_t>(max_triggers))
            break;
    }

    return valid_triggers;
}

/**
 * @brief Extracts signal segments based on trigger points for all detectors.
 *
 * @param signal_map Map of signals for each detector.
 * @param time_map Map of time values for each detector.
 * @param valid_triggers List of valid trigger segments (start, end).
 * @return Tuple containing NumPy arrays for times, signals, detector names, and segment IDs.
 */
std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> extract_signal_segments(
    const std::map<std::string, py::array_t<double>> &signal_map,
    const std::map<std::string, py::array_t<double>> &time_map,
    const std::vector<std::pair<int, int>> &valid_triggers)
{
    std::vector<double> times_out, signals_out;
    std::vector<std::string> detectors_out;
    std::vector<int> segment_ids_out;

    for (const auto &[detector_name, signal_array] : signal_map)
    {
        auto time_array = time_map.at(detector_name);

        py::buffer_info signal_buf = signal_array.request();
        py::buffer_info time_buf = time_array.request();

        if (signal_buf.ndim != 1 || time_buf.ndim != 1)
            throw std::runtime_error("Signal and time arrays must be 1D");

        size_t signal_size = signal_buf.shape[0];
        double *signal_ptr = static_cast<double *>(signal_buf.ptr);
        double *time_ptr = static_cast<double *>(time_buf.ptr);

        size_t segment_id = 0;
        for (const auto &[start, end] : valid_triggers)
        {
            for (int i = start; i <= end; ++i)
            {
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

    // Convert vector of strings to Python list
    py::list detector_list;
    for (const auto &detector : detectors_out)
        detector_list.append(detector);


    return std::make_tuple(
        py::array_t<double>(times_out.size(), times_out.data()),
        py::array_t<double>(signals_out.size(), signals_out.data()),
        detector_list,
        py::array_t<int>(segment_ids_out.size(), segment_ids_out.data()));
}


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
std::tuple<py::array_t<double>, py::array_t<double>, py::list, py::array_t<int>> run_triggering(
    std::map<std::string, py::array_t<double>> signal_map,
    std::map<std::string, py::array_t<double>> time_map,
    const std::string &trigger_detector_name,
    double threshold,
    int pre_buffer = 64,
    int post_buffer = 64,
    int max_triggers = -1)
{
    // Validate trigger detector
    validate_detector_existence(signal_map, trigger_detector_name, "Trigger detector not found in signal map.");
    validate_detector_existence(time_map, trigger_detector_name, "Trigger detector not found in time map.");

    // Get trigger detector data
    auto trigger_signal_array = signal_map.at(trigger_detector_name);
    auto trigger_time_array = time_map.at(trigger_detector_name);

    py::buffer_info trigger_signal_buf = trigger_signal_array.request();
    py::buffer_info trigger_time_buf = trigger_time_array.request();

    size_t n_trigger = trigger_signal_buf.shape[0];
    double *trigger_signal_ptr = static_cast<double *>(trigger_signal_buf.ptr);

    // Apply Baseline Restoration BEFORE thresholding
    std::vector<double> trigger_signal(trigger_signal_ptr, trigger_signal_ptr + n_trigger);

    // Find trigger indices using baseline-restored signal
    std::vector<int> trigger_indices = find_trigger_indices(trigger_signal.data(), n_trigger, threshold);

    // Apply buffer constraints
    std::vector<std::pair<int, int>> valid_triggers = apply_buffer_constraints(
        trigger_indices,
        pre_buffer - 1,
        post_buffer,
        static_cast<int>(n_trigger),
        max_triggers
    );

    if (valid_triggers.empty())
    {
        PyErr_WarnEx(PyExc_UserWarning, "No valid triggers found after baseline restoration. Returning empty arrays.", 1);
        return std::make_tuple(py::array_t<double>(0), py::array_t<double>(0), py::list(), py::array_t<int>(0));
    }

    // Extract triggered signal segments
    return extract_signal_segments(signal_map, time_map, valid_triggers);
}


PYBIND11_MODULE(triggering_system, module) {
    module.doc() = "Module for efficient signal processing and triggered acquisition using C++";

    // Expose run_triggering function with full filtering capabilities
    module.def("run", &run_triggering,
      py::arg("signal_map"),
      py::arg("time_map"),
      py::arg("trigger_detector_name"),
      py::arg("threshold"),
      py::arg("pre_buffer") = 64,
      py::arg("post_buffer") = 64,
      py::arg("max_triggers") = -1,               // Maximum number of trigger events (-1 for unlimited)
      "Executes triggered acquisition analysis with optional baseline restoration and Bessel low-pass filtering. "
      "Detects triggers based on a given threshold, applies pre/post-trigger buffers, and extracts signal segments "
      "from multiple detectors.");
}
