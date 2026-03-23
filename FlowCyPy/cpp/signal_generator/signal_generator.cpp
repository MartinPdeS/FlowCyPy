#include "signal_generator.h"

#include <complex>
#include <fftw3.h>

#include <utils/utils.h>


SignalGenerator::SignalGenerator(size_t n_elements)
    : n_elements(n_elements),
      random_generator(std::mt19937(std::random_device{}()))
{
    if (n_elements == 0) {
        throw std::runtime_error("SignalGenerator requires n_elements > 0.");
    }
}


void SignalGenerator::set_seed(uint64_t seed) {
    random_generator.seed(seed);
}


size_t SignalGenerator::get_number_of_elements() const {
    return n_elements;
}


bool SignalGenerator::has_channel(const std::string& channel) const {
    return data_dict.find(channel) != data_dict.end();
}


bool SignalGenerator::has_time_channel() const {
    return has_channel(TIME_KEY);
}


std::vector<std::string> SignalGenerator::get_channel_names() const {
    std::vector<std::string> channel_names;
    channel_names.reserve(data_dict.size());

    for (const auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }
        channel_names.push_back(channel_name);
    }

    return channel_names;
}


// -----------------------------------------------------------------------------
// Internal checks
// -----------------------------------------------------------------------------

void SignalGenerator::assert_channel_exists(const std::string& channel) const {
    if (!has_channel(channel)) {
        throw std::runtime_error("Channel '" + channel + "' does not exist.");
    }
}


void SignalGenerator::assert_valid_size(size_t vector_size, const std::string& object_name) const {
    if (vector_size != n_elements) {
        throw std::runtime_error(
            object_name + " size does not match n_elements."
        );
    }
}


void SignalGenerator::assert_time_channel_ready() const {
    auto iterator = data_dict.find(TIME_KEY);

    if (iterator == data_dict.end()) {
        throw std::runtime_error(
            "Time channel is missing. Add '" + std::string(TIME_KEY) + "' before calling this method."
        );
    }

    if (iterator->second.size() != n_elements) {
        throw std::runtime_error("Time channel size does not match n_elements.");
    }
}


// -----------------------------------------------------------------------------
// Time channel
// -----------------------------------------------------------------------------

void SignalGenerator::set_time_channel(const std::vector<double>& time_values) {
    assert_valid_size(time_values.size(), "Time channel");
    data_dict[TIME_KEY] = time_values;
}


std::vector<double>& SignalGenerator::get_time_channel() {
    assert_time_channel_ready();
    return data_dict.at(TIME_KEY);
}


const std::vector<double>& SignalGenerator::get_time_channel_const() const {
    assert_time_channel_ready();
    return data_dict.at(TIME_KEY);
}


double SignalGenerator::get_time_step() const {
    const auto& time_channel = get_time_channel_const();

    if (time_channel.size() < 2) {
        throw std::runtime_error("Time channel must contain at least two samples.");
    }

    const double time_step = time_channel[1] - time_channel[0];

    if (time_step <= 0.0) {
        throw std::runtime_error("Time channel must be strictly increasing.");
    }

    return time_step;
}


double SignalGenerator::get_sampling_rate() const {
    return 1.0 / get_time_step();
}


// -----------------------------------------------------------------------------
// Channel creation and retrieval
// -----------------------------------------------------------------------------

void SignalGenerator::add_channel(
    const std::string& channel,
    const std::vector<double>& channel_data
) {
    if (has_channel(channel)) {
        throw std::runtime_error("Channel '" + channel + "' already exists.");
    }

    assert_valid_size(channel_data.size(), "Channel '" + channel + "'");
    data_dict.emplace(channel, channel_data);
}


void SignalGenerator::create_channel(const std::string& channel, double constant_value) {
    if (has_channel(channel)) {
        throw std::runtime_error("Channel '" + channel + "' already exists.");
    }

    data_dict.emplace(channel, std::vector<double>(n_elements, constant_value));
}


void SignalGenerator::create_zero_channel(const std::string& channel) {
    create_channel(channel, 0.0);
}


std::vector<double>& SignalGenerator::get_channel(const std::string& channel) {
    assert_channel_exists(channel);
    return data_dict.at(channel);
}


const std::vector<double>& SignalGenerator::get_channel_const(const std::string& channel) const {
    assert_channel_exists(channel);
    return data_dict.at(channel);
}


// -----------------------------------------------------------------------------
// Basic arithmetic
// -----------------------------------------------------------------------------

