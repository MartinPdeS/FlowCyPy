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


class Digitizer {
public:
    double bandwidth;
    double sampling_rate;
    size_t bit_depth;
    double min_voltage;
    double max_voltage;
    bool use_auto_range;

    /**
     * @brief Construct a new Digitizer object.
     *
     * The digitizer can optionally clip a signal to a voltage range and quantize it
     * according to a specified bit depth.
     *
     * The bandwidth is optional. When it is unset, it is not considered in any
     * computation and simply remains undefined.
     *
     * A bit depth of 0 disables quantization.
     *
     * @param bandwidth Digitizer bandwidth in hertz, or NaN if unset.
     * @param sampling_rate Sampling rate in hertz. Must be strictly positive.
     * @param bit_depth Number of quantization bits. A value of 0 disables digitization.
     * @param min_voltage Minimum clipping voltage in volts, or NaN if unset.
     * @param max_voltage Maximum clipping voltage in volts, or NaN if unset.
     * @param use_auto_range Persistent automatic voltage range inference flag.
     */
    Digitizer(
        const double bandwidth,
        const double sampling_rate,
        const size_t bit_depth = 0,
        const double min_voltage = std::numeric_limits<double>::quiet_NaN(),
        const double max_voltage = std::numeric_limits<double>::quiet_NaN(),
        const bool use_auto_range = false
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
     * @brief Digitize a signal according to the configured bit depth and voltage range.
     *
     * If bit_depth is 0, the signal is left unchanged.
     *
     * Digitization requires a defined voltage range.
     *
     * NaN values are preserved.
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
     * @param signal Signal values in volts.
     */
    void process_signal(std::vector<double>& signal);

    /**
     * @brief Process a signal using an explicit automatic range override.
     *
     * Processing order:
     *
     * 1. optional automatic range inference
     * 2. clipping
     * 3. digitization
     *
     * @param signal Signal values in volts.
     * @param use_auto_range_override If true, infer the voltage range from the signal before processing.
     */
    void process_signal(std::vector<double>& signal, const bool use_auto_range_override);

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
     * @brief Generate the digitizer sampling time axis for a given acquisition duration.
     *
     * The returned sequence is:
     *
     * time[index] = index / sampling_rate
     *
     * for index in [0, sample_count), where
     *
     * sample_count = floor(sampling_rate * run_time)
     *
     * @param run_time Acquisition duration in seconds.
     * @return Time axis in seconds.
     * @throws std::invalid_argument If run_time is negative.
     */
    std::vector<double> get_time_series(const double run_time) const;
};
