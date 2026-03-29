#include <opto_electronics/source/source.h>


BaseSource::BaseSource(
    const double wavelength,
    const double rin,
    const double optical_power,
    const double polarization,
    const double bandwidth,
    const bool include_shot_noise,
    const bool include_rin_noise,
    const bool debug_mode
)
    : wavelength(wavelength),
    rin(rin),
    optical_power(optical_power),
    amplitude(0.0),
    polarization(polarization),
    bandwidth(bandwidth),
    include_shot_noise(include_shot_noise),
    include_rin_noise(include_rin_noise),
    debug_mode(debug_mode)
{
    if (this->wavelength <= 0.0) {
        throw std::runtime_error("wavelength must be strictly positive.");
    }

    if (this->optical_power < 0.0) {
        throw std::runtime_error("optical_power must be non negative.");
    }

    if (this->debug_mode) {
        std::printf(
            "[BaseSource] Initialized | wavelength=%g m | rin=%g dB/Hz | optical_power=%g W | polarization=%g rad | include_shot_noise=%d | include_rin_noise=%d\n",
            this->wavelength,
            this->rin,
            this->optical_power,
            this->polarization,
            static_cast<int>(this->include_shot_noise),
            static_cast<int>(this->include_rin_noise)
        );
    }
}

void BaseSource::test_openmp() {
    std::printf("max threads = %d\n", omp_get_max_threads());
    #pragma omp parallel
    {
        #pragma omp single
        std::printf("parallel threads = %d\n", omp_get_num_threads());
    }
}


double BaseSource::get_frequency() const {
    return Constants::light_speed / this->wavelength;
}


double BaseSource::get_photon_energy() const {
    return Constants::plank * this->get_frequency();
}


double BaseSource::get_rin_linear() const {
    return std::pow(10.0, this->rin / 10.0);
}


double BaseSource::get_watt_to_photon_factor(const double time_step) const {
    if (time_step <= 0.0) {
        throw std::runtime_error("time_step must be strictly positive.");
    }

    return time_step / this->get_photon_energy();
}


double BaseSource::get_time_step_from_time_array(const std::vector<double>& time_array) const {
    if (time_array.size() < 2) {
        throw std::runtime_error("time_array must contain at least two samples.");
    }

    const double time_step = time_array[1] - time_array[0];

    if (time_step <= 0.0) {
        throw std::runtime_error("time_array must be strictly increasing.");
    }

    for (size_t index = 2; index < time_array.size(); ++index) {
        const double current_step = time_array[index] - time_array[index - 1];

        if (current_step <= 0.0) {
            throw std::runtime_error("time_array must be strictly increasing.");
        }

        if (std::abs(current_step - time_step) > 1e-12 * std::max(1.0, std::abs(time_step))) {
            throw std::runtime_error("time_array must be uniformly sampled.");
        }
    }

    return time_step;
}


void BaseSource::add_rin_to_signal(std::vector<double>& signal_values) const {
    if (std::isnan(this->bandwidth)) {
        if (debug_mode) {
            std::printf("[RIN] bandwidth is NaN → RIN disabled\n");
        }
        return;
    }

    if (this->bandwidth <= 0.0) {
        throw std::runtime_error("bandwidth must be strictly positive.");
    }

    const double rin_linear   = this->get_rin_linear();
    const double sigma_factor = std::sqrt(rin_linear * this->bandwidth);

    if (debug_mode) {
        std::printf(
            "[RIN] rin_linear = %.6e | bandwidth = %.6e | sigma_factor = %.6e\n",
            rin_linear, this->bandwidth, sigma_factor
        );
    }

    const size_t N = signal_values.size();

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (debug_mode) {
                std::printf("[RIN] using %d OpenMP threads\n", omp_get_num_threads());
            }
        }

        static thread_local std::random_device rd;
        static thread_local std::mt19937 gen(rd());
        static thread_local std::normal_distribution<double> standard_normal(0.0, 1.0);

        #pragma omp for
        for (size_t i = 0; i < N; ++i) {
            const double value = signal_values[i];

            if (value < 0.0) {
                throw std::runtime_error("RIN cannot be applied to negative signal values.");
            }

            const double sigma = sigma_factor * value;
            const double noise = standard_normal(gen) * sigma;

            signal_values[i] += noise;
        }
    }
}




