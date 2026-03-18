#include "circuits.h"

void BaseLineRestoration::process(SignalGenerator &signal_generator) {
    double sampling_rate = signal_generator.get_sampling_rate();

    size_t window_size_units = round(this->window_size  / sampling_rate);

    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            signal_generator.apply_baseline_restoration(window_size_units);
}

void ButterworthLowPassFilter::process(SignalGenerator &signal_generator) {
    double sampling_rate = signal_generator.get_sampling_rate();

    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            utils::apply_butterworth_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
}

void BesselLowPassFilter::process(SignalGenerator &signal_generator) {
    double sampling_rate = signal_generator.get_sampling_rate();

    for (auto &entry : signal_generator.data_dict)
        if (entry.first != "Time")
            utils::apply_bessel_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);
}
