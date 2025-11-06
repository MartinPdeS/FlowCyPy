#pragma once

#include <stdexcept>
#include <vector>
#include <random>
#include <cmath>
#include <algorithm>
#include <string>
#include <map>
#include "../utils/utils.h"

/**
 * @brief Container and operations for synthetic signals on a shared time base.
 *
 * SignalGenerator stores multiple named signals of equal length in a dictionary.
 * It provides common arithmetic transforms, baseline restoration, pulse synthesis,
 * frequency domain filters, and noise models. The special key "Time" can be used
 * to hold the time axis. Many operations skip the time axis by default.
 *
 * Design notes:
 *  - All signals must have length n_elements.
 *  - Accessors throw if a signal name is missing.
 *  - The random generator is owned by the instance for reproducible noise.
 */
class SignalGenerator {
public:
    /// Dictionary of signal_name -> vector values. The key "Time" is reserved for the time axis.
    std::map<std::string, std::vector<double>> data_dict;

    /// Common number of samples for every stored signal.
    size_t n_elements;

    /// Centralized key for the time axis.
    static constexpr const char* TIME_KEY = "Time";

    /// Random engine used by noise routines. Seed with set_seed for reproducibility.
    std::mt19937 random_generator;

    /**
     * @brief Construct a generator for signals of fixed length.
     * @param n_elements Number of samples per signal.
     */
    explicit SignalGenerator(const size_t n_elements)
        : n_elements(n_elements),
          random_generator(std::mt19937(std::random_device{}())) {}

    /**
     * @brief Seed the internal random generator.
     * @param seed Seed value for deterministic noise.
     */
    void set_seed(uint64_t seed) { random_generator.seed(seed); }

    /**
     * @brief Check if a signal exists in the dictionary.
     * @param signal_name Name to query.
     * @return True if present, false otherwise.
     */
    bool has_signal(const std::string& signal_name) const {
        return data_dict.find(signal_name) != data_dict.end();
    }

    // ----------------------------- Setters and Getters -----------------------------

    /**
     * @brief Create a new signal initialized with zeros.
     * @param signal_name Name of the signal to create.
     * @throws std::runtime_error If the name already exists.
     */
    void create_zero_signal(const std::string &signal_name);

    /**
     * @brief Insert a signal with explicit data.
     * @param signal_name Name of the signal to add.
     * @param signal_data Vector of values. Size must equal n_elements.
     * @throws std::runtime_error If the name exists or size mismatches n_elements.
     */
    void add_signal(const std::string &signal_name, const std::vector<double> &signal_data);

    /**
     * @brief Mutable access to a stored signal.
     * @param signal_name Name of the signal to retrieve.
     * @return Reference to the signal vector.
     * @throws std::runtime_error If the signal does not exist.
     */
    std::vector<double> &get_signal(const std::string &signal_name);

    /**
     * @brief Const access to a stored signal.
     * @param signal_name Name of the signal to retrieve.
     * @return Const reference to the signal vector.
     * @throws std::runtime_error If the signal does not exist.
     */
    const std::vector<double> &get_signal_const(const std::string &signal_name) const;

    // ----------------------------- Basics Operations ------------------------------

    /**
     * @brief Add a constant to every sample of a given signal.
     * @param signal_name Target signal name.
     * @param constant Value to add.
     * @throws std::runtime_error If the signal does not exist.
     */
    void add_constant_to_signal(const std::string &signal_name, double constant);

    /**
     * @brief Add a constant to every sample of all signals except the time axis.
     * @param constant Value to add.
     */
    void add_constant(double constant);

    /**
     * @brief Multiply a given signal by a constant factor.
     * @param signal_name Target signal name.
     * @param factor Multiplicative factor.
     * @throws std::runtime_error If the signal does not exist.
     */
    void multiply_signal(const std::string &signal_name, double factor);

    /**
     * @brief Multiply all signals by a constant factor, skipping the time axis.
     * @param factor Multiplicative factor.
     */
    void multiply(double factor);

    /**
     * @brief Round each sample of a given signal to the nearest integer.
     * @param signal_name Target signal name.
     * @throws std::runtime_error If the signal does not exist.
     */
    void round_signal(const std::string &signal_name);

    /**
     * @brief Round each sample of all signals to the nearest integer, skipping the time axis.
     */
    void round();

    /**
     * @brief List names of all stored signals except the time axis.
     * @return Vector of names.
     */
    std::vector<std::string> get_signal_names() const {
        std::vector<std::string> signal_names;
        signal_names.reserve(data_dict.size());
        for (const auto &pair : data_dict) {
            if (pair.first == TIME_KEY) continue;
            signal_names.push_back(pair.first);
        }
        return signal_names;
    }

    // ----------------------------- Complex Operations -----------------------------

    /**
     * @brief Baseline restoration by subtracting a rolling minimum of the past.
     *
     * For sample i, subtract the minimum over indices [max(0, i - window_size), i)
     * computed on the original unmodified reference. If window_size equals -1,
     * use the minimum over [0, i) for each i.
     *
     * @param window_size Window length in samples, or -1 for an expanding window.
     */
    void apply_baseline_restoration(int window_size);