void BaseSource::add_common_rin_to_signals(std::vector<std::vector<double>>& signal_values_per_channel) const {
    if (std::isnan(this->bandwidth)) {
        if (debug_mode) {
            std::printf("[CommonRIN] bandwidth is NaN → RIN disabled\n");
        }
        return;
    }

    if (this->bandwidth <= 0.0) {
        throw std::runtime_error("bandwidth must be strictly positive.");
    }

    if (signal_values_per_channel.empty()) {
        throw std::runtime_error("signal_values_per_channel must not be empty.");
    }

    const size_t N = signal_values_per_channel.front().size();
    for (const auto& ch : signal_values_per_channel) {
        if (ch.size() != N) {
            throw std::runtime_error("All detector channels must have the same number of samples.");
        }
    }

    const double rin_linear = this->get_rin_linear();
    const double sigma      = std::sqrt(rin_linear * this->bandwidth);

    if (debug_mode) {
        std::printf(
            "[CommonRIN] rin_linear = %.6e | bandwidth = %.6e | sigma = %.6e\n",
            rin_linear, this->bandwidth, sigma
        );
    }

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (debug_mode) {
                std::printf("[CommonRIN] using %d OpenMP threads\n", omp_get_num_threads());
            }
        }
        static thread_local std::random_device random_device;
        static thread_local std::mt19937 generator(random_device());
        static thread_local std::normal_distribution<double> standard_normal(0.0, 1.0);

        #pragma omp for
        for (size_t t = 0; t < N; ++t) {
            const double fluct = standard_normal(generator) * sigma;

            for (auto& ch : signal_values_per_channel) {
                if (ch[t] < 0.0) {
                    throw std::runtime_error("RIN cannot be applied to negative optical power values.");
                }
                ch[t] *= (1.0 + fluct);
            }
        }
    }
}




void BaseSource::add_shot_noise_to_signal(std::vector<double>& power_values, const double time_step) const {
    if (time_step <= 0.0) {
        throw std::runtime_error("time_step must be strictly positive.");
    }

    const double photon_energy = this->get_photon_energy();
    const double watt_to_photon = time_step / photon_energy;

    if (debug_mode && !power_values.empty()) {
        const double minimum_power = *std::min_element(power_values.begin(), power_values.end());
        const double maximum_power = *std::max_element(power_values.begin(), power_values.end());

        std::printf(
            "[ShotNoise] min=%.6e W | max=%.6e W | photon_energy=%.6e J | factor=%.6e\n",
            minimum_power,
            maximum_power,
            photon_energy,
            watt_to_photon
        );
    }

    bool found_negative_input = false;
    size_t bad_index = 0;
    double bad_value = 0.0;

    const size_t number_of_samples = power_values.size();

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (debug_mode) {
                std::printf("[ShotNoise] using %d OpenMP threads\n", omp_get_num_threads());
            }
        }

        static thread_local std::random_device random_device;
        static thread_local std::mt19937 generator(random_device());
        static thread_local std::normal_distribution<double> standard_normal(0.0, 1.0);

        bool local_found_negative_input = false;
        size_t local_bad_index = 0;
        double local_bad_value = 0.0;

        #pragma omp for
        for (size_t sample_index = 0; sample_index < number_of_samples; ++sample_index) {
            if (found_negative_input) {
                continue;
            }

            const double power_value = power_values[sample_index];

            if (power_value < 0.0) {
                local_found_negative_input = true;
                local_bad_index = sample_index;
                local_bad_value = power_value;
                continue;
            }

            const double mean_photons = power_value * watt_to_photon;
            double noisy_photons = 0.0;

            if (mean_photons < 100.0) {
                std::poisson_distribution<int> poisson_distribution(mean_photons);
                noisy_photons = static_cast<double>(poisson_distribution(generator));
            } else {
                noisy_photons = std::max(
                    0.0,
                    mean_photons + standard_normal(generator) * std::sqrt(mean_photons)
                );
            }

            power_values[sample_index] = noisy_photons / watt_to_photon;
        }

        #pragma omp critical
        {
            if (local_found_negative_input && !found_negative_input) {
                found_negative_input = true;
                bad_index = local_bad_index;
                bad_value = local_bad_value;
            }
        }
    }

    if (found_negative_input) {
        throw std::runtime_error(
            "Shot noise received a negative optical power sample, which is nonphysical. "
            "Shot noise can only be applied to nonnegative optical power. "
            "This usually indicates that the source RIN noise produces invalid power values. "
            "First invalid sample: index=" + std::to_string(bad_index) +
            ", value=" + std::to_string(bad_value) + " W."
        );
    }
}




