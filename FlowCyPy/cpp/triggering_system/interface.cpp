#include <pybind11/pybind11.h>
#include "triggering_system.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_triggering_system, module) {
    module.doc() = R"pbdoc(
        Signal Triggering and Segmentation System.

        Provides an efficient framework for threshold-based and dynamic
        window triggering of signals, with support for debouncing,
        pre/post buffering, and segment extraction.
    )pbdoc";

    py::class_<TriggeringSystem>(module, "TRIGERRINGSYSTEM", R"pbdoc(
        Encapsulates logic for detecting and extracting signal segments.

        Supports:
        - Fixed-window or sliding-window threshold detection
        - Hysteresis via a lower threshold
        - Debouncing to suppress rapid retriggers
        - Pre- and post-trigger sample buffering
        - Optional cap on total triggers
        - Dynamic window sizing based on signal characteristics

        Parameters
        ----------
        threshold : float
            Primary threshold above which a trigger is fired.
        lower_threshold : float
            Secondary threshold below which the signal must fall before re-arming.
        pre_buffer : int, optional
            Number of samples to include before each trigger. Default = 64.
        post_buffer : int, optional
            Number of samples to include after each trigger. Default = 64.
        max_triggers : int, optional
            Maximum triggers to record; -1 for unlimited. Default = -1.
        debounce_enabled : bool, optional
            If true, applies debouncing to avoid rapid successive triggers. Default = true.
        min_window_duration : int, optional
            Minimum samples between triggers in dynamic mode; -1 to disable. Default = -1.

        Attributes
        ----------
        global_time : numpy.ndarray
            1D array of time stamps corresponding to all added signals.
    )pbdoc")
        .def(py::init<const std::string&, const size_t, const size_t, const int>(),
             py::arg("trigger_detector_name"),
             py::arg("pre_buffer") = 64,
             py::arg("post_buffer") = 64,
             py::arg("max_triggers") = -1,
             R"pbdoc(
                 Initialize a TriggeringSystem.

                Parameters
                ----------
                trigger_detector_name : str
                    Identifier for the detection algorithm (e.g. 'fixed', 'sliding', 'global').
                pre_buffer : int, optional
                    Number of samples to include before each trigger. Default = 64.
                post_buffer : int, optional
                    Number of samples to include after each trigger. Default = 64.
                max_triggers : int, optional
                    Maximum triggers to record; -1 for unlimited. Default = -1.


                See the class docstring for detailed parameter descriptions.
            )pbdoc")

        .def_readwrite("trigger_detector_name", &TriggeringSystem::trigger_detector_name,
             R"pbdoc(
                 Name of the trigger detection algorithm used.

                 This is set during initialization and determines the
                 behavior of the trigger detection.
             )pbdoc")

        .def_readwrite("pre_buffer", &TriggeringSystem::pre_buffer,
             R"pbdoc(
                 Number of samples to include before each detected trigger.

                 This is used to buffer data before the trigger point.
             )pbdoc")

        .def_readwrite("post_buffer", &TriggeringSystem::post_buffer,
             R"pbdoc(
                 Number of samples to include after each detected trigger.

                 This is used to buffer data after the trigger point.
             )pbdoc")

        .def_readwrite("max_triggers", &TriggeringSystem::max_triggers,
             R"pbdoc(
                 Maximum number of triggers to record.

                 If set to -1, there is no limit on the number of triggers.
             )pbdoc")

        .def("_cpp_add_time", &TriggeringSystem::add_time,
             R"pbdoc(
                Add a global time axis for subsequent signal additions.

                Parameters
                ----------
                time_array : numpy.ndarray
                    1D array of monotonically increasing time stamps.
            )pbdoc")

        .def("_cpp_add_signal", &TriggeringSystem::add_signal,
             R"pbdoc(
                Add a signal trace to be analyzed for triggers.

                Parameters
                ----------
                signal_array : numpy.ndarray
                    1D array of signal values aligned to `global_time`.
            )pbdoc")

        .def("_cpp_run", &TriggeringSystem::run,
            py::arg("algorithm"),
            py::arg("threshold"),
            py::arg("lower_threshold"),
            py::arg("debounce_enabled"),
            py::arg("min_window_duration"),
             R"pbdoc(
                Execute the configured trigger algorithm.

                Parameters
                ----------
                algorithm : str
                    Which algorithm to use (must match `trigger_detector_name`).
                threshold : float
                    Primary threshold above which a trigger is fired.
                lower_threshold : float
                    Secondary threshold below which the signal must fall before re-arming.
                debounce_enabled : bool, optional
                    If true, applies debouncing to avoid rapid successive triggers. Default = true.
                min_window_duration : int, optional
                    Minimum samples between triggers in dynamic mode; -1 to disable. Default = -1.

             )pbdoc")

        .def("_cpp_run_dynamic",
            &TriggeringSystem::run_dynamic,
             R"pbdoc(
                 Execute a dynamic-window trigger analysis.

                 The window size may expand or contract based on signal behavior
                 and `min_window_duration`.
             )pbdoc")

        .def("_cpp_get_times",
            &TriggeringSystem::get_times_py,
             R"pbdoc(
                 Retrieve time segments for each detected trigger.

                 Returns
                 -------
                 List[numpy.ndarray]
                     One array of time stamps per trigger segment.
             )pbdoc")

        .def("_cpp_get_signals",
            &TriggeringSystem::get_signals_py,
             R"pbdoc(
                 Retrieve signal segments corresponding to each trigger.

                 Returns
                 -------
                 List[numpy.ndarray]
                     One array of signal values per trigger segment.
             )pbdoc")

        .def("_cpp_get_segments_ID",
            &TriggeringSystem::get_segments_ID_py,
             R"pbdoc(
                 Retrieve a mapping from sample index to segment ID.

                 Returns
                 -------
                 numpy.ndarray
                     1D array of ints where each entry is the segment index
                     (or -1 for no segment).
             )pbdoc")

        .def_readonly("_cpp_global_time",
            &TriggeringSystem::global_time,
            py::return_value_policy::reference_internal,
            R"pbdoc(
                Global time vector used for all signal operations.

                Aligns one-to-one with samples in added signals.
            )pbdoc")
    ;
}
