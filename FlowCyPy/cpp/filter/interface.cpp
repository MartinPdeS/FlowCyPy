#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "filter.cpp"

namespace py = pybind11;

PYBIND11_MODULE(interface_filter, module) {
    module.doc() = "Module for efficient signal processing and triggered acquisition using C++";

    // Expose Bessel low-pass filter function for direct use if needed
    module.def("apply_bessel_lowpass_filter", &apply_bessel_lowpass_filter_py,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff"),
        py::arg("order"),
        py::arg("gain") = 1,
        "Applies an in-place Bessel low-pass filter to the provided signals.");

    // Expose Bessel low-pass filter function for direct use if needed
    module.def("apply_butterworth_lowpass_filter", &apply_butterworth_lowpass_filter_py,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff"),
        py::arg("order"),
        py::arg("gain") = 1,
        "Applies an in-place Bessel low-pass filter to the provided signals.");

    // Expose baseline restoration function independently if needed
    module.def("apply_baseline_restoration", &apply_baseline_restoration,
        py::arg("signal"),
        py::arg("window_size"),
        "Applies baseline restoration by subtracting the rolling minimum value over a specified window size.");
}