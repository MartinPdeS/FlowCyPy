#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "triggering_system.cpp"

namespace py = pybind11;

PYBIND11_MODULE(interface_triggering_system, module) {
    module.doc() = "Module for efficient signal processing and triggered acquisition using C++";

    py::class_<TriggeringSystem>(module, "TriggeringSystem")
        .def(py::init<const std::string&, const std::string&, const double, const double, const int, const int, const int, const bool, const int>(),
            py::arg("scheme"),
            py::arg("trigger_detector_name"),
            py::arg("threshold"),
            py::arg("lower_threshold"),
            py::arg("pre_buffer") = 64,
            py::arg("post_buffer") = 64,
            py::arg("max_triggers") = -1,
            py::arg("debounce_enabled") = true,
            py::arg("min_window_duration") = -1
        )
        .def("add_time", &TriggeringSystem::add_time, "Adds a global time array to the system.")
        .def("add_signal", &TriggeringSystem::add_signal, "Adds a new signal to the system.")
        .def("run", &TriggeringSystem::run, "Executes the triggered acquisition analysis.")
        .def("get_signal_out", &TriggeringSystem::get_signal_out_py, "")
        .def("get_time_out", &TriggeringSystem::get_time_out_py, "")
        .def("get_segment_ID", &TriggeringSystem::get_segment_ID_py, "")
        .def_readonly("global_time", &TriggeringSystem::global_time, "Time vector used for computation")
        .def("run_dynamic", &TriggeringSystem::run_dynamic, "Executes dynamic triggered acquisition analysis.")
        ;
}
