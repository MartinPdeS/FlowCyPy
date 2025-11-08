#include "signal_generator.h"

// Keep heavy headers out of the .h
#include <fftw3.h>
#include <complex>
#include <iostream>

// ----------------------------- Internal checks -----------------------------

void SignalGenerator::assert_signal_exists(const std::string& signal_name) const {
    if (!has_signal(signal_name))
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");
}

void SignalGenerator::assert_time_signal_ready() const {
    auto it = data_dict.find(TIME_KEY);
    if (it == data_dict.end())
        throw std::runtime_error("Time signal is missing. Add '" + std::string(TIME_KEY) + "' before calling this method.");
    if (it->second.size() != n_elements)
        throw std::runtime_error("Time signal size does not match n_elements.");
}

// ----------------------------- Setters and Getters -----------------------------

void SignalGenerator::add_signal(const std::string &signal_name, const std::vector<double> &signal_data) {
    if (has_signal(signal_name))
        throw std::runtime_error("Signal '" + signal_name + "' already exists.");
    if (signal_data.size() != n_elements)
        throw std::runtime_error("Signal '" + signal_name + "' size does not match n_elements.");
    data_dict.emplace(signal_name, signal_data);
}

void SignalGenerator::create_zero_signal(const std::string &signal_name) {
    if (has_signal(signal_name))
        throw std::runtime_error("Signal '" + signal_name + "' already exists.");
    data_dict.emplace(signal_name, std::vector<double>(n_elements, 0.0));
}

std::vector<double> &SignalGenerator::get_signal(const std::string &signal_name) {
    auto it = data_dict.find(signal_name);
    if (it == data_dict.end())
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");
    return it->second;
}

const std::vector<double> &SignalGenerator::get_signal_const(const std::string &signal_name) const {
    auto it = data_dict.find(signal_name);
    if (it == data_dict.end())
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");
    return it->second;
}

// ----------------------------- Basics Operations -----------------------------

void SignalGenerator::add_constant(double constant) {
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        this->add_constant_to_signal(entry.first, constant);
    }
}

void SignalGenerator::add_constant_to_signal(const std::string &signal_name, double constant) {
    auto it = data_dict.find(signal_name);
    if (it == data_dict.end())
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

    auto& vec = it->second;
    const size_t n = vec.size();

    // #pragma omp parallel for
    for (size_t i = 0; i < n; ++i)
        vec[i] += constant;
}



void SignalGenerator::multiply(double factor) {
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        this->multiply_signal(entry.first, factor);
    }
}

// void SignalGenerator::multiply_signal(const std::string &signal_name, double factor) {
//     auto it = data_dict.find(signal_name);
//     if (it == data_dict.end())
//         throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

//     auto& vec = it->second;
//     const size_t n = vec.size();

//     #pragma omp parallel for
//     for (size_t i = 0; i < n; ++i)
//         vec[i] *= factor;
// }

// void SignalGenerator::multiply_signal(const std::string& signal_name, double factor) {
//     auto it = data_dict.find(signal_name);
//     if (it == data_dict.end())
//         throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

//     auto& vec = it->second;
//     const size_t n = vec.size();
//     double* __restrict data = vec.data();

//     #pragma omp parallel for schedule(static)
//     for (long long i = 0; i < static_cast<long long>(n); ++i) {
//         data[i] *= factor;
//     }
// }








void SignalGenerator::multiply_signal(const std::string& signal_name, double factor) {
    // auto it = data_dict.find(signal_name);
    // if (it == data_dict.end())
    //     throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

    // auto& vec = it->second;
    // const size_t n = vec.size();
    // double* __restrict data = vec.data();

    double a;

    #pragma omp parallel for
    for (size_t i = 0; i < 1000; ++i)
        a += 3;

    std::cout<<a<<std::endl;
}



// void SignalGenerator::multiply_signal(const std::string& signal_name, double factor) {
//     auto it = data_dict.find(signal_name);
//     if (it == data_dict.end())
//         throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

//     auto& vec = it->second;
//     const size_t n = vec.size();

//     #pragma omp parallel for
//     for (size_t i = 0; i < n; ++i)
//         double a = factor;

// }


void SignalGenerator::round_signal(const std::string &signal_name) {
    auto it = data_dict.find(signal_name);
    if (it == data_dict.end())
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

    auto& vec = it->second;
    const size_t n = vec.size();

    #pragma omp parallel for
    for (size_t i = 0; i < n; ++i)
        vec[i] = std::round(vec[i]);
}

void SignalGenerator::round() {
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        round_signal(entry.first);
    }
}

// ----------------------------- Complex Operations -----------------------------

void SignalGenerator::apply_baseline_restoration(int window_size) {
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::apply_baseline_restoration_to_signal(entry.second, window_size);
    }
}

