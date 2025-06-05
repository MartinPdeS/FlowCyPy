#pragma once

#include <stdexcept>
#include <vector>
#include <random>
#include <fftw3.h>
#include <cmath>
#include <complex>
#include <algorithm>
#include <map>

class SignalGenerator {
public:
    std::map<std::string, std::vector<double>> data_dict;
    SignalGenerator(const size_t n_elements) : n_elements(n_elements) {}

    size_t n_elements;

    void create_zero_signal(const std::string &signal_name) {

        if (data_dict.find(signal_name) != data_dict.end())
            throw std::runtime_error("Signal with this name already exists.");

        this->data_dict[signal_name] = std::vector<double>(this->n_elements, 0.0);
    }

    void add_signal(const std::string &signal_name, const std::vector<double> &signal_data) {
        if (data_dict.find(signal_name) != data_dict.end())
            throw std::runtime_error("Signal with this name already exists.");

        if (signal_data.size() != this->n_elements)
            throw std::runtime_error("Signal data size does not match the number of elements.");

        this->data_dict[signal_name] = signal_data;
    }

    /**
     * @brief Applies baseline restoration to a signal using a rolling window minimum.
     * For each index \( i \) (with \( i \ge 1 \)) in the input signal, this function computes
     * the minimum value among the previous `window_size` samples (i.e. indices from
     * \(\max(0, i - \text{window_size})\) to \( i-1 \)) based on the original unmodified signal.
     * It then subtracts that minimum value from the current sample.
     * If `window_size == -1`, then for each \( i > 0 \) the function uses the minimum value
     * from indices \([0, i)\).
     * @param signal_name The name of the signal to apply baseline restoration to.
     * @param window_size The number of previous samples to consider for the minimum. If set to -1, the window is treated as infinite (using all samples from index 0 to \(i-1\)).
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @param window_size The number of previous samples to consider for the minimum. If set to -1, the window is treated as infinite (using all samples from index 0 to \(i-1\)).
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @param window_size The number of previous samples to consider for the minimum. If set to -1, the window is treated as infinite (using all samples from index 0 to \(i-1\)).
     */
    void apply_baseline_restoration_to_signal(const std::string &signal_name, const int window_size);
    void apply_baseline_restoration(const int window_size);

    /**
     * @brief Applies a Butterworth low-pass filter to a signal.
     * The filter transfer function is defined as:
     *     H(f) = (1 / sqrt(1 + (f/cutoff_frequency)^2))^order,
     * where @c cutoff_frequency sets the cutoff point and @c order controls the steepness
     * of the filter's roll-off. After filtering, the signal is scaled by the @c gain factor.
     * @param signal_name The name of the signal to apply the filter to.
     * @param sampling_rate The sampling rate of the signal.
     * @param cutoff_frequency The cutoff frequency for the low-pass filter.
     * @param order The order of the filter, determining the sharpness of the frequency cutoff.
     * @param gain A gain factor to scale the filtered signal.
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @throws std::runtime_error If the signal vector is empty.
     */
    void apply_butterworth_lowpass_filter_to_signal(const std::string &signal_name, const double sampling_rate, const double cutoff_frequency, const int order, const double gain);
    void apply_butterworth_lowpass_filter(const double sampling_rate, const double cutoff_frequency, const int order, const double gain);

    /**
     * @brief Generates a composite signal with Gaussian pulses on a constant background.
     * This function computes a composite signal by adding one or more Gaussian pulses to a
     * constant background power level. Each pulse is defined by its width, center, and coupling power.
     * The resulting signal is stored in an internal buffer of the SignalGenerator object.
     * The process is as follows:
     * - The output signal is first initialized with the background_power at every time point.
     * - For each pulse, a Gaussian function is evaluated at each time value. The Gaussian is given by:
     *   \f[
     *       \text{gauss\_val} = \text{coupling\_power}[i] \times \exp\left(-\frac{(t - \text{centers}[i])^2}{2 \times \text{widths}[i]^2}\right)
     *   \f]
     * - The computed Gaussian value is added to the output signal at each time point.
     * @param signal_name The name of the signal to generate pulses for.
     * @param widths A vector of pulse widths.
     * @param centers A vector of pulse centers.
     * @param coupling_power A vector of coupling powers for each pulse.
     * @param background_power The constant background power level to initialize the signal.
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @throws std::runtime_error If the sizes of widths, centers, and coupling_power vectors do not match.
     */
    void generate_pulses_signal(const std::string &signal_name, const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, const double background_power);
    void generate_pulses(const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, const double background_power);

