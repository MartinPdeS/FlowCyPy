#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>


/**
 * @class SignalGenerator
 * @brief Container and operations for synthetic signals defined on a shared time axis.
 *
 * This class stores multiple named channels, each represented as a vector of double
 * with a common length fixed at construction. A reserved channel named "Time"
 * stores the shared time axis.
 *
 * The class provides:
 *
 * - channel creation and retrieval
 * - scalar and vector arithmetic
 * - pulse synthesis on the shared time axis
 * - baseline restoration
 * - Butterworth and Bessel low pass filtering
 * - Gaussian and Poisson noise models
 * - FFT based Gaussian convolution
 * - gamma trace generation
 *
 * Design rules:
 *
 * - every stored channel must have exactly `n_elements` samples
 * - the time channel is optional, but required by methods that depend on time
 * - time dependent methods assume a strictly increasing time axis
 * - random noise uses the internal random generator for reproducibility
 */
class SignalGenerator {
public:
    /// Reserved key used for the time axis.
    static constexpr const char* TIME_KEY = "Time";
    std::map<std::string, std::vector<double>> data_dict;

public:
    /**
     * @brief Construct a signal generator with a fixed number of samples.
     * @param n_elements Number of samples for every stored channel.
     * @throws std::runtime_error If `n_elements` is zero.
     */
    explicit SignalGenerator(size_t n_elements);

    /**
     * @brief Seed the internal random generator.
     * @param seed Deterministic seed value.
     */
    void set_seed(uint64_t seed);

    /**
     * @brief Return the common number of samples for each channel.
     * @return Number of samples.
     */
    size_t get_number_of_elements() const;

    /**
     * @brief Check whether a channel exists.
     * @param channel Channel name.
     * @return True if the channel exists, false otherwise.
     */
    bool has_channel(const std::string& channel) const;

    /**
     * @brief Check whether the time channel exists.
     * @return True if the time channel exists, false otherwise.
     */
    bool has_time_channel() const;

    /**
     * @brief Return the names of all stored channels except the time channel.
     * @return Vector of channel names.
     */
    std::vector<std::string> get_channel_names() const;

    // -------------------------------------------------------------------------
    // Time channel
    // -------------------------------------------------------------------------

    /**
     * @brief Set the shared time channel.
     *
     * The provided vector must have length `n_elements`.
     *
     * @param time_values Time samples.
     * @throws std::runtime_error If the size does not match `n_elements`.
     */
    void set_time_channel(const std::vector<double>& time_values);

    /**
     * @brief Return mutable access to the time channel.
     * @return Mutable reference to the time channel.
     * @throws std::runtime_error If the time channel does not exist.
     */
    std::vector<double>& get_time_channel();

    /**
     * @brief Return const access to the time channel.
     * @return Const reference to the time channel.
     * @throws std::runtime_error If the time channel does not exist.
     */
    const std::vector<double>& get_time_channel_const() const;

    /**
     * @brief Return the sampling period from the first two time samples.
     * @return Sampling period `dt`.
     * @throws std::runtime_error If the time channel is missing, too short, or non increasing.
     */
    double get_time_step() const;

    /**
     * @brief Return the sampling rate computed as `1 / dt`.
     * @return Sampling rate.
     * @throws std::runtime_error If the time channel is missing, too short, or non increasing.
     */
    double get_sampling_rate() const;

    // -------------------------------------------------------------------------
    // Channel creation and retrieval
    // -------------------------------------------------------------------------

    /**
     * @brief Add a new channel with explicit values.
     * @param channel Channel name.
     * @param channel_data Channel values.
     * @throws std::runtime_error If the channel already exists or the size is invalid.
     */
    void add_channel(const std::string& channel, const std::vector<double>& channel_data);

    /**
     * @brief Create a new channel initialized with a constant value.
     * @param channel Channel name.
     * @param constant_value Constant fill value.
     * @throws std::runtime_error If the channel already exists.
     */
    void create_channel(const std::string& channel, double constant_value = 0.0);

    /**
     * @brief Create a new channel initialized with zeros.
     * @param channel Channel name.
     * @throws std::runtime_error If the channel already exists.
     */
    void create_zero_channel(const std::string& channel);

    /**
     * @brief Return mutable access to a stored channel.
     * @param channel Channel name.
     * @return Mutable reference to the channel values.
     * @throws std::runtime_error If the channel does not exist.
     */
    std::vector<double>& get_channel(const std::string& channel);

    /**
     * @brief Return const access to a stored channel.
     * @param channel Channel name.
     * @return Const reference to the channel values.
     * @throws std::runtime_error If the channel does not exist.
     */
    const std::vector<double>& get_channel_const(const std::string& channel) const;

