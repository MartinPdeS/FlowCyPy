#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    std::vector<double> widths;
    std::vector<double> centers;
    py::array_t<double> coupling_power;
    py::array_t<double> time_array;
    // Constructor taking a py::array_t<double> by value.
    FlowCyPySim(
        const std::vector<double> &widths,
        const std::vector<double> &centers,
        const std::vector<double> &coupling_power,
        const std::vector<double> &time_array
    );

    // (Optional) Other public methods can go here.

};