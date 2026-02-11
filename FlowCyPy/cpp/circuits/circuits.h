#pragma once

#include <vector>
#include "../utils/utils.h"
#include "../signal_generator/signal_generator.h"

class BaseCircuit {
public:
    virtual ~BaseCircuit() = default;

    // Pure virtual function to be implemented by derived classes
    virtual void process(SignalGenerator &signal_generator) = 0;
};


class BaseLineRestoration: public BaseCircuit {
public:
    double window_size;

    BaseLineRestoration() = default;
    BaseLineRestoration(const double _window_size) : window_size(_window_size) {}


    /**
     * @brief Constructs a BaseLineRestoration object with a specified window size.
     * @param window_size The size of the window for baseline restoration. If set to -1, the window is treated as infinite.
     */
    void process(SignalGenerator &signal_generator) override;
};


class ButterworthLowPassFilter: public BaseCircuit {
public:
    double cutoff_frequency;
    int order;
    double gain;

    ButterworthLowPassFilter() = default;

    ButterworthLowPassFilter(double cutoff_frequency, int order, double gain)
    : cutoff_frequency(cutoff_frequency), order(order), gain(gain) {}

    /**
     * @brief Processes the signal generator by applying a Butterworth low-pass filter.
     * This function applies a Butterworth low-pass filter to all signals in the signal generator,
     * except for the "Time" signal.
     * @param signal_generator The SignalGenerator object containing the signals to be processed.
     * @throws std::runtime_error If the signal generator is empty or if the filter parameters are invalid.
     * @note The filter transfer function is defined as:
     *       H(f) = (1 / sqrt(1 + (f/cutoff_frequency)^2))^order,
     *       where @c cutoff_frequency sets the cutoff point and @c order controls the steepness.
     *       The gain parameter adjusts the amplitude of the filtered signal.
     *       The sampling rate is used to determine the frequency response of the filter.
     *       The filter is applied to all signals in the signal generator, except for the "Time" signal.
     *       The filter is applied in-place, modifying the original signals.
     */
    void process(SignalGenerator &signal_generator) override;
};

class BesselLowPassFilter: public BaseCircuit {
public:
    double cutoff_frequency;
    int order;
    double gain;

    BesselLowPassFilter() = default;

    BesselLowPassFilter(double cutoff_frequency, int order, double gain)
    : cutoff_frequency(cutoff_frequency), order(order), gain(gain) {}
    /**
     * @brief Processes the signal generator by applying a Bessel low-pass filter.
     * This function applies a Bessel low-pass filter to all signals in the signal generator,
     * except for the "Time" signal.
     * @param signal_generator The SignalGenerator object containing the signals to be processed.
     * @throws std::runtime_error If the signal generator is empty or if the filter parameters are invalid.
     * @note The filter transfer function is defined as:
     *       H(f) = (1 / sqrt(1 + (f/cutoff_frequency)^2))^order,
     *       where @c cutoff_frequency sets the cutoff point and @c order controls the steepness.
     *       The gain parameter adjusts the amplitude of the filtered signal.
     *       The sampling rate is used to determine the frequency response of the filter.
     *       The filter is applied to all signals in the signal generator, except for the "Time" signal.
     *       The filter is applied in-place, modifying the original signals.
     */
    void process(SignalGenerator &signal_generator) override;
};