    // -------------------------------------------------------------------------
    // Basic arithmetic
    // -------------------------------------------------------------------------

    /**
     * @brief Add a constant to all non time channels.
     * @param constant_value Value added to each sample.
     */
    void add_constant(double constant_value);

    /**
     * @brief Add a constant to one channel.
     * @param channel Channel name.
     * @param constant_value Value added to each sample.
     * @throws std::runtime_error If the channel does not exist.
     */
    void add_constant_to_channel(const std::string& channel, double constant_value);

    /**
     * @brief Multiply all non time channels by a scalar factor.
     * @param factor Multiplicative factor.
     */
    void multiply(double factor);

    /**
     * @brief Multiply one channel by a scalar factor.
     * @param channel Channel name.
     * @param factor Multiplicative factor.
     * @throws std::runtime_error If the channel does not exist.
     */
    void multiply_channel(const std::string& channel, double factor);

    /**
     * @brief Round all non time channels to the nearest integer.
     */
    void round();

    /**
     * @brief Round one channel to the nearest integer.
     * @param channel Channel name.
     * @throws std::runtime_error If the channel does not exist.
     */
    void round_channel(const std::string& channel);

    /**
     * @brief Add an array element wise to one channel.
     * @param channel Channel name.
     * @param added_array Values added element wise.
     * @throws std::runtime_error If the channel does not exist or sizes do not match.
     */
    void add_array_to_channel(const std::string& channel, const std::vector<double>& added_array);

    // -------------------------------------------------------------------------
    // Signal processing
    // -------------------------------------------------------------------------

    /**
     * @brief Apply baseline restoration to all non time channels.
     *
     * For sample `i`, the baseline is computed as the minimum over a backward window
     * on the original signal and is subtracted from the current sample.
     *
     * @param window_size Window length in samples. Use `-1` for an expanding window.
     */
    void apply_baseline_restoration(int window_size);

    /**
     * @brief Apply a Butterworth low pass filter to all non time channels.
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Filter order.
     * @param gain Gain applied after filtering.
     */
    void apply_butterworth_lowpass_filter(
        double sampling_rate,
        double cutoff_frequency,
        int order,
        double gain
    );

    /**
     * @brief Apply a Butterworth low pass filter to one channel.
     * @param channel Channel name.
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Filter order.
     * @param gain Gain applied after filtering.
     * @throws std::runtime_error If the channel does not exist.
     */
    void apply_butterworth_lowpass_filter_to_channel(
        const std::string& channel,
        double sampling_rate,
        double cutoff_frequency,
        int order,
        double gain
    );

    /**
     * @brief Apply a Bessel low pass filter to all non time channels.
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Supported orders are 1 through 4.
     * @param gain Gain applied after filtering.
     */
    void apply_bessel_lowpass_filter(
        double sampling_rate,
        double cutoff_frequency,
        int order,
        double gain
    );

    /**
     * @brief Apply a Bessel low pass filter to one channel.
     * @param channel Channel name.
     * @param sampling_rate Sampling rate in samples per second.
     * @param cutoff_frequency Cutoff frequency in hertz.
     * @param order Supported orders are 1 through 4.
     * @param gain Gain applied after filtering.
     * @throws std::runtime_error If the channel does not exist.
     */
    void apply_bessel_lowpass_filter_to_channel(
        const std::string& channel,
        double sampling_rate,
        double cutoff_frequency,
        int order,
        double gain
    );

    // -------------------------------------------------------------------------
    // Pulse generation
    // -------------------------------------------------------------------------

    /**
     * @brief Generate Gaussian pulses in all non time channels.
     *
     * Every target channel is reset to `background_power`, then each Gaussian pulse
     * is added using the shared time channel.
     *
     * @param sigmas Standard deviations of the pulses.
     * @param centers Pulse centers in the same units as the time axis.
     * @param coupling_power Pulse amplitudes.
     * @param background_power Constant background added before the pulses.
     * @throws std::runtime_error If the time channel is missing or vector sizes mismatch.
     */
    void generate_pulses(
        const std::vector<double>& sigmas,
        const std::vector<double>& centers,
        const std::vector<double>& coupling_power,
        double background_power
    );

    /**
     * @brief Generate Gaussian pulses in one channel.
     * @param channel Channel name.
     * @param sigmas Standard deviations of the pulses.
     * @param centers Pulse centers in the same units as the time axis.
     * @param coupling_power Pulse amplitudes.
     * @param background_power Constant background added before the pulses.
     * @throws std::runtime_error If the channel or time channel is missing or vector sizes mismatch.
     */
    void generate_pulses_to_channel(
        const std::string& channel,
        const std::vector<double>& sigmas,
        const std::vector<double>& centers,
        const std::vector<double>& coupling_power,
        double background_power
    );

