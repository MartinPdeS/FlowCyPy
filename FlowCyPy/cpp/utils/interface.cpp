#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "utils.cpp"


namespace py = pybind11;

PYBIND11_MODULE(Interface, module) {

    module.doc() = "Module for in-place signal processing operations using C++ and pybind11";

    module.def("fft_filter", &fft_filter,
        "Apply FFT-based low-pass filter to emulate amplifier bandwidth",
        py::arg("input"),
        py::arg("dt"),
        py::arg("fc"),
        py::arg("order")
    );

    module.def("add_gaussian_noise", &add_gaussian_noise,
          py::arg("signal"),
          py::arg("mean") = 0.0,
          py::arg("std_dev") = 1.0,
          "Adds Gaussian noise (with specified mean and standard deviation) to the input signal in-place.");
}
