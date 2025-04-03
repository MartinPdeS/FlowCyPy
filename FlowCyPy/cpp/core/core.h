#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    std::vector<double> widths;
    std::vector<double> centers;
    // Constructor taking a py::array_t<double> by value.
    FlowCyPySim(
        const std::vector<double> &widths,
        const std::vector<double> &centers
    );

    // (Optional) Other public methods can go here.

};