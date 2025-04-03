// #include <pybind11/pybind11.h>
// #include "core.h"

// namespace py = pybind11;


// // PYBIND11 MODULE
// PYBIND11_MODULE(interface_core, m) {
//     m.doc() = "Pybind11 example with no std::vector, only py::array_t<double>";

//     py::class_<FlowCyPySim>(m, "FlowCyPySim")
//     .def(
//         py::init<const std::vector<double> &, const std::vector<double> &, const std::vector<double>&, const std::vector<double>&, const double>(),
//         py::arg("widths"),
//         py::arg("centers"),
//         py::arg("coupling_power"),
//         py::arg("time_array"),
//         py::arg("background_power")
//     )
//     .def("get_acquisition", &FlowCyPySim::get_acquisition, "Sums background power plus Gaussian pulses for each scatterer.")
//     ;
// }



// minimal.cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>

namespace py = pybind11;

class FlowCyPySim {
public:
    FlowCyPySim() = default;

    // This method creates a new 2D array.
    void get_acquisition() {
        // Ensure we hold the GIL.
        py::gil_scoped_acquire gil;
        // Create a new 2D py::array_t with shape (3, 5).
        py::array_t<double> arr({3, 5});
        // Print out the shape to verify.
        std::cout << "Created array with shape: "
                  << arr.shape(0) << " x " << arr.shape(1) << std::endl;
    }
};

PYBIND11_MODULE(minimal, m) {
    m.doc() = "Minimal reproduction module for py::array_t segfault issue";

    // Note: Not calling py::module::import("numpy") here may lead to a segfault on macOS.
    // Uncommenting the following line forces the NumPy C API initialization:
    // py::module::import("numpy");

    py::class_<FlowCyPySim>(m, "FlowCyPySim")
        .def(py::init<>())
        .def("get_acquisition", &FlowCyPySim::get_acquisition);
}