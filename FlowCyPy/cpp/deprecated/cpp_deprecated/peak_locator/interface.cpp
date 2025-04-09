#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "peak_locator.cpp"

namespace py = pybind11;

PYBIND11_MODULE(interface_peak_locator, m) {
    m.doc() = "An overlapping sliding window peak locator implemented in C++ with pybind11. "
              "If window_step is not provided, it defaults to window_size.";
    py::class_<SlidingWindowPeakLocator>(m, "SlidingWindowPeakLocator")
        .def(py::init<int, int, int, int, bool, bool, double>(),
            py::arg("window_size"),
            py::arg("window_step") = -1,
            py::arg("max_number_of_peaks") = 5,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("threshold") = 0.5)
        .def("__call__", &SlidingWindowPeakLocator::operator());

    py::class_<GlobalPeakLocator>(m, "GlobalPeakLocator")
        .def(py::init<int, int, bool, bool, double>(),
            py::arg("max_number_of_peaks") = 1,
            py::arg("padding_value") = -1,
            py::arg("compute_width") = false,
            py::arg("compute_area") = false,
            py::arg("threshold") = 0.5)
        .def("__call__", &GlobalPeakLocator::operator());
}