void SignalGenerator::add_constant(double constant_value) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        add_constant_to_channel(channel_name, constant_value);
    }
}


void SignalGenerator::add_constant_to_channel(const std::string& channel, double constant_value) {
    auto& channel_values = get_channel(channel);
    const size_t number_of_values = channel_values.size();
    double* channel_data = channel_values.data();

    #pragma omp parallel for schedule(static)
    for (long long index = 0; index < static_cast<long long>(number_of_values); ++index) {
        channel_data[index] += constant_value;
    }
}


void SignalGenerator::multiply(double factor) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        multiply_channel(channel_name, factor);
    }
}


void SignalGenerator::multiply_channel(const std::string& channel, double factor) {
    auto& channel_values = get_channel(channel);
    const size_t number_of_values = channel_values.size();
    double* channel_data = channel_values.data();

    #pragma omp parallel for schedule(static)
    for (long long index = 0; index < static_cast<long long>(number_of_values); ++index) {
        channel_data[index] *= factor;
    }
}


void SignalGenerator::round() {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        round_channel(channel_name);
    }
}


void SignalGenerator::round_channel(const std::string& channel) {
    auto& channel_values = get_channel(channel);
    const size_t number_of_values = channel_values.size();
    double* channel_data = channel_values.data();

    #pragma omp parallel for schedule(static)
    for (long long index = 0; index < static_cast<long long>(number_of_values); ++index) {
        channel_data[index] = std::round(channel_data[index]);
    }
}


void SignalGenerator::add_array_to_channel(
    const std::string& channel,
    const std::vector<double>& added_array
) {
    auto& channel_values = get_channel(channel);

    if (added_array.size() != channel_values.size()) {
        throw std::runtime_error(
            "Size mismatch in add_array_to_channel for channel '" + channel + "'."
        );
    }

    const size_t number_of_values = channel_values.size();
    const double* added_array_data = added_array.data();
    double* channel_data = channel_values.data();

    #pragma omp parallel for schedule(static)
    for (long long index = 0; index < static_cast<long long>(number_of_values); ++index) {
        channel_data[index] += added_array_data[index];
    }
}


// -----------------------------------------------------------------------------
// Signal processing
// -----------------------------------------------------------------------------

void SignalGenerator::apply_baseline_restoration(int window_size) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        utils::apply_baseline_restoration_to_signal(channel_values, window_size);
    }
}


void SignalGenerator::apply_butterworth_lowpass_filter(
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain
) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        utils::apply_butterworth_lowpass_filter_to_signal(
            channel_values,
            sampling_rate,
            cutoff_frequency,
            order,
            gain
        );
    }
}


void SignalGenerator::apply_butterworth_lowpass_filter_to_channel(
    const std::string& channel,
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain
) {
    auto& channel_values = get_channel(channel);

    utils::apply_butterworth_lowpass_filter_to_signal(
        channel_values,
        sampling_rate,
        cutoff_frequency,
        order,
        gain
    );
}


void SignalGenerator::apply_bessel_lowpass_filter(
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain
) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        utils::apply_bessel_lowpass_filter_to_signal(
            channel_values,
            sampling_rate,
            cutoff_frequency,
            order,
            gain
        );
    }
}


void SignalGenerator::apply_bessel_lowpass_filter_to_channel(
    const std::string& channel,
    double sampling_rate,
    double cutoff_frequency,
    int order,
    double gain
) {
    auto& channel_values = get_channel(channel);

    utils::apply_bessel_lowpass_filter_to_signal(
        channel_values,
        sampling_rate,
        cutoff_frequency,
        order,
        gain
    );
}


// -----------------------------------------------------------------------------
// Pulse generation
// -----------------------------------------------------------------------------

void SignalGenerator::generate_pulses(
    const std::vector<double>& sigmas,
    const std::vector<double>& centers,
    const std::vector<double>& coupling_power,
    double background_power
) {
    assert_time_channel_ready();

    if (!(sigmas.size() == centers.size() && centers.size() == coupling_power.size())) {
        throw std::runtime_error(
            "sigmas, centers, and coupling_power must have the same size."
        );
    }

    const auto& time_channel = get_time_channel_const();

    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        utils::generate_pulses_signal(
            channel_values,
            sigmas,
            centers,
            coupling_power,
            time_channel,
            background_power
        );
    }
}