std::vector<double> BaseSource::get_amplitude_signal(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& z
) const {

    this->validate_coordinate_vectors(x, y, z);

    std::vector<double> amplitudes;
    amplitudes.reserve(x.size());

    for (size_t index = 0; index < x.size(); ++index) {
        amplitudes.push_back(
            this->get_amplitude_at(
                x[index],
                y[index],
                z[index]
            )
        );
    }

    return amplitudes;
}


std::vector<double> BaseSource::get_power_signal(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& z,
    const double time_step
) const {
    (void)time_step;

    this->validate_coordinate_vectors(x, y, z);

    std::vector<double> power_values;
    power_values.reserve(x.size());

    for (size_t index = 0; index < x.size(); ++index) {
        power_values.push_back(
            this->get_power_at(
                x[index],
                y[index],
                z[index]
            )
        );
    }

    return power_values;
}


double BaseSource::get_power_at(
    const double x,
    const double y,
    const double z
) const {
    return this->optical_power * this->get_normalized_profile_value(x, y, z);
}



std::vector<double> BaseSource::convolve_with_kernel(
    const std::vector<double>& signal,
    const std::vector<double>& kernel
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal must not be empty.");
    }
    if (kernel.empty()) {
        throw std::runtime_error("kernel must not be empty.");
    }

    const int half = kernel.size() / 2;
    const int N    = signal.size();

    std::vector<double> out(N, 0.0);

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (debug_mode) {
                std::printf("[Convolution] using %d OpenMP threads\n", omp_get_num_threads());
            }
        }

        #pragma omp for
        for (int i = 0; i < N; ++i) {
            double acc = 0.0;

            for (int k = 0; k < (int)kernel.size(); ++k) {
                int idx = i + k - half;

                idx = std::abs(idx);
                if (idx >= N) idx = 2 * N - idx - 2;

                acc += signal[idx] * kernel[k];
            }

            out[i] = acc;
        }
    }

    return out;
}




std::vector<double> BaseSource::get_gamma_trace(
    const std::vector<double>& time_array,
    double shape,
    double scale,
    double mean_velocity
) const {
    const size_t N = time_array.size();
    const double dt = this->get_time_step_from_time_array(time_array);

    if (debug_mode) {
        std::printf("[GammaTrace] dt=%.6e | shape=%.6e | scale=%.6e | v=%.6e\n", dt, shape, scale, mean_velocity);
    }

    std::vector<double> latent(N);

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (debug_mode) {
                std::printf("[GammaTrace] using %d OpenMP threads\n", omp_get_num_threads());
            }
        }

        static thread_local std::random_device rd;
        static thread_local std::mt19937 gen(rd());
        std::gamma_distribution<double> gamma_dist(shape, scale);

        #pragma omp for
        for (size_t i = 0; i < N; ++i) {
            latent[i] = gamma_dist(gen);
        }
    }

    const auto kernel = this->get_temporal_kernel(dt, mean_velocity);

    return this->convolve_with_kernel(latent, kernel);
}



void BaseSource::update_amplitude() {
    this->amplitude = this->get_amplitude_at_focus();
}

void BaseSource::validate_coordinate_vectors(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& z
) const {
    if (x.size() != y.size() || x.size() != z.size()) {
        throw std::runtime_error("x, y, and z must have the same size.");
    }
}


void BaseSource::validate_pulse_vectors(
    const std::vector<double>& velocities,
    const std::vector<double>& pulse_centers,
    const std::vector<double>& pulse_amplitudes
) const {
    if (
        velocities.size() != pulse_centers.size() ||
        velocities.size() != pulse_amplitudes.size()
    ) {
        throw std::runtime_error(
            "velocities, pulse_centers, and pulse_amplitudes must have the same size."
        );
    }
}


void BaseSource::validate_velocity_vector(
    const std::vector<double>& velocity
) const {
    if (velocity.empty()) {
        throw std::runtime_error("velocity must not be empty.");
    }

    if (std::any_of(velocity.begin(), velocity.end(), [](double value) { return value <= 0.0; })) {
        throw std::runtime_error("velocity must be strictly positive.");
    }
}




Gaussian::Gaussian(
    const double wavelength,
    const double rin,
    const double optical_power,
    const double waist_y,
    const double waist_z,
    const double polarization,
    const double bandwidth,
    const bool include_shot_noise,
    const bool include_rin_noise,
    const bool debug_mode
)
    : BaseSource(
        wavelength,
        rin,
        optical_power,
        polarization,
        bandwidth,
        include_shot_noise,
        include_rin_noise,
        debug_mode
    ),
        waist_y(waist_y),
        waist_z(waist_z)
{
    if (this->waist_y <= 0.0) {
        throw std::runtime_error("waist_y must be strictly positive.");
    }

    if (this->waist_z <= 0.0) {
        throw std::runtime_error("waist_z must be strictly positive.");
    }

    this->update_amplitude();
}


