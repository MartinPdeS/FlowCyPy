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

void SignalGenerator::multiply_signal(const std::string& signal_name, double factor) {
    auto it = data_dict.find(signal_name);
    if (it == data_dict.end())
        throw std::runtime_error("Signal '" + signal_name + "' does not exist.");

    auto& vec = it->second;
    const size_t n = vec.size();
    double* __restrict data = vec.data();

    #pragma omp parallel for schedule(static)
    for (long long i = 0; i < static_cast<long long>(n); ++i) {
        data[i] *= factor;
    }
}


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
    const std::vector<double> &sigmas,
    const std::vector<double> &centers,
    const std::vector<double> &coupling_power,
    double background_power)
{
    assert_time_signal_ready();
    const auto& time = data_dict.at(TIME_KEY);

    if (!(sigmas.size() == centers.size() && centers.size() == coupling_power.size()))
        throw std::runtime_error("sigmas, centers, and coupling_power must have the same size.");

    for (auto &entry : data_dict) {
        if (entry.first == TIME_KEY) continue;
        utils::generate_pulses_signal(entry.second, sigmas, centers, coupling_power, time, background_power);
    }
}

void SignalGenerator::generate_pulses_signal(
    const std::string& signal_name,
    const std::vector<double> &sigmas,
    const std::vector<double> &centers,
    const std::vector<double> &coupling_power,
    double background_power)
{
    assert_signal_exists(signal_name);
    assert_time_signal_ready();
    const auto& time = data_dict.at(TIME_KEY);

    if (!(sigmas.size() == centers.size() && centers.size() == coupling_power.size()))
        throw std::runtime_error("sigmas, centers, and coupling_power must have the same size.");

    utils::generate_pulses_signal(data_dict[signal_name], sigmas, centers, coupling_power, time, background_power);
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

void SignalGenerator::add_array_to_signal(
    const std::string& signal_name,
    const std::vector<double>& added_array)
{
    assert_signal_exists(signal_name);

    auto& signal = data_dict[signal_name];
    if (added_array.size() != signal.size())
        throw std::runtime_error("Size mismatch in add_array_to_signal for '" + signal_name + "'.");

    const size_t n = signal.size();
    const double* __restrict a = added_array.data();
    double* __restrict s = signal.data();

    #pragma omp parallel for schedule(static)
    for (long long i = 0; i < static_cast<long long>(n); ++i) {
        s[i] += a[i];
    }
}

void SignalGenerator::convolve_signal_with_gaussian(
    const std::string& signal_name,
    double sigma)
{
    assert_signal_exists(signal_name);
    assert_time_signal_ready();

    auto& signal = data_dict[signal_name];
    const auto& time = data_dict.at(TIME_KEY);
    const size_t n = signal.size();

    if (n < 2)
        throw std::runtime_error("Signal '" + signal_name + "' too short for convolution.");

    // Estimate time step from first two samples
    const double dt = time[1] - time[0];

    // ------------------- Build Gaussian kernel -------------------
    std::vector<double> kernel(n);
    const double sigma_squared = sigma * sigma;

    for (size_t i = 0; i < n; ++i) {
        double t = (static_cast<double>(i) - static_cast<double>(n) / 2.0) * dt;
        kernel[i] = std::exp(-(t * t) / (2.0 * sigma_squared));
    }

    // Normalize kernel
    double sum = 0.0;
    for (double v : kernel) sum += v;
    for (double& v : kernel) v /= sum;

    // ------------------- FFT of signal and kernel -------------------
    std::vector<std::complex<double>> fft_signal(n);
    std::vector<std::complex<double>> fft_kernel(n);

    fftw_plan plan_signal = fftw_plan_dft_r2c_1d(
        static_cast<int>(n),
        signal.data(),
        reinterpret_cast<fftw_complex*>(fft_signal.data()),
        FFTW_ESTIMATE);

    fftw_plan plan_kernel = fftw_plan_dft_r2c_1d(
        static_cast<int>(n),
        kernel.data(),
        reinterpret_cast<fftw_complex*>(fft_kernel.data()),
        FFTW_ESTIMATE);

    fftw_execute(plan_signal);
    fftw_execute(plan_kernel);

    fftw_destroy_plan(plan_signal);
    fftw_destroy_plan(plan_kernel);

    // ------------------- Frequency domain multiplication -------------------
    const size_t n_fft = n; // complex values with size n for C2C after cast

    for (size_t i = 0; i < n_fft; ++i) {
        fft_signal[i] *= fft_kernel[i];
    }

    // ------------------- Inverse FFT -------------------
    fftw_plan plan_inverse = fftw_plan_dft_c2r_1d(
        static_cast<int>(n),
        reinterpret_cast<fftw_complex*>(fft_signal.data()),
        signal.data(),
        FFTW_ESTIMATE);

    fftw_execute(plan_inverse);
    fftw_destroy_plan(plan_inverse);

    // FFTW gives unnormalized inverse. Divide by n.
    for (size_t i = 0; i < n; ++i)
        signal[i] /= static_cast<double>(n);
}


void SignalGenerator::add_gamma_trace(
    const std::string& signal_name,
    double shape,
    double scale,
    double gaussian_sigma)
{
    assert_signal_exists(signal_name);

    if (shape <= 0.0 || scale <= 0.0)
        throw std::runtime_error("add_gamma_trace requires positive shape and scale.");

    std::gamma_distribution<double> gamma_dist(shape, scale);

    std::vector<double> gamma_trace(n_elements);
    for (size_t i = 0; i < n_elements; ++i) {
        gamma_trace[i] = gamma_dist(random_generator);
    }

    // Optional Gaussian convolution
    if (gaussian_sigma > 0.0) {
        // Create kernel
        std::vector<double> kernel(n_elements);
        const auto& time = data_dict.at(TIME_KEY);

        double dt = time[1] - time[0];
        double sigma2 = gaussian_sigma * gaussian_sigma;

        for (size_t i = 0; i < n_elements; ++i) {
            double t = (static_cast<double>(i) - static_cast<double>(n_elements) / 2.0) * dt;
            kernel[i] = std::exp(-(t * t) / (2.0 * sigma2));
        }

        // Normalize
        double sum = 0.0;
        for (double v : kernel) sum += v;
        for (double& v : kernel) v /= sum;

        // FFTW convolution
        std::vector<std::complex<double>> fft_trace(n_elements);
        std::vector<std::complex<double>> fft_kernel(n_elements);

        fftw_plan plan_trace = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            gamma_trace.data(),
            reinterpret_cast<fftw_complex*>(fft_trace.data()),
            FFTW_ESTIMATE);

        fftw_plan plan_kernel = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            kernel.data(),
            reinterpret_cast<fftw_complex*>(fft_kernel.data()),
            FFTW_ESTIMATE);

        fftw_execute(plan_trace);
        fftw_execute(plan_kernel);

        fftw_destroy_plan(plan_trace);
        fftw_destroy_plan(plan_kernel);

        for (size_t i = 0; i < n_elements; ++i) {
            fft_trace[i] *= fft_kernel[i];
        }

        fftw_plan plan_inverse = fftw_plan_dft_c2r_1d(
            static_cast<int>(n_elements),
            reinterpret_cast<fftw_complex*>(fft_trace.data()),
            gamma_trace.data(),
            FFTW_ESTIMATE);

        fftw_execute(plan_inverse);
        fftw_destroy_plan(plan_inverse);

        for (size_t i = 0; i < n_elements; ++i) {
            gamma_trace[i] /= static_cast<double>(n_elements);
        }
    }

    // Add result to the signal
    add_array_to_signal(signal_name, gamma_trace);
}