    /**
     * @brief Apply a Butterworth low pass filter to all signals except the time axis.
     *
     * The magnitude response is (1 / sqrt(1 + (f / f_c)^2))^order.
     * After filtering, the result is scaled by gain.
     *
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency f_c in hertz.
     * @param order Integer order that controls transition steepness.
     * @param gain Output gain applied after filtering.
     */
    void apply_butterworth_lowpass_filter(double sampling_rate, double cutoff_frequency, int order, double gain);

    /**
     * @brief Apply a Butterworth low pass filter to one signal.
     * @see apply_butterworth_lowpass_filter for parameter meaning.
     * @throws std::runtime_error If the signal does not exist.
     */
    void apply_butterworth_lowpass_filter_to_signal(const std::string &signal_name, double sampling_rate, double cutoff_frequency, int order, double gain);

    /**
     * @brief Synthesize a composite signal as a sum of Gaussian pulses on a constant background for all signals.
     *
     * For each non time signal, initialize with background_power, then for each pulse k add
     * coupling_power[k] * exp( - (t - centers[k])^2 / (2 * widths[k]^2) ) evaluated at the stored time axis.
     * The vectors widths, centers, and coupling_power must have equal length.
     * The time axis must exist and have size n_elements.
     *
     * @param widths Gaussian standard deviations for each pulse.
     * @param centers Pulse centers in the same units as the time axis.
     * @param coupling_power Amplitudes for each pulse.
     * @param background_power Constant background added before pulses.
     * @throws std::runtime_error If the time axis is missing or sizes do not match.
     */
    void generate_pulses(const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, double background_power);

    /**
     * @brief Synthesize pulses into a single target signal using the stored time axis.
     * @see generate_pulses for the mathematical form and preconditions.
     * @throws std::runtime_error If the signal or time axis is missing or sizes do not match.
     */
    void generate_pulses_signal(const std::string &signal_name, const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, double background_power);

    /**
     * @brief Apply a Bessel low pass filter to all signals except the time axis.
     *
     * Implemented in the frequency domain with classic Bessel polynomials
     * of orders 1 through 4 and normalized so that H(0) equals 1. The output
     * is scaled by gain after filtering.
     *
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Supported orders are 1, 2, 3, and 4.
     * @param gain Output gain applied after filtering.
     */
    void apply_bessel_lowpass_filter(double sampling_rate, double cutoff_frequency, int order, double gain);

    /**
     * @brief Apply a Bessel low pass filter to one signal.
     * @see apply_bessel_lowpass_filter for parameter meaning.
     * @throws std::runtime_error If the signal does not exist.
     */
    void apply_bessel_lowpass_filter_to_signal(const std::string &signal_name, double sampling_rate, double cutoff_frequency, int order, double gain);

    // ----------------------------- Noise Operations ------------------------------

    /**
     * @brief Add independent Gaussian noise to every sample of all signals except the time axis.
     * @param mean Mean of the Gaussian distribution.
     * @param standard_deviation Standard deviation of the Gaussian distribution.
     * @note Uses the instance random generator for reproducibility.
     */
    void add_gaussian_noise(double mean, double standard_deviation);

    /**
     * @brief Add independent Gaussian noise to one signal.
     * @param signal_name Target signal name.
     * @param mean Mean of the Gaussian distribution.
     * @param standard_deviation Standard deviation of the Gaussian distribution.
     * @throws std::runtime_error If the signal does not exist.
     * @note Uses the instance random generator for reproducibility.
     */
    void add_gaussian_noise_to_signal(const std::string &signal_name, double mean, double standard_deviation);

    /**
     * @brief Apply Poisson noise to a single signal.
     *
     * Values must be non negative. For large means an internal Gaussian
     * approximation may be used. The operation is in place.
     *
     * @param signal_name Target signal name.
     * @throws std::runtime_error If the signal does not exist or contains negative values.
     */
    void apply_poisson_noise_to_signal(const std::string &signal_name);

    /**
     * @brief Apply Poisson noise to all signals except the time axis.
     * @throws std::runtime_error If any target signal contains negative values.
     */
    void apply_poisson_noise();

private:
    // ----------------------------- Internal helpers ------------------------------

    /**
     * @brief Strict Poisson sampling for each sample of a signal.
     * @param signal_name Target signal name.
     * @throws std::runtime_error If the signal is missing, empty, or contains negative values.
     */
    void _apply_poisson_noise_to_signal(const std::string &signal_name);

    /**
     * @brief Gaussian approximation to Poisson noise for each sample of a signal.
     * @param signal_name Target signal name.
     * @throws std::runtime_error If the signal is missing, empty, or contains negative values.
     */
    void _apply_poisson_noise_as_gaussian_to_signal(const std::string &signal_name);

    /**
     * @brief Mixed strategy for Poisson noise, using Poisson for small means and Gaussian for large means.
     * @param signal_name Target signal name.
     * @throws std::runtime_error If the signal is missing, empty, or contains negative values.
     */
    void _apply_mixed_poisson_noise_to_signal(const std::string &signal_name);

    /**
     * @brief Throw if a signal is not present.
     * @param signal_name Name to check.
     */
    void assert_signal_exists(const std::string& signal_name) const;

    /**
     * @brief Throw if the time axis is missing or has an unexpected size.
     */
    void assert_time_signal_ready() const;
};
