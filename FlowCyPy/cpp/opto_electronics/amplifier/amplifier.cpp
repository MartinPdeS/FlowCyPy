#include "amplifier.h"
#include <omp.h>


Amplifier::Amplifier(
    const double gain,
    const double bandwidth,
    const double voltage_noise_density,
    const double current_noise_density,
    const int filter_order,
    const bool debug_mode
)
    : gain(gain),
        bandwidth(bandwidth),
        voltage_noise_density(voltage_noise_density),
        current_noise_density(current_noise_density),
        filter_order(filter_order),
        debug_mode(debug_mode)
{
    if (this->gain < 0.0) {
        throw std::runtime_error("gain must be non negative.");
    }

    if (!std::isnan(this->bandwidth) && this->bandwidth <= 0.0) {
        throw std::runtime_error("bandwidth must be strictly positive when defined.");
    }

    if (this->voltage_noise_density < 0.0) {
        throw std::runtime_error("voltage_noise_density must be non negative.");
    }

    if (this->current_noise_density < 0.0) {
        throw std::runtime_error("current_noise_density must be non negative.");
    }

    if (this->filter_order <= 0) {
        throw std::runtime_error("filter_order must be strictly positive.");
    }

    if (this->debug_mode) {
        std::printf(
            "[Amplifier] Initialized | gain=%g | bandwidth=%g Hz | voltage_noise_density=%g V/sqrt(Hz) | current_noise_density=%g A/sqrt(Hz) | filter_order=%d\n",
            this->gain,
            this->bandwidth,
            this->voltage_noise_density,
            this->current_noise_density,
            this->filter_order
        );
    }
}

double Amplifier::get_rms_noise() const {
    if (std::isnan(this->bandwidth)) {
        return 0.0;
    }

    const double voltage_noise_rms =
        this->voltage_noise_density * std::sqrt(this->bandwidth);

    const double current_noise_rms =
        this->current_noise_density * std::sqrt(this->bandwidth) * this->gain;

    return std::sqrt(
        voltage_noise_rms * voltage_noise_rms +
        current_noise_rms * current_noise_rms
    );
}

std::vector<double> Amplifier::amplify(
    const std::vector<double>& signal,
    const double sampling_rate
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    std::vector<double> output_signal;

    if (std::isnan(this->bandwidth)) {
        output_signal = this->amplify_without_bandwidth(signal);
    }
    else if (std::isnan(sampling_rate)) {
        output_signal = this->amplify_without_bandwidth(signal);
    }
    else {
        output_signal = this->amplify_with_bandwidth(signal, sampling_rate);
    }

    if (
        !std::isnan(this->bandwidth) &&
        (
            this->voltage_noise_density > 0.0 ||
            this->current_noise_density > 0.0
        )
    ) {
        output_signal = this->add_gaussian_noise(
            output_signal,
            0.0,
            this->get_rms_noise()
        );
    }

    return output_signal;
}


std::vector<double> Amplifier::amplify_with_bandwidth(
    const std::vector<double>& signal,
    const double sampling_rate
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    if (std::isnan(this->bandwidth)) {
        throw std::runtime_error(
            "amplify_with_bandwidth requires amplifier bandwidth to be defined."
        );
    }

    if (sampling_rate <= 0.0 || std::isnan(sampling_rate)) {
        throw std::runtime_error("sampling_rate must be strictly positive.");
    }

    if (this->bandwidth >= 0.5 * sampling_rate) {
        throw std::runtime_error(
            "Amplifier bandwidth is too high for the digitizer sampling rate.\n"
            "To simulate the amplifier correctly, the sampling rate must be at least "
            "twice the amplifier bandwidth (Nyquist limit).\n"
            "Otherwise the signal would be distorted by aliasing.\n\n"
            "How to fix this:\n"
            "  • Increase the digitizer sampling rate, or\n"
            "  • Use a lower amplifier bandwidth, or\n"
            "  • Disable bandwidth filtering by setting bandwidth=None.\n"
        );
    }




    std::vector<double> output_signal(signal);

    utils::apply_bessel_lowpass_filter_to_signal(
        output_signal,
        sampling_rate,
        this->bandwidth,
        this->filter_order,
        this->gain
    );

    return output_signal;
}


std::vector<double> Amplifier::amplify_without_bandwidth(
    const std::vector<double>& signal
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    std::vector<double> output_signal(signal.size());

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (this->debug_mode) {
                std::printf(
                    "[Amplifier::amplify_without_bandwidth] using %d OpenMP threads\n",
                    omp_get_num_threads()
                );
            }
        }

        #pragma omp for
        for (long long index = 0; index < static_cast<long long>(signal.size()); ++index) {
            output_signal[index] = signal[index] * this->gain;
        }
    }

    return output_signal;
}


std::vector<double> Amplifier::add_gaussian_noise(
    const std::vector<double>& signal,
    const double mean,
    const double standard_deviation
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    if (standard_deviation < 0.0) {
        throw std::runtime_error("standard_deviation must be non negative.");
    }

    if (standard_deviation == 0.0) {
        return signal;
    }

    std::vector<double> output_signal(signal);

    #pragma omp parallel
    {
        #pragma omp single
        {
            if (this->debug_mode) {
                std::printf(
                    "[Amplifier::add_gaussian_noise] using %d OpenMP threads | mean=%g | std=%g\n",
                    omp_get_num_threads(),
                    mean,
                    standard_deviation
                );
            }
        }

        std::random_device random_device;
        std::mt19937 generator(
            random_device() + static_cast<unsigned int>(omp_get_thread_num())
        );
        std::normal_distribution<double> distribution(mean, standard_deviation);

        #pragma omp for
        for (long long index = 0; index < static_cast<long long>(output_signal.size()); ++index) {
            output_signal[index] += distribution(generator);
        }
    }

    return output_signal;
}
