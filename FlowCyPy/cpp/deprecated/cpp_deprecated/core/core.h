#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    std::vector<double> widths;
    std::vector<double> centers;
    std::vector<double> coupling_power;
    std::vector<double> time_array;
    double background_power;

    // Constructor taking a std::vector<double> by value.
    FlowCyPySim() = default;
    FlowCyPySim(
        const std::vector<double> &widths,
        const std::vector<double> &centers,
        const std::vector<double> &coupling_power,
        const std::vector<double> &time_array,
        const double background_power
    );

    std::vector<double> get_acquisition();

};