void SignalGenerator::apply_butterworth_lowpass_filter(
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain)
{
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::apply_butterworth_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
    }
}

void SignalGenerator::apply_butterworth_lowpass_filter_to_signal(
    const std::string &signal_name,
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain)
{
    assert_signal_exists(signal_name);
    utils::apply_butterworth_lowpass_filter_to_signal(data_dict[signal_name], sampling_rate, cutoff_frequency, order, gain);
}

void SignalGenerator::generate_pulses(
    const std::vector<double> &widths,
    const std::vector<double> &centers,
    const std::vector<double> &coupling_power,
    double background_power)
{
    assert_time_signal_ready();
    const auto& time = data_dict.at(TIME_KEY);

    if (!(widths.size() == centers.size() && centers.size() == coupling_power.size()))
        throw std::runtime_error("widths, centers, and coupling_power must have the same size.");

    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::generate_pulses_signal(entry.second, widths, centers, coupling_power, time, background_power);
    }
}

void SignalGenerator::generate_pulses_signal(
    const std::string& signal_name,
    const std::vector<double> &widths,
    const std::vector<double> &centers,
    const std::vector<double> &coupling_power,
    double background_power)
{
    assert_signal_exists(signal_name);
    assert_time_signal_ready();
    const auto& time = data_dict.at(TIME_KEY);

    if (!(widths.size() == centers.size() && centers.size() == coupling_power.size()))
        throw std::runtime_error("widths, centers, and coupling_power must have the same size.");

    utils::generate_pulses_signal(data_dict[signal_name], widths, centers, coupling_power, time, background_power);
}

void SignalGenerator::apply_bessel_lowpass_filter(
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain)
{
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::apply_bessel_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
    }
}

void SignalGenerator::apply_bessel_lowpass_filter_to_signal(
    const std::string &signal_name,
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain)
{
    assert_signal_exists(signal_name);
    utils::apply_bessel_lowpass_filter_to_signal(data_dict[signal_name], sampling_rate, cutoff_frequency, order, gain);
}

// ----------------------------- Noise Operations ------------------------------

void SignalGenerator::add_gaussian_noise(double mean, double standard_deviation) {
    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::add_gaussian_noise_to_signal(entry.second, mean, standard_deviation, random_generator);
    }
}

void SignalGenerator::add_gaussian_noise_to_signal(
    const std::string &signal_name,
    double mean,
    double standard_deviation)
{
    assert_signal_exists(signal_name);
    utils::add_gaussian_noise_to_signal(data_dict[signal_name], mean, standard_deviation, random_generator);
}

void SignalGenerator::apply_poisson_noise_to_signal(const std::string &signal_name) {
    assert_signal_exists(signal_name);
    _apply_mixed_poisson_noise_to_signal(signal_name);
}

void SignalGenerator::_apply_mixed_poisson_noise_to_signal(const std::string &signal_name) {
    auto& signal = data_dict[signal_name];
    if (signal.empty())
        throw std::runtime_error("Signal '" + signal_name + "' is empty.");

    constexpr double threshold = 1e6;

    for (size_t i = 0; i < signal.size(); ++i) {
        double value = signal[i];
        if (value < 0.0)
            throw std::runtime_error("Poisson noise requires non-negative values.");

        if (value < threshold) {
            std::poisson_distribution<int> dist(value);
            signal[i] = static_cast<double>(dist(random_generator));
        } else {
            std::normal_distribution<double> dist(value, std::sqrt(value));
            signal[i] = std::round(dist(random_generator));
        }
    }
}

void SignalGenerator::_apply_poisson_noise_to_signal(const std::string &signal_name) {
    auto& signal = data_dict[signal_name];
    if (signal.empty())
        throw std::runtime_error("Signal '" + signal_name + "' is empty.");

    for (size_t i = 0; i < signal.size(); ++i) {
        if (signal[i] < 0.0)
            throw std::runtime_error("Poisson noise requires non-negative values.");
        std::poisson_distribution<int> dist(signal[i]);
        signal[i] = static_cast<double>(dist(random_generator));
    }
}

void SignalGenerator::_apply_poisson_noise_as_gaussian_to_signal(const std::string &signal_name) {
    auto& signal = data_dict[signal_name];
    if (signal.empty())
        throw std::runtime_error("Signal '" + signal_name + "' is empty.");

    for (size_t i = 0; i < signal.size(); ++i) {
        if (signal[i] < 0.0)
            throw std::runtime_error("Poisson noise requires non-negative values.");
        const double mean = signal[i];
        const double stdev = std::sqrt(signal[i]);
        std::normal_distribution<double> dist(mean, stdev);
        signal[i] = std::round(dist(random_generator));
    }
}

void SignalGenerator::apply_poisson_noise() {
    for (const auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        _apply_mixed_poisson_noise_to_signal(entry.first);
    }
}
