// #include <pybind11/pybind11.h>
// #include "core.h"

// namespace py = pybind11;


// // PYBIND11 MODULE
// PYBIND11_MODULE(interface_core, m) {
//     m.doc() = "Pybind11 example with no py::array_t, only py::array_t<double>";

//     py::class_<FlowCyPySim>(m, "FlowCyPySim")
//     .def(
//         py::init<const py::array_t<double> &, const py::array_t<double> &, const py::array_t<double>&, const py::array_t<double>&, const double>(),
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
#include "core.h"


namespace py = pybind11;


PYBIND11_MODULE(interface_core, m) {
    m.doc() = "Pybind11 example with no py::array_t, only py::array_t<double>";

    py::class_<FlowCyPySim>(m, "FlowCyPySim")
    .def(py::init<>())
    .def(
        py::init<const py::array_t<double> &, const py::array_t<double> &, const py::array_t<double>&, const py::array_t<double>&, const double>(),
        py::arg("widths"),
        py::arg("centers"),
        py::arg("coupling_power"),
        py::arg("time_array"),
        py::arg("background_power")
    )
    ;

    py::module::import("numpy");
}
