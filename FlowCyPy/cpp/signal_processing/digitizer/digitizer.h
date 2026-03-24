#pragma once

#include <vector>
#include <string>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <map>


class Digitizer {
public:
    double bandwidth;
    double sampling_rate;
    size_t bit_depth;
    double min_voltage;
    double max_voltage;
    bool use_auto_range;
    bool output_signed_codes;
    bool debug_mode;

    /**
     * @brief Construct a new Digitizer object.
     *
     * The digitizer can optionally clip a signal to a voltage range and quantize it
     * into integer ADC codes according to a specified bit depth.
     *
     * Input voltages may be negative, positive, or bipolar. The voltage range is
     * defined by `min_voltage` and `max_voltage`, and the signal is mapped onto a
     * code range determined by `bit_depth` and `output_signed_codes`.
     *
     * If `output_signed_codes` is false, the output code range is:
     *
     *     [0, 2^bit_depth - 1]
     *
     * If `output_signed_codes` is true, the output code range is:
     *
     *     [-2^(bit_depth-1), 2^(bit_depth-1) - 1]
     *
     * A bit depth of 0 disables quantization.
     *
     * The bandwidth is optional. When it is unset, it is not considered in any
     * computation and simply remains undefined.
     *
     * @param bandwidth Digitizer bandwidth in hertz, or NaN if unset.
     * @param sampling_rate Sampling rate in hertz. Must be strictly positive.
     * @param bit_depth Number of quantization bits. A value of 0 disables digitization.
     * @param min_voltage Minimum clipping voltage in volts, or NaN if unset.
     * @param max_voltage Maximum clipping voltage in volts, or NaN if unset.
     * @param use_auto_range Persistent automatic voltage range inference flag.
     * @param output_signed_codes If true, generate signed ADC codes.
     */
    Digitizer(
        const double bandwidth,
        const double sampling_rate,
        const size_t bit_depth = 0,
        const double min_voltage = std::numeric_limits<double>::quiet_NaN(),
        const double max_voltage = std::numeric_limits<double>::quiet_NaN(),
        const bool use_auto_range = false,
        const bool output_signed_codes = false,
        const bool debug_mode = false
    );

    /**
     * @brief Return whether a bandwidth has been defined.
     *
     * @return True if the bandwidth is defined, false otherwise.
     */
    bool has_bandwidth() const;

    /**
     * @brief Return whether both clipping bounds are defined.
     *
     * @return True if both min_voltage and max_voltage are defined.
     */
    bool has_voltage_range() const;

    /**
     * @brief Return whether digitization is enabled.
     *
     * @return True if bit_depth is greater than 0.
     */
    bool should_digitize() const;

    /**
     * @brief Return whether the digitizer outputs signed codes.
     *
     * @return True if signed output codes are enabled.
     */
    bool has_signed_output_codes() const;

    /**
     * @brief Clear the configured bandwidth.
     *
     * After this call, the bandwidth is considered unset and should not be used
     * in downstream computations.
     */
    void clear_bandwidth();

    /**
     * @brief Clear the configured voltage range.
     *
     * After this call, both clipping bounds become undefined.
     */
    void clear_voltage_range();

    /**
     * @brief Clip a signal to the configured voltage range.
     *
     * If the voltage range is not fully defined, this method leaves the signal unchanged.
     *
     * NaN values are preserved.
     *
     * @param signal Signal values in volts.
     */
    void clip_signal(std::vector<double>& signal) const;

    /**
     * @brief Compute the minimum and maximum finite values of a signal.
     *
     * NaN values are ignored.
     *
     * @param signal Signal values in volts.
     * @return Pair containing minimum and maximum finite values.
     * @throws std::runtime_error If the signal contains only NaN values.
     */
    std::pair<double, double> get_min_max(const std::vector<double>& signal) const;