void Gaussian::set_waist(
    const double waist_y,
    const double waist_z
) {
    if (waist_y <= 0.0) {
        throw std::runtime_error("waist_y must be strictly positive.");
    }

    if (waist_z <= 0.0) {
        throw std::runtime_error("waist_z must be strictly positive.");
    }

    this->waist_y = waist_y;
    this->waist_z = waist_z;
    this->update_amplitude();
}


std::vector<double> Gaussian::get_particle_width(const std::vector<double>& velocity) const {
    this->validate_velocity_vector(velocity);

    std::vector<double> widths;
    widths.reserve(velocity.size());

    for (double current_velocity : velocity) {
        widths.push_back(this->waist_z / (2.0 * current_velocity));
    }

    return widths;
}


double Gaussian::get_kernel_width_from_velocity(const double mean_velocity) const {
    if (mean_velocity <= 0.0) {
        throw std::runtime_error("mean_velocity must be strictly positive.");
    }

    return this->waist_z / (2.0 * mean_velocity);
}


std::vector<double> Gaussian::get_temporal_kernel(
    const double time_step,
    const double mean_velocity
) const {
    if (time_step <= 0.0) {
        throw std::runtime_error("time_step must be strictly positive.");
    }

    const double pulse_width = this->get_kernel_width_from_velocity(mean_velocity);
    const double sigma_in_samples = pulse_width / time_step;

    if (sigma_in_samples <= 0.0) {
        throw std::runtime_error("Gaussian kernel width must be strictly positive.");
    }

    const int half_window_size = static_cast<int>(std::ceil(4.0 * sigma_in_samples));
    const int kernel_size = 2 * half_window_size + 1;

    std::vector<double> kernel(static_cast<size_t>(kernel_size), 0.0);
    double kernel_sum = 0.0;

    for (int kernel_index = 0; kernel_index < kernel_size; ++kernel_index) {
        const int shifted_index = kernel_index - half_window_size;
        const double normalized_time =
            static_cast<double>(shifted_index) / sigma_in_samples;

        const double value = std::exp(-0.5 * normalized_time * normalized_time);

        kernel[static_cast<size_t>(kernel_index)] = value;
        kernel_sum += value;
    }

    for (double& value : kernel) {
        value /= kernel_sum;
    }

    return kernel;
}


double Gaussian::get_amplitude_at(
    const double x,
    const double y,
    const double z
) const {
    (void)x;

    return this->amplitude * std::exp(
        -(y * y) / (this->waist_y * this->waist_y)
        - (z * z) / (this->waist_z * this->waist_z)
    );
}

std::vector<double> Gaussian::generate_pulses(
    const std::vector<double>& velocities,
    const std::vector<double>& pulse_centers,
    const std::vector<double>& pulse_amplitudes,
    const std::vector<double>& time_array,
    const double base_level
) const {
    this->validate_pulse_vectors(
        velocities,
        pulse_centers,
        pulse_amplitudes
    );

    this->validate_velocity_vector(velocities);

    std::vector<double> signal;
    signal.reserve(time_array.size());

    for (double time_value : time_array) {
        double signal_value = base_level;

        for (size_t index = 0; index < velocities.size(); ++index) {
            const double pulse_width = this->waist_z / (2.0 * velocities[index]);
            const double normalized_time =
                (time_value - pulse_centers[index]) / pulse_width;

            const double exponent = -0.5 * normalized_time * normalized_time;

            signal_value += pulse_amplitudes[index] * std::exp(exponent);
        }

        signal.push_back(signal_value);
    }

    return signal;
}


double Gaussian::get_amplitude_at_focus() const {
    const double area = this->waist_y * this->waist_z;

    return std::sqrt(
        4.0 * this->optical_power /
        (
            Constants::pi *
            Constants::vacuum_permitivity *
            Constants::light_speed *
            area
        )
    );
}


double Gaussian::get_normalized_profile_value(const double x, const double y, const double z) const {
    (void)x;

    return std::exp(
        -(y * y) / (this->waist_y * this->waist_y)
        - (z * z) / (this->waist_z * this->waist_z)
    );
}




