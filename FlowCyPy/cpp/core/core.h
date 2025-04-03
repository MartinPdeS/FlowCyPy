#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    std::vector<double> widths;
    // Constructor taking a py::array_t<double> by value.
    FlowCyPySim(
        const std::vector<double> &widths
    );

    // (Optional) Other public methods can go here.

};