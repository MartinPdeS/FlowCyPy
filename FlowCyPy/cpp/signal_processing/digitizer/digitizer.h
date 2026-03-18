#include <pybind11/pybind11.h>
#include <vector>
#include <string>
#include <cmath>      // for std::isnan


class Digitizer {
public:
    double bandwidth;
    double sampling_rate;
    size_t bit_depth;
    double min_voltage;
    double max_voltage;

    Digitizer(double sampling_rate, double threshold)
        : sampling_rate_(sampling_rate), threshold_(threshold) {}


    void clip_signal(std::vector<double>& signal) {
        for (auto& sample : signal) {
            if (sample < min_voltage)
                sample = min_voltage;
            else if (sample > max_voltage)
                sample = max_voltage;
        }
    }

    std::pair<double, double> get_min_max(const std::vector<double>& signal) {
        double min_val = std::numeric_limits<double>::infinity();
        double max_val = -std::numeric_limits<double>::infinity();
        for (const auto& sample : signal) {
            if (std::isnan(sample)) continue; // Skip NaN values
            if (sample < min_val) min_val = sample;
            if (sample > max_val) max_val = sample;
        }
        return {min_val, max_val};
    }

    void capture_signal(const std::vector<double>& signal) {

    }
};