FlatTop::FlatTop(
    const double wavelength,
    const double rin,
    const double optical_power,
    const double waist_y,
    const double waist_z,
    const double polarization,
    const double bandwidth,
    const bool include_shot_noise,
    const bool include_rin_noise,
    const bool debug_mode
)
    : BaseSource(
        wavelength,
        rin,
        optical_power,
        polarization,
        bandwidth,
        include_shot_noise,
        include_rin_noise,
        debug_mode
    ),
        waist_y(waist_y),
        waist_z(waist_z)
{
    if (this->waist_y <= 0.0) {
        throw std::runtime_error("waist_y must be strictly positive.");
    }

    if (this->waist_z <= 0.0) {
        throw std::runtime_error("waist_z must be strictly positive.");
    }

    this->update_amplitude();
}


void FlatTop::set_waist(const double waist_y, const double waist_z) {
    if (waist_y <= 0.0) {
        throw std::runtime_error("waist_y must be strictly positive.");
    }

    if (waist_z <= 0.0) {
        throw std::runtime_error("waist_z must be strictly positive.");
    }

    this->waist_y = waist_y;
    this->waist_z = waist_z;
    this->update_amplitude();
}


std::vector<double> FlatTop::get_particle_width(const std::vector<double>& velocity) const {
    this->validate_velocity_vector(velocity);

    std::vector<double> widths;
    widths.reserve(velocity.size());

    for (double current_velocity : velocity) {
        widths.push_back(this->waist_z / (2.0 * current_velocity));
    }

    return widths;
}


double FlatTop::get_kernel_width_from_velocity(const double mean_velocity) const {
    if (mean_velocity <= 0.0) {
        throw std::runtime_error("mean_velocity must be strictly positive.");
    }

    return this->waist_z / (2.0 * mean_velocity);
}


std::vector<double> FlatTop::get_temporal_kernel(
    const double time_step,
    const double mean_velocity
) const {
    if (time_step <= 0.0) {
        throw std::runtime_error("time_step must be strictly positive.");
    }

    const double pulse_width = this->get_kernel_width_from_velocity(mean_velocity);
    double width_in_samples = pulse_width / time_step;

    if (width_in_samples <= 0.0) {
        throw std::runtime_error("FlatTop kernel width must be strictly positive.");
    }

    int support_in_samples = static_cast<int>(std::round(width_in_samples));

    if (support_in_samples < 1) {
        support_in_samples = 1;
    }

    if (support_in_samples % 2 == 0) {
        support_in_samples += 1;
    }

    std::vector<double> kernel(static_cast<size_t>(support_in_samples), 1.0);

    const double normalization = static_cast<double>(support_in_samples);

    for (double& value : kernel) {
        value /= normalization;
    }

    return kernel;
}


double FlatTop::get_amplitude_at(
    const double x,
    const double y,
    const double z
) const {
    (void)x;

    const double normalized_radius_squared =
        (y * y) / (this->waist_y * this->waist_y) +
        (z * z) / (this->waist_z * this->waist_z);

    if (normalized_radius_squared <= 1.0) {
        return this->amplitude;
    }

    return 0.0;
}


std::vector<double> FlatTop::generate_pulses(
    const std::vector<double>& velocities,
    const std::vector<double>& pulse_centers,
    const std::vector<double>& pulse_amplitudes,
    const std::vector<double>& time_array,
    const double base_level
) const {

    this->validate_pulse_vectors(
        velocities,
        pulse_centers,
        pulse_amplitudes
    );

    this->validate_velocity_vector(velocities);

    std::vector<double> signal;
    signal.reserve(time_array.size());

    for (double time_value : time_array) {
        double signal_value = base_level;

        for (size_t index = 0; index < velocities.size(); ++index) {
            const double pulse_width = this->waist_z / (2.0 * velocities[index]);
            const bool is_inside_pulse =
                std::abs(time_value - pulse_centers[index]) <= pulse_width / 2.0;

            signal_value += pulse_amplitudes[index] * (is_inside_pulse ? 1.0 : 0.0);
        }

        signal.push_back(signal_value);
    }

    return signal;
}


double FlatTop::get_amplitude_at_focus() const {
    const double area = this->waist_y * this->waist_z;

    return std::sqrt(
        4.0 * this->optical_power /
        (
            Constants::pi *
            Constants::vacuum_permitivity *
            Constants::light_speed *
            area
        )
    );
}


double FlatTop::get_normalized_profile_value(
    const double x,
    const double y,
    const double z
) const {
    (void)x;

    const double normalized_radius_squared =
        (y * y) / (this->waist_y * this->waist_y) +
        (z * z) / (this->waist_z * this->waist_z);

    if (normalized_radius_squared <= 1.0) {
        return 1.0;
    }

    return 0.0;
}
