#include "signal_generator.h"


// ----------------------------- Setters and Getters ---------------------------
// -----------------------------------------------------------------------------

void SignalGenerator::add_signal(const std::string &signal_name, const std::vector<double> &signal_data) {
    if (this->data_dict.find(signal_name) != this->data_dict.end())
        throw std::runtime_error("Signal with this name already exists.");

    if (signal_data.size() != this->n_elements)
        throw std::runtime_error("Signal data size does not match the number of elements.");

    this->data_dict[signal_name] = signal_data;
}

void SignalGenerator::create_zero_signal(const std::string &signal_name) {

    if (this->data_dict.find(signal_name) != this->data_dict.end())
        throw std::runtime_error("Signal with this name already exists.");

    this->data_dict[signal_name] = std::vector<double>(this->n_elements, 0.0);
}

std::vector<double> &SignalGenerator::get_signal(const std::string &signal_name) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    return this->data_dict[signal_name];
}





// ----------------------------- Basics Operations -----------------------------
// -----------------------------------------------------------------------------

void SignalGenerator::add_constant(const double constant) {
    for (auto &entry : this->data_dict) {
        if (entry.first == "Time")  // Skip the time signal
            continue;
        this->add_constant_to_signal(entry.first, constant);
    }
}

void SignalGenerator::add_constant_to_signal(const std::string &signal_name, const double constant) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    #pragma omp parallel for
    for (auto &value : this->data_dict[signal_name])
        value += constant;

}

void SignalGenerator::multiply(const double factor) {
    for (auto &entry : this->data_dict) {
        if (entry.first == "Time")  // Skip the time signal
            continue;
        this->multiply_signal(entry.first, factor);
    }
}

void SignalGenerator::multiply_signal(const std::string &signal_name, const double factor) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    #pragma omp parallel for
    for (auto &value : data_dict[signal_name])
        value *= factor;
}

void SignalGenerator::round_signal(const std::string &signal_name) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    #pragma omp parallel for
    for (auto &value : this->data_dict[signal_name])
        value = std::round(value);
}

void SignalGenerator::round() {
    for (auto &entry : this->data_dict) {
        if (entry.first == "Time")  // Skip the time signal
            continue;
        this->round_signal(entry.first);
    }
}


// ----------------------------- Complex Operations ----------------------------
// -----------------------------------------------------------------------------

void SignalGenerator::apply_baseline_restoration(const int window_size) {
    for (auto &entry : this->data_dict)
        if (entry.first != "Time")
            utils::apply_baseline_restoration_to_signal(entry.second, window_size);
}

void SignalGenerator::apply_butterworth_lowpass_filter(const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    for (auto &entry : this->data_dict)
        if (entry.first != "Time")
            utils::apply_butterworth_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);

}

void SignalGenerator::apply_butterworth_lowpass_filter_to_signal(const std::string &signal_name, const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    utils::apply_butterworth_lowpass_filter_to_signal(this->data_dict[signal_name], sampling_rate, cutoff_frequency, order, gain);
}

void SignalGenerator::generate_pulses(const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, const double background_power) {
    for (auto &entry : this->data_dict)
        if (entry.first != "Time")
            utils::generate_pulses_signal(entry.second, widths, centers, coupling_power, this->data_dict["Time"], background_power);

}

void SignalGenerator::generate_pulses_signal(const std::string& signal_name, const std::vector<double> &widths, const std::vector<double> &centers, const std::vector<double> &coupling_power, const double background_power) {

    utils::generate_pulses_signal(this->data_dict[signal_name], widths, centers, coupling_power, this->data_dict["Time"], background_power);

}

void SignalGenerator::apply_bessel_lowpass_filter(const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    for (auto &entry : this->data_dict)
        if (entry.first != "Time")
            utils::apply_bessel_lowpass_filter_to_signal(entry.second, sampling_rate, cutoff_frequency, order, gain);

}

void SignalGenerator::apply_bessel_lowpass_filter_to_signal(const std::string &signal_name, const double sampling_rate, const double cutoff_frequency, const int order, const double gain) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    utils::apply_bessel_lowpass_filter_to_signal(this->data_dict[signal_name], sampling_rate, cutoff_frequency, order, gain);
}



// ----------------------------- Noise Operations ------------------------------
// -----------------------------------------------------------------------------

void SignalGenerator::add_gaussian_noise(const double mean, const double standard_deviation) {
    for (auto &entry : this->data_dict)
        if (entry.first != "Time")
            utils::add_gaussian_noise_to_signal(entry.second, mean, standard_deviation);

}

void SignalGenerator::add_gaussian_noise_to_signal(std::string &signal_name, const double mean, const double standard_deviation) {
    if (this->data_dict.find(signal_name) == this->data_dict.end())
        throw std::runtime_error("Signal with this name does not exist.");

    utils::add_gaussian_noise_to_signal(this->data_dict[signal_name], mean, standard_deviation);
}

void SignalGenerator::apply_poisson_noise_to_signal(const std::string &signal_name) {
    std::vector<double> &signal = this->data_dict[signal_name];

    this->_apply_mixed_poisson_noise_to_signal(signal_name);
}

void SignalGenerator::_apply_mixed_poisson_noise_to_signal(const std::string &signal_name) {
    std::vector<double> &signal = this->data_dict[signal_name];

    if (signal.empty()) {
        throw std::runtime_error("Signal vector is empty.");
    }

    std::default_random_engine random_generator(std::random_device{}());
    constexpr double threshold = 1e6;

    for (size_t i = 0; i < signal.size(); ++i) {
        double value = signal[i];

        if (value < 0.0) {
            throw std::runtime_error("Poisson noise requires non-negative values");
        }

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
    std::vector<double> &signal = this->data_dict[signal_name];

    if (signal.empty()) {
        throw std::runtime_error("Signal vector is empty.");
    }

    std::default_random_engine random_generator(std::random_device{}());

    for (size_t i = 0; i < signal.size(); ++i) {
        if (signal[i] < 0.0)
            throw std::runtime_error("Poisson noise requires non-negative values");

        std::poisson_distribution<int> dist(signal[i]);

        signal[i] = static_cast<double>(dist(random_generator));
    }
}

void SignalGenerator::_apply_poisson_noise_as_gaussian_to_signal(const std::string &signal_name) {
    std::vector<double> &signal = this->data_dict[signal_name];

    if (signal.empty()) {
        throw std::runtime_error("Signal vector is empty.");
    }

    std::default_random_engine random_generator(std::random_device{}());

    for (size_t i = 0; i < signal.size(); ++i) {
        if (signal[i] < 0.0) {
            throw std::runtime_error("Poisson noise requires non-negative values");
        }

        double mean = signal[i];
        double standard_deviation = std::sqrt(signal[i]);
        std::normal_distribution<double> dist(mean, standard_deviation);

        signal[i] = std::round(dist(random_generator));
    }
}

void SignalGenerator::apply_poisson_noise() {
    for (const auto &entry : this->data_dict)
        if (entry.first != "Time")
            this->apply_poisson_noise_to_signal(entry.first);

}





