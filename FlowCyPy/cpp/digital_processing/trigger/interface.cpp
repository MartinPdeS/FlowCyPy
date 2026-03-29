#include <pybind11/pybind11.h>



void register_trigger(pybind11::module& module) {

    pybind11::class_<Trigger>(module, "TRIGGER")
        .def(pybind11::init<>())
        .def_readonly("global_time",
             &Trigger::global_time,
             pybind11::return_value_policy::reference_internal,
             R"pbdoc(
                 Global time vector used for all signal operations.

                 This aligns one-to-one with samples in added signals.
             )pbdoc"
        )
        .def("get_segmented_signal",
             &Trigger::get_segmented_signal,
             pybind11::arg("detector_name"),
             R"pbdoc(
                 Retrieve the signal data for a specific detector.

                 Parameters
                 ----------
                 detector_name : str
                     Name of the signal detector to retrieve.

                 Returns
                 -------
                 numpy.ndarray
                     1D array of signal values for the specified detector.
             )pbdoc"
        )
        .def_readonly("segmented_time",
             &Trigger::time_out,
             R"pbdoc(
                 Time segments corresponding to each detected trigger.

                 This is a 1D array where each entry corresponds to the
                 time stamps of a trigger segment.
             )pbdoc"
        )
        .def_readonly("segment_ids",
             &Trigger::segment_ids_out,
             R"pbdoc(
                 Mapping of sample indices to segment IDs.

                 This is a 1D array where each entry indicates the segment
                 ID for that sample, or -1 if it does not belong to any segment.
             )pbdoc"
        )
        ;
}