void SignalGenerator::generate_pulses_to_channel(
    const std::string& channel,
    const std::vector<double>& sigmas,
    const std::vector<double>& centers,
    const std::vector<double>& coupling_power,
    double background_power
) {
    assert_time_channel_ready();

    if (!(sigmas.size() == centers.size() && centers.size() == coupling_power.size())) {
        throw std::runtime_error(
            "sigmas, centers, and coupling_power must have the same size."
        );
    }

    auto& channel_values = get_channel(channel);
    const auto& time_channel = get_time_channel_const();

    utils::generate_pulses_signal(
        channel_values,
        sigmas,
        centers,
        coupling_power,
        time_channel,
        background_power
    );
}


// -----------------------------------------------------------------------------
// Noise
// -----------------------------------------------------------------------------

void SignalGenerator::add_gaussian_noise(double mean, double standard_deviation) {
    for (auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        utils::add_gaussian_noise_to_signal(
            channel_values,
            mean,
            standard_deviation,
            random_generator
        );
    }
}


void SignalGenerator::add_gaussian_noise_to_channel(
    const std::string& channel,
    double mean,
    double standard_deviation
) {
    auto& channel_values = get_channel(channel);

    utils::add_gaussian_noise_to_signal(
        channel_values,
        mean,
        standard_deviation,
        random_generator
    );
}


void SignalGenerator::apply_poisson_noise() {
    for (const auto& [channel_name, channel_values] : data_dict) {
        if (channel_name == TIME_KEY) {
            continue;
        }

        apply_mixed_poisson_noise_to_channel(channel_name);
    }
}


void SignalGenerator::apply_poisson_noise_to_channel(const std::string& channel) {
    assert_channel_exists(channel);
    apply_mixed_poisson_noise_to_channel(channel);
}


void SignalGenerator::apply_poisson_noise_through_conversion(
    const std::string& channel,
    double watt_to_photon
) {
    if (watt_to_photon <= 0.0) {
        throw std::runtime_error("watt_to_photon must be strictly positive.");
    }

    multiply_channel(channel, watt_to_photon);
    apply_poisson_noise_to_channel(channel);
    multiply_channel(channel, 1.0 / watt_to_photon);
}


void SignalGenerator::apply_strict_poisson_noise_to_channel(const std::string& channel) {
    auto& channel_values = get_channel(channel);

    if (channel_values.empty()) {
        throw std::runtime_error("Channel '" + channel + "' is empty.");
    }

    for (double& value : channel_values) {
        if (value < 0.0) {
            throw std::runtime_error("Poisson noise requires non negative values.");
        }

        std::poisson_distribution<long long> poisson_distribution(value);
        value = static_cast<double>(poisson_distribution(random_generator));
    }
}


void SignalGenerator::apply_gaussian_approximated_poisson_noise_to_channel(
    const std::string& channel
) {
    auto& channel_values = get_channel(channel);

    if (channel_values.empty()) {
        throw std::runtime_error("Channel '" + channel + "' is empty.");
    }

    for (double& value : channel_values) {
        if (value < 0.0) {
            throw std::runtime_error("Poisson noise requires non negative values.");
        }

        const double mean_value = value;
        const double standard_deviation = std::sqrt(value);

        std::normal_distribution<double> normal_distribution(
            mean_value,
            standard_deviation
        );

        value = std::round(normal_distribution(random_generator));
    }
}


void SignalGenerator::apply_mixed_poisson_noise_to_channel(const std::string& channel) {
    auto& channel_values = get_channel(channel);

    if (channel_values.empty()) {
        throw std::runtime_error("Channel '" + channel + "' is empty.");
    }

    constexpr double gaussian_approximation_threshold = 1e6;

    for (double& value : channel_values) {
        if (value < 0.0) {
            throw std::runtime_error("Poisson noise requires non negative values.");
        }

        if (value < gaussian_approximation_threshold) {
            std::poisson_distribution<long long> poisson_distribution(value);
            value = static_cast<double>(poisson_distribution(random_generator));
        }
        else {
            std::normal_distribution<double> normal_distribution(
                value,
                std::sqrt(value)
            );
            value = std::round(normal_distribution(random_generator));
        }
    }
}


// -----------------------------------------------------------------------------
// Convolution and trace generation
// -----------------------------------------------------------------------------

