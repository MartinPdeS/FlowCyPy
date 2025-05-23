#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <tuple>
#include <cmath>
#include <map>
#include <limits>
#include "../utils/utils.h"

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
std::tuple<py::array_t<int>, py::array_t<int>> get_trigger_indices(
    py::array_t<double> signal,
    double threshold,
    int pre_buffer = 64,
    int post_buffer = 64)
{
    // Request a contiguous buffer from the input signal.
    auto buf = signal.request();
    if (buf.ndim != 1) {
        throw std::runtime_error("Input signal must be 1-dimensional");
    }
    size_t n = buf.shape[0];
    double* ptr = static_cast<double*>(buf.ptr);

    // Compute trigger_signal: true if signal value > threshold
    std::vector<bool> trigger_signal(n, false);
    for (size_t i = 0; i < n; i++) {
        trigger_signal[i] = (ptr[i] > threshold);
    }

    // Find rising edges: where the difference is 1 (i.e., transition from false to true)
    std::vector<int> crossings;
    for (size_t i = 1; i < n; i++) {
        if (!trigger_signal[i - 1] && trigger_signal[i]) {
            // Mimic np.where(np.diff(...)==1) by storing index i-1
            crossings.push_back(static_cast<int>(i - 1));
        }
    }

    // Compute start and end indices with buffers
    std::vector<int> start_indices, end_indices;
    for (int c : crossings) {
        int start_idx = std::max(0, c - pre_buffer);
        int end_idx = std::min(static_cast<int>(n - 1), c + post_buffer);
        start_indices.push_back(start_idx);
        end_indices.push_back(end_idx);
    }

    // Suppress retriggering: remove overlapping segments
    std::vector<int> suppressed_start, suppressed_end;
    int last_end = -1;
    for (size_t i = 0; i < start_indices.size(); i++) {
        if (start_indices[i] > last_end) {
            suppressed_start.push_back(start_indices[i]);
            suppressed_end.push_back(end_indices[i]);
            last_end = end_indices[i];
        }
    }

    // Create numpy arrays to return
    auto np_start = py::array_t<int>(suppressed_start.size());
    auto np_end = py::array_t<int>(suppressed_end.size());
    auto buf_start = np_start.request();
    auto buf_end = np_end.request();
    int* start_ptr = static_cast<int*>(buf_start.ptr);
    int* end_ptr = static_cast<int*>(buf_end.ptr);
    for (size_t i = 0; i < suppressed_start.size(); i++) {
        start_ptr[i] = suppressed_start[i];
    }
    for (size_t i = 0; i < suppressed_end.size(); i++) {
        end_ptr[i] = suppressed_end[i];
    }

    return std::make_tuple(np_start, np_end);
}

/**
 * @brief Applies an in-place cascaded first-order low-pass filter (approximating a Bessel filter) using FFT.
 *
 * This function converts the input signal into a NumPy array, applies an FFT-based low-pass filter that
 * cascades a first-order response 'order' times (emulating a Bessel-like filter), and then writes the filtered
 * signal back to the original vector with an overall gain applied.
 *
 * @param signal The signal vector to be filtered (modified in place).
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param order The number of first-order stages to cascade (default: 4).
 * @param gain The gain factor to be applied after filtering (default: 1.0).
 *
 * @throws std::invalid_argument if cutoff_freq >= (sampling_rate / 2).
 */
