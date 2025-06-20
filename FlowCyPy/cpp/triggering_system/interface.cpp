#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "triggering_system.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_triggering_system, module) {
    module.doc() = R"pbdoc(
        Signal Triggering and Segmentation System.

        Provides an efficient framework for threshold-based and dynamic
        window triggering of signals, with support for debouncing,
        pre/post buffering, and segment extraction.
    )pbdoc";

    // BaseTrigger class
    py::class_<BaseTrigger>(module, "BASETRIGGER")
        .def(py::init<>())
        .def_readwrite("trigger_detector_name", &BaseTrigger::trigger_detector_name,
             R"pbdoc(
                 Name of the trigger detection algorithm used.

                 This is set during initialization and determines the
                 behavior of the trigger detection.
             )pbdoc"
        )
        .def_readwrite("pre_buffer", &BaseTrigger::pre_buffer,
             R"pbdoc(
                 Number of samples to include before each detected trigger.

                 This is used to buffer data before the trigger point.
             )pbdoc"
        )
        .def_readwrite("post_buffer", &BaseTrigger::post_buffer,
             R"pbdoc(
                 Number of samples to include after each detected trigger.

                 This is used to buffer data after the trigger point.
             )pbdoc"
        )
        .def_readwrite("max_triggers", &BaseTrigger::max_triggers,
             R"pbdoc(
                 Maximum number of triggers to record.

                 If set to -1, there is no limit on the number of triggers.
             )pbdoc"
        )
        .def("_cpp_add_time", &BaseTrigger::add_time,
             R"pbdoc(
                Add a global time axis for subsequent signal additions.

                Parameters
                ----------
                time_array : numpy.ndarray
                    1D array of monotonically increasing time stamps.
            )pbdoc"
        )
        .def("_cpp_add_signal",
            &BaseTrigger::add_signal,
            py::arg("detector_name") = "default",
            py::arg("signal_array"),
            R"pbdoc(
                Add a signal trace to be analyzed for triggers.

                Parameters
                ----------
                signal_array : numpy.ndarray
                    1D array of signal values aligned to `global_time`.
            )pbdoc"
        )
        .def("_cpp_get_times",
            &BaseTrigger::get_times_py,
             R"pbdoc(
                 Retrieve time segments for each detected trigger.

                 Returns
                 -------
                 List[numpy.ndarray]
                     One array of time stamps per trigger segment.
             )pbdoc"
        )
        .def("_cpp_get_signals",
            &BaseTrigger::get_signals_py,
             R"pbdoc(
                 Retrieve signal segments corresponding to each trigger.

                 Returns
                 -------
                 List[numpy.ndarray]
                     One array of signal values per trigger segment.
             )pbdoc"
        )
        .def("_cpp_get_segments_ID",
            &BaseTrigger::get_segments_ID_py,
             R"pbdoc(
                 Retrieve a mapping from sample index to segment ID.

                 Returns
                 -------
                 numpy.ndarray
                     1D array of ints where each entry is the segment index
                     (or -1 for no segment).
             )pbdoc"
        )
        .def_readonly("_cpp_global_time",
            &BaseTrigger::global_time,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Global time vector used for all signal operations.

                Aligns one-to-one with samples in added signals.
            )pbdoc"
        )
    ;

    // FixedWindow class
    py::class_<FixedWindow, BaseTrigger>(module, "FIXEDWINDOW")
    .def(py::init<const std::string&, size_t, size_t, int>(),
        py::arg("trigger_detector_name"),
        py::arg("pre_buffer") = 0,
        py::arg("post_buffer") = 0,
        py::arg("max_triggers") = -1,
        R"pbdoc(
            Initialize a FixedWindow trigger detector.

            Parameters
            ----------
            trigger_detector_name : str
                Name of the detection algorithm to apply.
            pre_buffer : int, optional
                Samples to buffer before each detected event. Default = 0.
            post_buffer : int, optional
                Samples to buffer after each detected event. Default = 0.
            max_triggers : int, optional
                Maximum number of triggers to record; -1 for no limit. Default = -1.
        )pbdoc"
    )
    .def("_cpp_run",
        &FixedWindow::run,
        py::arg("threshold"),
        R"pbdoc(
            Execute fixed-window trigger detection.

            Parameters
            ----------
            threshold : float
                Primary threshold above which a trigger is fired.
        )pbdoc"
    )
    ;

    // DynamicWindow class
    py::class_<DynamicWindow, BaseTrigger>(module, "DYNAMICWINDOW")
    .def(py::init<const std::string&, size_t, size_t, int>(),
        py::arg("trigger_detector_name"),
        py::arg("pre_buffer") = 0,
        py::arg("post_buffer") = 0,
        py::arg("max_triggers") = -1,
        R"pbdoc(
            Initialize a FixedWindow trigger detector.

            Parameters
            ----------
            trigger_detector_name : str
                Name of the detection algorithm to apply.
            pre_buffer : int, optional
                Samples to buffer before each detected event. Default = 0.
            post_buffer : int, optional
                Samples to buffer after each detected event. Default = 0.
            max_triggers : int, optional
                Maximum number of triggers to record; -1 for no limit. Default = -1.
        )pbdoc"
    )
    .def("_cpp_run",
        &DynamicWindow::run,
        py::arg("threshold"),
        R"pbdoc(
            Execute dynamic-window trigger detection.

            Parameters
            ----------
            threshold : float
                Primary threshold above which a trigger is fired.
        )pbdoc"
    )
    ;

    // DoubleThreshold class
    py::class_<DoubleThreshold, BaseTrigger>(module, "DOUBLETHRESHOLD")
    .def(py::init<const std::string&, size_t, size_t, int>(),
        py::arg("trigger_detector_name"),
        py::arg("pre_buffer") = 0,
        py::arg("post_buffer") = 0,
        py::arg("max_triggers") = -1,
        R"pbdoc(
            Initialize a FixedWindow trigger detector.

            Parameters
            ----------
            trigger_detector_name : str
                Name of the detection algorithm to apply.
            pre_buffer : int, optional
                Samples to buffer before each detected event. Default = 0.
            post_buffer : int, optional
                Samples to buffer after each detected event. Default = 0.
            max_triggers : int, optional
                Maximum number of triggers to record; -1 for no limit. Default = -1.
        )pbdoc"
    )
    .def("_cpp_run",
        &DoubleThreshold::run,
        py::arg("threshold"),
        py::arg("lower_threshold") = std::nan(""),
        py::arg("debounce_enabled") = true,
        py::arg("min_window_duration") = -1,
        R"pbdoc(
            Execute double-threshold trigger detection with hysteresis.

            Parameters
            ----------
            threshold : float
                Primary threshold above which a trigger is fired.
            lower_threshold : float, optional
                Secondary threshold below which the signal must fall before re-arming.
                Default = NaN (no lower threshold).
            debounce_enabled : bool, optional
                If true, applies debouncing to avoid rapid successive triggers. Default = true.
            min_window_duration : int, optional
                Minimum samples between triggers; -1 to disable. Default = -1.
        )pbdoc"
    )
    ;
}