    /**
     * @brief Infer the clipping range from a signal.
     *
     * The minimum and maximum finite values of the input signal are used to update
     * min_voltage and max_voltage.
     *
     * @param signal Signal values in volts.
     */
    void set_auto_range(const std::vector<double>& signal);

    /**
     * @brief Return the minimum output code produced by the current digitizer settings.
     *
     * For unsigned output this is 0.
     *
     * For signed output this is -2^(bit_depth - 1).
     *
     * @return Minimum code value.
     * @throws std::runtime_error If digitization is disabled.
     */
    int64_t get_minimum_code() const;

    /**
     * @brief Return the maximum output code produced by the current digitizer settings.
     *
     * For unsigned output this is 2^bit_depth - 1.
     *
     * For signed output this is 2^(bit_depth - 1) - 1.
     *
     * @return Maximum code value.
     * @throws std::runtime_error If digitization is disabled.
     */
    int64_t get_maximum_code() const;

    /**
     * @brief Digitize a signal according to the configured bit depth and voltage range.
     *
     * If bit_depth is 0, the signal is left unchanged.
     *
     * Digitization requires a defined voltage range.
     *
     * NaN values are preserved.
     *
     * The signal is first clipped to the configured voltage range, then mapped to
     * either an unsigned or signed integer code range depending on
     * `output_signed_codes`.
     *
     * The resulting integer codes are stored back into the input vector as double
     * values for storage convenience.
     *
     * @param signal Signal values in volts.
     * @throws std::runtime_error If digitization is enabled but the voltage range is undefined.
     * @throws std::runtime_error If the voltage range is invalid.
     */
    void digitize_signal(std::vector<double>& signal) const;

    /**
     * @brief Process a signal using the instance automatic range setting.
     *
     * Processing order:
     *
     * 1. optional automatic range inference
     * 2. clipping
     * 3. digitization
     *
     * If digitization is enabled, the final signal contains integer code values
     * stored in a double vector.
     *
     * @param signal Signal values in volts.
     */
    void process_signal(std::vector<double>& signal);


    /**
     * @brief Update internal voltage range information without modifying the signal.
     *
     * @param signal Signal values in volts.
     */
    void capture_signal(const std::vector<double>& signal);

    /**
     * @brief Update internal voltage range information using an explicit override.
     *
     * @param signal Signal values in volts.
     * @param use_auto_range_override If true, infer the voltage range from the signal.
     */
    void capture_signal(const std::vector<double>& signal, const bool use_auto_range_override);

    /**
     * @brief Process a dictionary of channels in place.
     *
     * Every entry is processed except the channel named `Time`, which is left unchanged.
     *
     * This method is the pure C++ backend for Python dictionary level digitization.
     * Channel processing is parallelized across channels when OpenMP is available.
     *
     * @param data_map Map from channel name to signal samples.
     */
    void process_data_map(std::map<std::string, std::vector<double>>& data_map) const;

    /**
     * @brief Process a dictionary of channels and return the processed copy.
     *
     * Every entry is processed except the channel named `Time`, which is copied unchanged.
     *
     * Channel processing is parallelized across channels when OpenMP is available.
     *
     * @param data_map Map from channel name to signal samples.
     * @return Processed map.
     */
    std::map<std::string, std::vector<double>> get_processed_data_map(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    /**
     * @brief Return whether any signal in a map contains NaN values.
     *
     * The `Time` channel is ignored.
     *
     * @param data_map Map from channel name to signal samples.
     * @return True if at least one processed channel contains NaN.
     */
    bool processed_data_map_contains_nan(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    /**
     * @brief Generate the digitizer sampling time axis for a given acquisition duration.
     *
     * The returned sequence is:
     *
     *     time[index] = index / sampling_rate
     *
     * for index in [0, sample_count), where
     *
     *     sample_count = floor(sampling_rate * run_time)
     *
     * @param run_time Acquisition duration in seconds.
     * @return Time axis in seconds.
     * @throws std::invalid_argument If run_time is negative.
     */
    std::vector<double> get_time_series(const double run_time) const;
};