void apply_bessel_lowpass_filter_fft(std::vector<double>& signal, double sampling_rate, double cutoff_freq, int order = 4, double gain = 1.0)
{
    if (cutoff_freq >= (sampling_rate / 2.0))
    {
        throw std::invalid_argument("Cutoff frequency must be less than Nyquist frequency (sampling_rate / 2).");
    }

    size_t n_samples = signal.size();
    if(n_samples == 0)
        return;

    double dt = 1.0 / sampling_rate;

    // Wrap the input vector into a NumPy array (using the vector's data without copying).
    py::array_t<double> py_signal(n_samples, signal.data());

    // Call the FFT-based filter that now accepts an 'order' parameter to emulate cascaded filtering.
    py::array_t<double> filtered = fft_filter(py_signal, dt, cutoff_freq, order);

    // Retrieve the filtered result and apply the overall gain.
    py::buffer_info buf = filtered.request();
    double* filtered_data = static_cast<double*>(buf.ptr);
    for (size_t i = 0; i < n_samples; i++)
        signal[i] = filtered_data[i] * gain;

}


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
void apply_bessel_lowpass_filter_td(std::vector<double>& signal, double sampling_rate, double cutoff_freq, int order = 4, double gain = 1.0)
{
    if (cutoff_freq >= (sampling_rate / 2.0))
    {
        throw std::invalid_argument("Cutoff frequency must be less than Nyquist frequency (sampling_rate / 2).");
    }

    size_t n_samples = signal.size();
    if(n_samples == 0)
        return;

    // Sampling period and RC constant
    double T = 1.0 / sampling_rate;
    double RC = 1.0 / (2.0 * M_PI * cutoff_freq);
    double alpha = T / (RC + T);

    // Create a temporary buffer to hold the intermediate filtered signal
    std::vector<double> temp(signal);

    // Cascade the first-order filter "order" times
    for (int stage = 0; stage < order; stage++)
    {
        double y_prev = temp[0];
        for (size_t i = 0; i < n_samples; i++)
        {
            double y = alpha * temp[i] + (1.0 - alpha) * y_prev;
            temp[i] = y;
            y_prev = y;
        }
    }

    // Apply overall gain and copy the result back to the original signal
    for (size_t i = 0; i < n_samples; i++)
    {
        signal[i] = temp[i] * gain;
    }
}




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
void apply_bessel_lowpass_filter_py(py::array_t<double>& py_signal, double sampling_rate, double cutoff_freq, int order = 4, double gain = 1.0)
{
    py::buffer_info signal_buf = py_signal.request();
    size_t n_samples = signal_buf.shape[0];
    double* signal_ptr = static_cast<double*>(signal_buf.ptr);

    // Copy data into a vector
    std::vector<double> signal(signal_ptr, signal_ptr + n_samples);

    // Apply cascaded first-order low-pass filters (Bessel-like)
    apply_bessel_lowpass_filter_fft(signal, sampling_rate, cutoff_freq, order, gain);

    // Write back the modified data in-place
    std::memcpy(signal_ptr, signal.data(), n_samples * sizeof(double));
}

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
void apply_first_order_butterworth_filter_td(std::vector<double>& signal, double sampling_rate, double cutoff_freq, double gain = 1.0)
{
    if (cutoff_freq >= (sampling_rate / 2.0)) {
        throw std::invalid_argument("Cutoff frequency must be less than Nyquist frequency (sampling_rate / 2).");
    }

    size_t n_samples = signal.size();
    if(n_samples == 0)
        return;

    double dt = 1.0 / sampling_rate;
    double RC = 1.0 / (2.0 * M_PI * cutoff_freq);
    double alpha = dt / (RC + dt);

    double y_prev = signal[0];
    for (size_t i = 0; i < n_samples; i++) {
        double y = alpha * signal[i] + (1.0 - alpha) * y_prev;
        signal[i] = y * gain;
        y_prev = y;
    }
}

/**
 * @brief Applies an in-place Butterworth low-pass filter to the signal stored in a NumPy array,
 *        by cascading first-order filters using FFT.
 *
 * This function modifies the provided NumPy array in-place. It calls an FFT-based filter function
 * that emulates the cascading of first-order Butterworth filters (e.g., 4 cascaded filters for a 4th order effect)
 * and then writes the filtered data back to the original array.
 *
 * @param py_signal NumPy array containing the signal to be filtered.
 * @param sampling_rate The sampling rate in Hz.
 * @param cutoff_freq The cutoff frequency in Hz.
 * @param num_stages The number of first-order filters to cascade (default: 4).
 * @param gain The gain factor applied after filtering (default: 1.0).
 *
 * @throws std::invalid_argument if cutoff_freq >= (sampling_rate / 2).
 */