void SignalGenerator::convolve_channel_with_gaussian(
    const std::string& channel,
    double sigma
) {
    if (sigma <= 0.0) {
        throw std::runtime_error("Gaussian convolution sigma must be strictly positive.");
    }

    auto& channel_values = get_channel(channel);
    const auto& time_channel = get_time_channel_const();

    const size_t number_of_values = channel_values.size();

    if (number_of_values < 2) {
        throw std::runtime_error(
            "Channel '" + channel + "' is too short for convolution."
        );
    }

    const double time_step = get_time_step();
    const double sigma_squared = sigma * sigma;

    std::vector<double> gaussian_kernel(number_of_values);

    for (size_t index = 0; index < number_of_values; ++index) {
        const double shifted_time =
            (static_cast<double>(index) - static_cast<double>(number_of_values) / 2.0) * time_step;

        gaussian_kernel[index] =
            std::exp(-(shifted_time * shifted_time) / (2.0 * sigma_squared));
    }

    double kernel_sum = 0.0;
    for (double value : gaussian_kernel) {
        kernel_sum += value;
    }

    for (double& value : gaussian_kernel) {
        value /= kernel_sum;
    }

    const size_t number_of_frequency_bins = number_of_values / 2 + 1;

    std::vector<std::complex<double>> channel_spectrum(number_of_frequency_bins);
    std::vector<std::complex<double>> kernel_spectrum(number_of_frequency_bins);

    fftw_plan channel_forward_plan = fftw_plan_dft_r2c_1d(
        static_cast<int>(number_of_values),
        channel_values.data(),
        reinterpret_cast<fftw_complex*>(channel_spectrum.data()),
        FFTW_ESTIMATE
    );

    fftw_plan kernel_forward_plan = fftw_plan_dft_r2c_1d(
        static_cast<int>(number_of_values),
        gaussian_kernel.data(),
        reinterpret_cast<fftw_complex*>(kernel_spectrum.data()),
        FFTW_ESTIMATE
    );

    fftw_execute(channel_forward_plan);
    fftw_execute(kernel_forward_plan);

    fftw_destroy_plan(channel_forward_plan);
    fftw_destroy_plan(kernel_forward_plan);

    for (size_t index = 0; index < number_of_frequency_bins; ++index) {
        channel_spectrum[index] *= kernel_spectrum[index];
    }

    fftw_plan inverse_plan = fftw_plan_dft_c2r_1d(
        static_cast<int>(number_of_values),
        reinterpret_cast<fftw_complex*>(channel_spectrum.data()),
        channel_values.data(),
        FFTW_ESTIMATE
    );

    fftw_execute(inverse_plan);
    fftw_destroy_plan(inverse_plan);

    for (double& value : channel_values) {
        value /= static_cast<double>(number_of_values);
    }

    (void)time_channel;
}


std::vector<double> SignalGenerator::add_gamma_trace_to_channel(
    const std::string& channel,
    double shape,
    double scale,
    double gaussian_sigma
) {
    assert_channel_exists(channel);

    if (shape <= 0.0) {
        throw std::runtime_error("Gamma shape must be strictly positive.");
    }

    if (scale <= 0.0) {
        throw std::runtime_error("Gamma scale must be strictly positive.");
    }

    std::gamma_distribution<double> gamma_distribution(shape, scale);

    std::vector<double> gamma_trace(n_elements, 0.0);

    for (double& value : gamma_trace) {
        value = gamma_distribution(random_generator);
    }

    if (gaussian_sigma > 0.0) {
        assert_time_channel_ready();

        if (n_elements < 2) {
            throw std::runtime_error("At least two time samples are required for Gaussian convolution.");
        }

        const double time_step = get_time_step();
        const double sigma_squared = gaussian_sigma * gaussian_sigma;

        std::vector<double> gaussian_kernel(n_elements, 0.0);

        for (size_t index = 0; index < n_elements; ++index) {
            const double shifted_time =
                (static_cast<double>(index) - static_cast<double>(n_elements) / 2.0) * time_step;

            gaussian_kernel[index] =
                std::exp(-(shifted_time * shifted_time) / (2.0 * sigma_squared));
        }

        double kernel_sum = 0.0;
        for (double value : gaussian_kernel) {
            kernel_sum += value;
        }

        for (double& value : gaussian_kernel) {
            value /= kernel_sum;
        }

        const size_t number_of_frequency_bins = n_elements / 2 + 1;

        std::vector<std::complex<double>> gamma_trace_spectrum(number_of_frequency_bins);
        std::vector<std::complex<double>> kernel_spectrum(number_of_frequency_bins);

        fftw_plan gamma_trace_forward_plan = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            gamma_trace.data(),
            reinterpret_cast<fftw_complex*>(gamma_trace_spectrum.data()),
            FFTW_ESTIMATE
        );

        fftw_plan kernel_forward_plan = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            gaussian_kernel.data(),
            reinterpret_cast<fftw_complex*>(kernel_spectrum.data()),
            FFTW_ESTIMATE
        );

        fftw_execute(gamma_trace_forward_plan);
        fftw_execute(kernel_forward_plan);

        fftw_destroy_plan(gamma_trace_forward_plan);
        fftw_destroy_plan(kernel_forward_plan);

        for (size_t index = 0; index < number_of_frequency_bins; ++index) {
            gamma_trace_spectrum[index] *= kernel_spectrum[index];
        }

        fftw_plan inverse_plan = fftw_plan_dft_c2r_1d(
            static_cast<int>(n_elements),
            reinterpret_cast<fftw_complex*>(gamma_trace_spectrum.data()),
            gamma_trace.data(),
            FFTW_ESTIMATE
        );

        fftw_execute(inverse_plan);
        fftw_destroy_plan(inverse_plan);

        for (double& value : gamma_trace) {
            value /= static_cast<double>(n_elements);
        }
    }

    add_array_to_channel(channel, gamma_trace);

    return gamma_trace;
}

