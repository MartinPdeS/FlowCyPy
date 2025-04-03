#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
// #include <pybind11/stl.h>
#include "core.cpp"

namespace py = pybind11;


// PYBIND11 MODULE
PYBIND11_MODULE(interface_core, m) {
    m.doc() = "Pybind11 example with no std::vector, only py::array_t<double>";

    py::class_<FlowCyPySim>(m, "FlowCyPySim")
        .def(py::init<const std::vector<double>&>())
        // .def(py::init<const py::array_t<double>&, const py::array_t<double>&, const py::array_t<double>&, const py::array_t<double>&, double>(),
        //      py::arg("widths"),
        //      py::arg("centers"),
        //      py::arg("coupling_power"),
        //      py::arg("time_array"),
        //      py::arg("background_power")
        // )
        // .def("getAcquisition", &FlowCyPySim::getAcquisition, "Sums background power plus Gaussian pulses for each scatterer.")
        ;
}