void apply_butterworth_lowpass_filter_py(py::array_t<double>& py_signal, double sampling_rate, double cutoff_freq, int num_stages = 4, double gain = 1.0)
{
    if (cutoff_freq >= (sampling_rate / 2.0)) {
        throw std::invalid_argument("Cutoff frequency must be less than Nyquist frequency (sampling_rate / 2).");
    }

    // Get the underlying NumPy array buffer.
    py::buffer_info signal_buf = py_signal.request();
    size_t n_samples = signal_buf.shape[0];
    double* signal_ptr = static_cast<double*>(signal_buf.ptr);

    // Compute the sampling period.
    double dt = 1.0 / sampling_rate;

    // Call the FFT-based filter with 'num_stages' (cascaded effect) using the order parameter.
    py::array_t<double> filtered = fft_filter(py_signal, dt, cutoff_freq, num_stages);

    // Retrieve the filtered data and apply the overall gain.
    py::buffer_info filtered_buf = filtered.request();
    double* filtered_data = static_cast<double*>(filtered_buf.ptr);
    for (size_t i = 0; i < n_samples; i++) {
        filtered_data[i] *= gain;
    }

    // Write the filtered data back into the original array (in-place modification).
    std::memcpy(signal_ptr, filtered_data, n_samples * sizeof(double));
}


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
void compute_baseline_restoration(std::vector<double> &signal, int window_size)
{
    size_t n = signal.size();

    // Make a copy of the original signal so that modifications do not affect future computations.
    std::vector<double> orig(signal);

    // Case: Infinite window (-1) => use all previous samples [0, i)
    if (window_size == -1)
    {
        double global_min = orig[0];
        // For i==0, no previous sample exists, so leave signal[0] unchanged.
        for (size_t i = 1; i < n; ++i)
        {
            global_min = std::min(global_min, orig[i]);  // Now look until the last point included
            // global_min = std::min(global_min, orig[i - 1]);  // Originally for look until the last point excluded
            signal[i] = orig[i] - global_min;
        }
        return;
    }

    // For a finite window: for each index i, consider the window [max(0, i-window_size), i)
    signal[0] = 0;  // No previous samples, so leave the first sample unchanged.
    for (size_t i = 1; i < n; ++i)
    {
        size_t start = (i < static_cast<size_t>(window_size)) ? 0 : i - window_size;
        double local_min = *std::min_element(orig.begin() + start, orig.begin() + i + 1);  // Now look until the last point included
        // double local_min = *std::min_element(orig.begin() + start, orig.begin() + i);  // Originally for look until the last point excluded
        signal[i] = orig[i] - local_min;
    }
}



/**
 * @brief Applies baseline restoration to all detectors in the signal map.
 *
 * This function modifies the `signal_map` **in-place**, ensuring that the
 * baseline-restored signal is stored back in `signal_map` before processing triggers.
 *
 * @param signal_map Dictionary of signals mapped to detector names.
 * @param window_size The sliding window size for baseline restoration.
 */
void apply_baseline_restoration(py::array_t<double> &signal_array, int window_size)
{
    py::buffer_info signal_buf = signal_array.request();
    size_t n = signal_buf.shape[0];

    double *signal_ptr = static_cast<double *>(signal_buf.ptr);
    std::vector<double> signal_vector(signal_ptr, signal_ptr + n);

    compute_baseline_restoration(signal_vector, window_size);

    // Store the modified signal back into the NumPy array
    std::memcpy(signal_ptr, signal_vector.data(), n * sizeof(double));
}



