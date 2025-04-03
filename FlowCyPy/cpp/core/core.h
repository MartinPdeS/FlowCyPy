#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class FlowCyPySim {
public:
    // Constructor taking a py::array_t<double> by value.
    FlowCyPySim(py::array_t<double> widths);

    // (Optional) Other public methods can go here.

private:
    py::array_t<double> widths;
};