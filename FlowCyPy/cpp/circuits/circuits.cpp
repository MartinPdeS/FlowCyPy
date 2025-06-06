#include "circuits.h"

void BaseLineRestoration::process(SignalGenerator &signal_generator) {
    #pragma omp parallel for
    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            signal_generator.apply_baseline_restoration(window_size);
}

ButterworthLowPassFilter::ButterworthLowPassFilter(double sampling_rate, double cutoff_frequency, int order, double gain)
: sampling_rate(sampling_rate), cutoff_frequency(cutoff_frequency), order(order), gain(gain) {}

void ButterworthLowPassFilter::process(SignalGenerator &signal_generator) {
    #pragma omp parallel for
    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            utils::apply_butterworth_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
}

BesselLowPassFilter::BesselLowPassFilter(double sampling_rate, double cutoff_frequency, int order, double gain)
: sampling_rate(sampling_rate), cutoff_frequency(cutoff_frequency), order(order), gain(gain) {}

void BesselLowPassFilter::process(SignalGenerator &signal_generator) {
    #pragma omp parallel for
    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            utils::apply_bessel_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
}

