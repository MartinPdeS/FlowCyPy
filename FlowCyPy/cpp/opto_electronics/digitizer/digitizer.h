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


enum class ChannelRangeMode {
    shared,
    per_channel
};


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
    ChannelRangeMode channel_range_mode;
    std::map<std::string, std::pair<double, double>> channel_voltage_ranges;

    Digitizer(
        const double bandwidth,
        const double sampling_rate,
        const size_t bit_depth = 0,
        const double min_voltage = std::numeric_limits<double>::quiet_NaN(),
        const double max_voltage = std::numeric_limits<double>::quiet_NaN(),
        const bool use_auto_range = false,
        const bool output_signed_codes = false,
        const bool debug_mode = false,
        const ChannelRangeMode channel_range_mode = ChannelRangeMode::shared
    );

    bool has_bandwidth() const;
    bool has_voltage_range() const;
    bool should_digitize() const;
    bool has_signed_output_codes() const;

    void clear_bandwidth();
    void clear_voltage_range();

    void clip_signal(std::vector<double>& signal) const;
    std::pair<double, double> get_min_max(const std::vector<double>& signal) const;
    void set_auto_range(const std::vector<double>& signal);

    int64_t get_minimum_code() const;
    int64_t get_maximum_code() const;

    void digitize_signal(std::vector<double>& signal) const;
    void process_signal(std::vector<double>& signal);

    void capture_signal(const std::vector<double>& signal);
    void capture_signal(const std::vector<double>& signal, const bool use_auto_range_override);

    void process_data_map(std::map<std::string, std::vector<double>>& data_map) const;

    std::map<std::string, std::vector<double>> get_processed_data_map(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    bool processed_data_map_contains_nan(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    std::vector<double> get_time_series(const double run_time) const;

    std::vector<int64_t> convert_signal_to_signed_codes(
        const std::vector<double>& signal
    ) const;

    std::vector<uint64_t> convert_signal_to_unsigned_codes(
        const std::vector<double>& signal
    ) const;

    std::map<std::string, std::vector<int64_t>> get_processed_signed_data_map(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    std::map<std::string, std::vector<uint64_t>> get_processed_unsigned_data_map(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    std::map<std::string, std::vector<double>> process_flat_acquisition_data(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    std::map<std::string, std::map<std::string, std::vector<double>>> process_nested_acquisition_data(
        const std::map<std::string, std::map<std::string, std::vector<double>>>& data_map
    ) const;

    void set_channel_voltage_range(
        const std::string& channel_name,
        const double minimum_voltage,
        const double maximum_voltage
    );

    void clear_channel_voltage_range(const std::string& channel_name);
    void clear_all_channel_voltage_ranges();

    bool has_channel_voltage_range(const std::string& channel_name) const;

    std::pair<double, double> get_channel_voltage_range(
        const std::string& channel_name
    ) const;

    std::string repr() const;

private:
    void validate_voltage_range_for_digitization(
        const double local_min_voltage,
        const double local_max_voltage
    ) const;

    void validate_voltage_range_pair(
        const double local_min_voltage,
        const double local_max_voltage,
        const std::string& range_name
    ) const;

    void clip_signal_with_range(
        std::vector<double>& signal,
        const double local_min_voltage,
        const double local_max_voltage
    ) const;

    void digitize_signal_with_range(
        std::vector<double>& signal,
        const double local_min_voltage,
        const double local_max_voltage
    ) const;

    void process_signal_with_range(
        std::vector<double>& signal,
        const double local_min_voltage,
        const double local_max_voltage
    ) const;

    std::pair<double, double> get_shared_min_max_from_data_map(
        const std::map<std::string, std::vector<double>>& data_map
    ) const;

    std::pair<double, double> resolve_fixed_or_auto_range_for_signal(
        const std::vector<double>& signal
    ) const;

    std::pair<double, double> resolve_channel_voltage_range(
        const std::string& channel_name,
        const std::vector<double>& channel_signal,
        const std::pair<double, double>& shared_auto_range
    ) const;
};
