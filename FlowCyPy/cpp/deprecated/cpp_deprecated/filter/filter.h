#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>


namespace py = pybind11;

/**
 * @brief Calculate the start and end indices for triggered segments.
 *
 * This function computes rising-edge indices from a 1D signal array where the signal crosses
 * a specified threshold. It then applies pre- and post-buffer clipping and suppresses overlapping
 * triggers to avoid retriggering within an active buffer period.
 *
 * @param signal A 1D numpy array of doubles representing the signal.
 * @param threshold The threshold value for triggering.
 * @param pre_buffer Number of samples to include before the trigger point (default 64).
 * @param post_buffer Number of samples to include after the trigger point (default 64).
 * @return A tuple containing two numpy arrays (start_indices, end_indices).
 * @throws std::runtime_error if the input signal is not 1-dimensional.
 */
std::tuple<py::array_t<int>, py::array_t<int>> get_trigger_indices(py::array_t<double> signal, double threshold, int pre_buffer, int post_buffer);



/**
 * @brief Applies an in-place cascaded first-order low-pass filter to approximate a Bessel filter.
 *
 * This function modifies the input signal directly. It applies a cascade of first-order RC low-pass filters,
 * which often provides a smoother (and more linear phase) response than a single high‑order filter.
 * The filter is implemented in a stable manner and includes a gain factor applied after filtering.
 *
 * @param signal The signal vector to be filtered (modified in place).
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param order The number of first-order stages to cascade (default: 4).
 * @param gain The gain factor to be applied after filtering (default: 1.0).
 *
 * @throws std::invalid_argument if cutoff_freq >= (sampling_rate / 2).
 */
void apply_bessel_lowpass_filter_(std::vector<double>& signal, double sampling_rate, double cutoff_freq, int order, double gain);


/**
 * @brief Pybind11 wrapper for in-place Bessel-like low-pass filtering of a NumPy array.
 *
 * This function extracts the underlying writable NumPy data from the provided array,
 * converts it to a std::vector, applies the cascaded first-order filtering (to approximate a Bessel filter),
 * and then writes the modified data back in place.
 *
 * @param py_signal NumPy array containing the signal to be filtered.
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param order The number of first-order stages to cascade (default: 4).
 * @param gain The gain factor applied after filtering (default: 1.0).
 */
void apply_bessel_lowpass_filter(py::array_t<double>& py_signal, double sampling_rate, double cutoff_freq, int order, double gain);


/**
 * @brief Applies a first-order Butterworth low-pass filter in-place.
 *
 * This function processes the input signal using a first-order Butterworth filter.
 * It uses the exponential smoothing formula:
 *
 *     y[n] = α * x[n] + (1 - α) * y[n-1]
 *
 * where α = dt / (RC + dt) and RC = 1 / (2π * cutoff_freq).
 *
 * @param signal The signal vector to be filtered (modified in place).
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param gain The gain applied to the filtered signal (default: 1.0).
 */
void apply_first_order_butterworth_filter(std::vector<double>& signal, double sampling_rate, double cutoff_freq, double gain);


/**
 * @brief Applies an in-place Butterworth low-pass filter to the signal stored in a NumPy array,
 *        by cascading first-order filters.
 *
 * This function modifies the provided NumPy array in-place. It converts the array to a vector,
 * applies a cascade of first-order Butterworth filters (e.g. 4 in cascade for a 4th order effect),
 * and then writes the modified data back into the array.
 *
 * @param py_signal NumPy array containing the signal to be filtered.
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param num_stages The number of first-order filters to cascade (default: 4).
 * @param gain The gain factor applied after filtering (default: 1.0)
 */
void apply_butterworth_lowpass_filter(py::array_t<double>& py_signal, double sampling_rate, double cutoff_freq, int num_stages, double gain);



/**
 * @brief Performs baseline restoration on a signal using a rolling window minimum.
 *
 * For each index \( i \) (with \( i \ge 1 \)) in the input signal, this function computes
 * the minimum value among the previous `window_size` samples (i.e. indices from
 * \(\max(0, i - \text{window_size})\) to \( i-1 \)) based on the original unmodified signal.
 * It then subtracts that minimum value from the current sample.
 *
 * If `window_size == -1`, then for each \( i > 0 \) the function uses the minimum value
 * from indices \([0, i)\).
 *
 * @param signal The input signal vector. The function does not update the original signal in-place
 *               during computation; instead, it computes a new baseline-restored signal and writes
 *               it back into the same vector.
 * @param window_size The number of previous samples to consider for the minimum. If set to -1,
 *                    the window is treated as infinite (using all samples from index 0 to \(i-1\)).
 */
void compute_baseline_restoration(std::vector<double> &signal, int window_size);




/**
 * @brief Applies baseline restoration to all detectors in the signal map.
 *
 * This function modifies the `signal_map` **in-place**, ensuring that the
 * baseline-restored signal is stored back in `signal_map` before processing triggers.
 *
 * @param signal_map Dictionary of signals mapped to detector names.
 * @param window_size The sliding window size for baseline restoration.
 */
void apply_baseline_restoration(py::array_t<double> &signal_array, int window_size);
