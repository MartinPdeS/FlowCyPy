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



// minimal_function.cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>

namespace py = pybind11;



class FlowCyPySim {
    public:
        std::vector<double> widths;
        std::vector<double> centers;
        std::vector<double> coupling_power;
        std::vector<double> time_array;
        double background_power;

        // Constructor taking a py::array_t<double> by value.
        FlowCyPySim(
            const std::vector<double> &widths,
            const std::vector<double> &centers,
            const std::vector<double> &coupling_power,
            const std::vector<double> &time_array,
            const double background_power
        );

        py::array_t<double> get_acquisition();

};



std::string create_array() {

    // Create a new 2D array with shape (3, 5)
    py::array_t<double> arr({3, 5});

    // Return the shape as a string
    return "Created array with shape: " + std::to_string(arr.shape(0)) +
           " x " + std::to_string(arr.shape(1));
}

PYBIND11_MODULE(interface_core, m) {
    m.doc() = "Pybind11 example with no std::vector, only py::array_t<double>";

    py::class_<FlowCyPySim>(m, "FlowCyPySim")
    .def(
        py::init<const std::vector<double> &, const std::vector<double> &, const std::vector<double>&, const std::vector<double>&, const double>(),
        py::arg("widths"),
        py::arg("centers"),
        py::arg("coupling_power"),
        py::arg("time_array"),
        py::arg("background_power")
    )

    // Uncommenting the following line forces the initialization of NumPy's C API.
    py::module::import("numpy");

    m.def("create_array", &create_array, "A function that creates a 2D array and returns its shape.");
}