    /**
     *  @brief Adds Gaussian noise to a signal.
     *  This function adds Gaussian noise to a specified signal in the data dictionary.
     *  The noise is generated using a normal distribution with the specified mean and standard deviation.
     *  @param signal_name The name of the signal to which noise will be added.
     *  @param mean The mean of the Gaussian noise.
     *  @param standard_deviation The standard deviation of the Gaussian noise.
     *  @throws std::runtime_error If the signal with the specified name does not exist.
     *  @throws std::runtime_error If the signal vector is empty.
     *  @note If the signal does not exist, it will throw an error.
     *  @note If the signal vector is empty, it will throw an error.
     *  @note This function modifies the signal in place.
    */
    void add_gaussian_noise_to_signal(const std::string &signal_name, const double mean, const double standard_deviation);
    void add_gaussian_noise(const double mean, const double standard_deviation);

    /**
     * @brief Applies a Bessel low-pass filter to a signal.
     * The filter is implemented using a frequency-domain approach where the transfer
     * function \(H(f)\) is computed for a Bessel filter of a specified order.
     * The following orders are supported:
     * - Order 1: \( H(s) = \frac{1}{s+1} \)
     * - Order 2: \( H(s) = \frac{3}{s^2+3s+3} \)
     * - Order 3: \( H(s) = \frac{15}{s^3+6s^2+15s+15} \)
     * - Order 4: \( H(s) = \frac{105}{s^4+10s^3+45s^2+105s+105} \)
     * In each case, \( s \) is defined as \( s = j \,(f/\text{cutoff_frequency}) \),
     * where \( f \) is the frequency, and the constants (1, 3, 15, 105) normalize the
     * filter so that \( H(0) = 1 \).
     * After filtering, the output signal is scaled by the provided gain factor.
     * @param signal_name The name of the signal to apply the filter to.
     * @param sampling_rate The sampling rate of the signal.
     * @param cutoff_frequency The cutoff frequency of the Bessel low-pass filter.
     * @param order The order of the Bessel filter (supported orders: 1, 2, 3, or 4).
     * @param gain A gain factor to scale the filtered signal.
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @throws std::runtime_error If the signal vector is empty.
     */
    void apply_bessel_lowpass_filter_to_signal(const std::string &signal_name, const double sampling_rate, const double cutoff_frequency, const int order, const double gain);
    void apply_bessel_lowpass_filter(const double sampling_rate, const double cutoff_frequency, const int order, const double gain);


    /**
     * @brief Adds Poisson noise to a signal.
     * This function adds Poisson-distributed noise to a specified signal in the data dictionary.
     * The noise is generated based on the signal values, ensuring that the noise is non-negative.
     * @param signal_name The name of the signal to which Poisson noise will be added.
     * @throws std::runtime_error If the signal with the specified name does not exist.
     * @throws std::runtime_error If the signal vector is empty.
     * @note If the signal does not exist, it will throw an error.
     * @note If the signal vector is empty, it will throw an error.
     * @note This function modifies the signal in place.
     * @note The signal must contain non-negative values, as Poisson noise is defined for non-negative integers.
     */
    void add_poisson_noise_to_signal(const std::string &signal_name);
    void add_poisson_noise();

    std::vector<double> &get_signal(const std::string &signal_name) {
        if (data_dict.find(signal_name) == data_dict.end())
            throw std::runtime_error("Signal with this name does not exist.");

        return data_dict[signal_name];
    }

    void add_constant_to_signal(const std::string &signal_name, const double constant) {
        if (data_dict.find(signal_name) == data_dict.end())
            throw std::runtime_error("Signal with this name does not exist.");

        for (auto &value : data_dict[signal_name])
            value += constant;

    }

    void add_constant(const double constant) {
        for (auto &entry : data_dict) {
            if (entry.first == "Time")  // Skip the time signal
                continue;
            this->add_constant_to_signal(entry.first, constant);
        }
    }
};
