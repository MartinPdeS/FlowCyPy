#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "processing.h"
#include "triggering_module.h"

namespace py = pybind11;

PYBIND11_MODULE(Interface, m) {
    m.doc() = "Module for efficient signal processing and triggered acquisition using C++";

    // Expose run_triggering function with full filtering capabilities
    m.def("run_triggering", &run_triggering,
      py::arg("signal_map"),
      py::arg("time_map"),
      py::arg("trigger_detector_name"),
      py::arg("threshold"),
      py::arg("pre_buffer") = 64,
      py::arg("post_buffer") = 64,
      py::arg("max_triggers") = -1,               // Maximum number of trigger events (-1 for unlimited)
      "Executes triggered acquisition analysis with optional baseline restoration and Bessel low-pass filtering. "
      "Detects triggers based on a given threshold, applies pre/post-trigger buffers, and extracts signal segments "
      "from multiple detectors.");

//     // Expose get_trigger_indices function
//     m.def("get_trigger_indices", &get_trigger_indices,
//           py::arg("signal"),
//           py::arg("threshold"),
//           py::arg("pre_buffer") = 64,
//           py::arg("post_buffer") = 64,
//           "Calculate start and end indices for triggered segments, suppressing retriggering during an active buffer period.");



//     // Expose baseline restoration function independently if needed
//     m.def("apply_baseline_restoration", &apply_baseline_restoration,
//           py::arg("signal"),
//           py::arg("window_size"),
//           "Applies baseline restoration by subtracting the rolling minimum value over a specified window size.");

//     // Expose Bessel low-pass filter function for direct use if needed
//     m.def("apply_bessel_lowpass_filter", &apply_bessel_lowpass_filter,
//           py::arg("signal"),
//           py::arg("sampling_rate"),
//           py::arg("cutoff"),
//           py::arg("order"),
//           py::arg("gain") = 1,
//           "Applies an in-place Bessel low-pass filter to the provided signals.");

//     // Expose Bessel low-pass filter function for direct use if needed
//     m.def("apply_butterworth_lowpass_filter", &apply_butterworth_lowpass_filter,
//       py::arg("signal"),
//       py::arg("sampling_rate"),
//       py::arg("cutoff"),
//       py::arg("order"),
//       py::arg("gain") = 1,
//       "Applies an in-place Bessel low-pass filter to the provided signals.");
}
