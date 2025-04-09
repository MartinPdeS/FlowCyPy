#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;


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
void baseline_restoration(py::buffer signal, const int window_size);


/**
 * @brief Applies a low-pass filter to a 1D signal using FFT.
 *
 * This function performs a low-pass filtering operation on a 1D NumPy array
 * (with float64 data type) by transforming the signal to the frequency domain,
 * applying a frequency-dependent attenuation (a Butterworth-like filter), and then
 * transforming the filtered signal back to the time domain using the inverse FFT.
 *
 * The filter transfer function is defined as:
 *     H(f) = (1 / sqrt(1 + (f/cutoff_frequency)^2))^order,
 * where @c cutoff_frequency sets the cutoff point and @c order controls the steepness
 * of the filter's roll-off. After filtering, the signal is scaled by the @c gain factor.
 *
 * @param signal A 1D NumPy array of type float64 representing the input signal.
 * @param dt The sampling interval (time step) of the signal.
 * @param cutoff_frequency The cutoff frequency for the low-pass filter.
 * @param order The order of the filter, determining the sharpness of the frequency cutoff.
 * @param gain A gain factor to scale the filtered signal.
 *
 * @throws std::runtime_error If the input array is not a 1D float64 NumPy array.
 */
void butterworth_lowpass_filter(const py::buffer signal, const double sampling_rate, const double cutoff_freq, const int order = 1, const double gain = 1);


/**
 * @brief Applies a Bessel low-pass filter to a 1D signal using FFT.
 *
 * This function applies a Bessel low-pass filter to a 1D NumPy array (float64) by
 * transforming the signal into the frequency domain, applying the Bessel filter's
 * frequency response, and transforming the filtered signal back to the time domain.
 *
 * The filter is implemented using a frequency-domain approach where the transfer
 * function \(H(f)\) is computed for a Bessel filter of a specified order.
 *
 * The following orders are supported:
 * - Order 1: \( H(s) = \frac{1}{s+1} \)
 * - Order 2: \( H(s) = \frac{3}{s^2+3s+3} \)
 * - Order 3: \( H(s) = \frac{15}{s^3+6s^2+15s+15} \)
 * - Order 4: \( H(s) = \frac{105}{s^4+10s^3+45s^2+105s+105} \)
 *
 * In each case, \( s \) is defined as \( s = j \,(f/\text{cutoff_frequency}) \),
 * where \( f \) is the frequency, and the constants (1, 3, 15, 105) normalize the
 * filter so that \( H(0) = 1 \).
 *
 * After filtering, the output signal is scaled by the provided gain factor.
 *
 * @param signal A 1D NumPy array of type float64 representing the input signal.
 * @param dt The sampling interval (time step) of the signal.
 * @param cutoff_frequency The cutoff frequency of the Bessel low-pass filter.
 * @param order The order of the Bessel filter (supported orders: 1, 2, 3, or 4).
 * @param gain A gain factor to scale the filtered signal.
 *
 * @throws std::runtime_error If the input is not a 1D float64 array, or if the specified
 *         filter order is not implemented.
 */
void bessel_lowpass_filter(const py::buffer signal, const double sampling_rate, const double cutoff_frequency, const int order, const double gain);


/**
 * @brief Generates a composite signal with Gaussian pulses on a constant background.
 *
 * This function computes a composite signal by adding one or more Gaussian pulses to a
 * constant background power level. Each pulse is defined by its width, center, and coupling power.
 * The resulting signal is stored in an internal buffer of the SignalGenerator object.
 *
 * The process is as follows:
 * - The output signal is first initialized with the background_power at every time point.
 * - For each pulse, a Gaussian function is evaluated at each time value. The Gaussian is given by:
 *   \f[
 *       \text{gauss\_val} = \text{coupling\_power}[i] \times \exp\left(-\frac{(t - \text{centers}[i])^2}{2 \times \text{widths}[i]^2}\right)
 *   \f]
 *   where \f$t\f$ is the current time from the time buffer.
 * - The computed Gaussian value is then added to the output signal at the corresponding time point.
 *
 * @param widths A 1D py::buffer containing the pulse widths (standard deviations) for each pulse.
 * @param centers A 1D py::buffer containing the center times for each pulse.
 * @param coupling_power A 1D py::buffer containing the amplitude (coupling power) for each pulse.
 * @param time A 1D py::buffer containing the time values at which the signal is evaluated.
 * @param background_power The constant background power to be added to the signal.
 *
 * @throws std::runtime_error If the sizes of the widths, centers, and coupling_power buffers are not equal.
 */
void generate_pulses(py::buffer signal, const py::buffer &widths, const py::buffer &centers, const py::buffer &coupling_power, const py::buffer &time, const double background_power);


/**
 * @brief Adds Gaussian noise to a 1D signal.
 *
 * This function adds Gaussian (normally distributed) noise to a 1D NumPy array in-place.
 * The noise is generated using a normal distribution with the specified mean and standard deviation.
 *
 * The input signal must be a 1D NumPy array of type float64. If the input array does not meet
 * these requirements, the function throws a std::runtime_error.
 *
 * @param signal A 1D NumPy array (float64) representing the signal to which noise will be added.
 * @param mean The mean of the Gaussian noise.
 * @param standard_deviation The standard deviation of the Gaussian noise.
 *
 * @throws std::runtime_error If the input array is not a 1D float64 NumPy array.
 */
void add_gaussian_noise(py::buffer signal, const double mean, const double standard_deviation);


/**
 * @brief Adds Poisson noise to a 1D signal.
 *
 * This function modifies a 1D NumPy array (float64) in-place by replacing each element with a random
 * value drawn from a Poisson distribution whose mean is the original value at that element.
 * Poisson noise is typically used to simulate counting statistics in signals that represent intensities
 * or photon counts.
 *
 * The input array must be a 1D NumPy array of type float64. Additionally, every element of the array
 * must be non-negative because the Poisson distribution is only defined for non-negative mean values.
 *
 * @param signal A 1D NumPy array (float64) representing the signal to which Poisson noise will be applied.
 *
 * @throws std::runtime_error If the input array is not a 1D float64 NumPy array or if any element is negative.
 */
void add_poisson_noise(py::buffer signal);

