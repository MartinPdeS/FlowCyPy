#include "circuits.h"


std::vector<double> BaseLineRestoration::process(
    const std::vector<double>& signal,
    const double sampling_rate
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    std::vector<double> output_signal(signal);

    int window_size_in_samples = -1;

    if (this->window_size != -1.0) {
        if (std::isnan(sampling_rate) || sampling_rate <= 0.0) {
            throw std::runtime_error(
                "sampling_rate must be strictly positive for finite baseline restoration window."
            );
        }

        window_size_in_samples = static_cast<int>(
            std::llround(this->window_size * sampling_rate)
        );

        if (window_size_in_samples <= 0) {
            throw std::runtime_error(
                "window_size corresponds to fewer than one sample."
            );
        }
    }

    utils::apply_baseline_restoration_to_signal(
        output_signal,
        window_size_in_samples
    );

    return output_signal;
}


std::vector<double> ButterworthLowPassFilter::process(
    const std::vector<double>& signal,
    const double sampling_rate
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    if (sampling_rate <= 0.0 || std::isnan(sampling_rate)) {
        throw std::runtime_error("sampling_rate must be strictly positive.");
    }

    if (this->cutoff_frequency >= 0.5 * sampling_rate) {
        throw std::runtime_error(
            "cutoff_frequency must be strictly smaller than the Nyquist frequency."
        );
    }

    std::vector<double> output_signal(signal);

    utils::apply_butterworth_lowpass_filter_to_signal(
        output_signal,
        sampling_rate,
        this->cutoff_frequency,
        this->order,
        this->gain
    );

    return output_signal;
}


std::vector<double> BesselLowPassFilter::process(
    const std::vector<double>& signal,
    const double sampling_rate
) const {
    if (signal.empty()) {
        throw std::runtime_error("signal vector is empty.");
    }

    if (sampling_rate <= 0.0 || std::isnan(sampling_rate)) {
        throw std::runtime_error("sampling_rate must be strictly positive.");
    }

    if (this->cutoff_frequency >= 0.5 * sampling_rate) {
        throw std::runtime_error(
            "cutoff_frequency must be strictly smaller than the Nyquist frequency."
        );
    }

    std::vector<double> output_signal(signal);

    utils::apply_bessel_lowpass_filter_to_signal(
        output_signal,
        sampling_rate,
        this->cutoff_frequency,
        this->order,
        this->gain
    );

    return output_signal;
}
