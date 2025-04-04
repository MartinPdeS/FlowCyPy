#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    py::array_t<double> widths;
    py::array_t<double> centers;
    py::array_t<double> coupling_power;
    py::array_t<double> time_array;
    double background_power;

    // Constructor taking a py::array_t<double> by value.
    FlowCyPySim() = default;
    FlowCyPySim(
        const py::array_t<double> &widths,
        const py::array_t<double> &centers,
        const py::array_t<double> &coupling_power,
        const py::array_t<double> &time_array,
        const double background_power
    );

    py::array_t<double> get_acquisition();

};