    // -------------------------------------------------------------------------
    // Noise
    // -------------------------------------------------------------------------

    /**
     * @brief Add Gaussian noise to all non time channels.
     * @param mean Mean of the Gaussian distribution.
     * @param standard_deviation Standard deviation of the Gaussian distribution.
     */
    void add_gaussian_noise(double mean, double standard_deviation);

    /**
     * @brief Add Gaussian noise to one channel.
     * @param channel Channel name.
     * @param mean Mean of the Gaussian distribution.
     * @param standard_deviation Standard deviation of the Gaussian distribution.
     * @throws std::runtime_error If the channel does not exist.
     */
    void add_gaussian_noise_to_channel(
        const std::string& channel,
        double mean,
        double standard_deviation
    );

    /**
     * @brief Apply Poisson noise to all non time channels.
     *
     * A mixed strategy is used internally:
     * Poisson sampling for moderate values and Gaussian approximation for very large values.
     *
     * @throws std::runtime_error If any target channel contains negative values.
     */
    void apply_poisson_noise();

    /**
     * @brief Apply Poisson noise to one channel.
     *
     * A mixed strategy is used internally:
     * Poisson sampling for moderate values and Gaussian approximation for very large values.
     *
     * @param channel Channel name.
     * @throws std::runtime_error If the channel does not exist or contains negative values.
     */
    void apply_poisson_noise_to_channel(const std::string& channel);

    /**
     * @brief Apply Poisson noise after converting a channel from watts to photon counts.
     *
     * The channel is scaled by `watt_to_photon`, Poisson noise is applied, then the
     * channel is scaled back by the inverse conversion factor.
     *
     * @param channel Channel name.
     * @param watt_to_photon Positive conversion factor.
     * @throws std::runtime_error If the factor is not positive or the channel is invalid.
     */
    void apply_poisson_noise_through_conversion(
        const std::string& channel,
        double watt_to_photon
    );

    // -------------------------------------------------------------------------
    // Convolution and trace generation
    // -------------------------------------------------------------------------

    /**
     * @brief Convolve a channel with a Gaussian kernel using FFTW.
     *
     * A Gaussian kernel is built on the shared time axis and normalized to unit sum.
     *
     * @param channel Channel name.
     * @param sigma Standard deviation of the Gaussian kernel in time axis units.
     * @throws std::runtime_error If the channel or time channel is missing, or the signal is too short.
     */
    void convolve_channel_with_gaussian(const std::string& channel, double sigma);

    /**
     * @brief Generate a gamma distributed trace and add it to a channel.
     *
     * The generated trace has length `n_elements`. If `gaussian_sigma > 0`,
     * the trace is convolved with a Gaussian kernel defined on the shared time axis
     * before being added to the target channel.
     *
     * @param channel Channel name.
     * @param shape Gamma shape parameter, must be positive.
     * @param scale Gamma scale parameter, must be positive.
     * @param gaussian_sigma Gaussian convolution sigma. No convolution is applied if non positive.
     * @return Generated trace after optional convolution.
     * @throws std::runtime_error If parameters are invalid or the channel or time channel is unavailable.
     */
    std::vector<double> add_gamma_trace_to_channel(
        const std::string& channel,
        double shape,
        double scale,
        double gaussian_sigma = 0.0
    );

    std::vector<double> get_gamma_trace(
        double shape,
        double scale,
        double gaussian_sigma = 0.0
    );

private:
    size_t n_elements;
    std::mt19937 random_generator;

private:
    /**
     * @brief Throw if a channel is missing.
     * @param channel Channel name.
     */
    void assert_channel_exists(const std::string& channel) const;

    /**
     * @brief Throw if the time channel is missing or has invalid size.
     */
    void assert_time_channel_ready() const;

    /**
     * @brief Validate that a vector has exactly `n_elements` samples.
     * @param vector_size Provided vector size.
     * @param object_name Name used in the exception message.
     * @throws std::runtime_error If the size is invalid.
     */
    void assert_valid_size(size_t vector_size, const std::string& object_name) const;

    /**
     * @brief Apply strict Poisson sampling to one channel.
     * @param channel Channel name.
     */
    void apply_strict_poisson_noise_to_channel(const std::string& channel);

    /**
     * @brief Apply Gaussian approximation of Poisson noise to one channel.
     * @param channel Channel name.
     */
    void apply_gaussian_approximated_poisson_noise_to_channel(const std::string& channel);

    /**
     * @brief Apply a mixed Poisson strategy to one channel.
     * @param channel Channel name.
     */
    void apply_mixed_poisson_noise_to_channel(const std::string& channel);
};