std::vector<double> SignalGenerator::get_gamma_trace(
    double shape,
    double scale,
    double gaussian_sigma
) {
    if (shape <= 0.0) {
        throw std::runtime_error("Gamma shape must be strictly positive.");
    }

    if (scale <= 0.0) {
        throw std::runtime_error("Gamma scale must be strictly positive.");
    }

    std::gamma_distribution<double> gamma_distribution(shape, scale);

    std::vector<double> gamma_trace(n_elements, 0.0);

    for (double& value : gamma_trace) {
        value = gamma_distribution(random_generator);
    }

    if (gaussian_sigma > 0.0) {

        if (n_elements < 2) {
            throw std::runtime_error("At least two time samples are required for Gaussian convolution.");
        }

        const double time_step = get_time_step();
        const double sigma_squared = gaussian_sigma * gaussian_sigma;

        std::vector<double> gaussian_kernel(n_elements, 0.0);

        for (size_t index = 0; index < n_elements; ++index) {
            const double shifted_time =
                (static_cast<double>(index) - static_cast<double>(n_elements) / 2.0) * time_step;

            gaussian_kernel[index] =
                std::exp(-(shifted_time * shifted_time) / (2.0 * sigma_squared));
        }

        double kernel_sum = 0.0;
        for (double value : gaussian_kernel) {
            kernel_sum += value;
        }

        for (double& value : gaussian_kernel) {
            value /= kernel_sum;
        }

        const size_t number_of_frequency_bins = n_elements / 2 + 1;

        std::vector<std::complex<double>> gamma_trace_spectrum(number_of_frequency_bins);
        std::vector<std::complex<double>> kernel_spectrum(number_of_frequency_bins);

        fftw_plan gamma_trace_forward_plan = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            gamma_trace.data(),
            reinterpret_cast<fftw_complex*>(gamma_trace_spectrum.data()),
            FFTW_ESTIMATE
        );

        fftw_plan kernel_forward_plan = fftw_plan_dft_r2c_1d(
            static_cast<int>(n_elements),
            gaussian_kernel.data(),
            reinterpret_cast<fftw_complex*>(kernel_spectrum.data()),
            FFTW_ESTIMATE
        );

        fftw_execute(gamma_trace_forward_plan);
        fftw_execute(kernel_forward_plan);

        fftw_destroy_plan(gamma_trace_forward_plan);
        fftw_destroy_plan(kernel_forward_plan);

        for (size_t index = 0; index < number_of_frequency_bins; ++index) {
            gamma_trace_spectrum[index] *= kernel_spectrum[index];
        }

        fftw_plan inverse_plan = fftw_plan_dft_c2r_1d(
            static_cast<int>(n_elements),
            reinterpret_cast<fftw_complex*>(gamma_trace_spectrum.data()),
            gamma_trace.data(),
            FFTW_ESTIMATE
        );

        fftw_execute(inverse_plan);
        fftw_destroy_plan(inverse_plan);

        for (double& value : gamma_trace) {
            value /= static_cast<double>(n_elements);
        }
    }

    return gamma_trace;
}
