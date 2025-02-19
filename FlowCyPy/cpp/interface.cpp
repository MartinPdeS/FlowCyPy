#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "processing.cpp"
#include "triggering_module.cpp"

PYBIND11_MODULE(Interface, m) {
      m.doc() = "Module for calculating trigger indices using C++ for efficiency";
      m.def("get_trigger_indices", &get_trigger_indices,
            py::arg("signal"),
            py::arg("threshold"),
            py::arg("pre_buffer") = 64,
            py::arg("post_buffer") = 64,
            "Calculate start and end indices for triggered segments, suppressing retriggering during an active buffer period.");


      m.def("run_triggering", &run_triggering,
            py::arg("signal_map"),
            py::arg("time_map"),
            py::arg("trigger_detector_name"),
            py::arg("threshold"),
            py::arg("pre_buffer") = 64,
            py::arg("post_buffer") = 64,
            py::arg("max_triggers") = -1,
            "Extract triggered segments and return NumPy arrays.");
}

