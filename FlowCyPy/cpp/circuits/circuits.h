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
    int window_size; // Size of the window for baseline restoration

    BaseLineRestoration() = default;

    void process(SignalGenerator &signal_generator) override;
};


class ButterworthLowPassFilter: public BaseCircuit {
public:
    double sampling_rate;
    double cutoff_frequency;
    int order;
    double gain;

    ButterworthLowPassFilter() = default;

    ButterworthLowPassFilter(double sampling_rate, double cutoff_frequency, int order, double gain);

    void process(SignalGenerator &signal_generator) override;
};

class BesselLowPassFilter: public BaseCircuit {
public:
    double sampling_rate;
    double cutoff_frequency;
    int order;
    double gain;

    BesselLowPassFilter() = default;

    BesselLowPassFilter(double sampling_rate, double cutoff_frequency, int order, double gain);

    void process(SignalGenerator &signal_generator) override;
};
