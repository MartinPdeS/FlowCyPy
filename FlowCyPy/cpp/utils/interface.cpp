#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "utils.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_utils, module) {
    module.doc() = "Utility bindings";

    module.def(
        "butterworth_lowpass_filter",
        &utils::apply_butterworth_lowpass_filter_to_signal,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain")
    );

    module.def(
        "bessel_lowpass_filter",
        &utils::apply_bessel_lowpass_filter_to_signal,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain")
    );

    module.def("baseline_restoration",
        &utils::apply_baseline_restoration_to_signal,
        py::arg("signal"),
        py::arg("window_size"),
        "In-place baseline restoration"
    );

    module.def(
        "generate_pulses",
        &utils::generate_pulses_signal,
        py::arg("signal"),
        py::arg("widths"),
        py::arg("centers"),
        py::arg("coupling_power"),
        py::arg("time"),
        py::arg("background_power"),
        "Sums background power plus Gaussian pulses for each scatterer."
    );


    module.def(
        "add_gaussian_noise",
        &utils::add_gaussian_noise_to_signal,
        py::arg("signal"),
        py::arg("mean"),
        py::arg("standard_deviation"),
        "Adds Gaussian noise in-place to the given output buffer."
    );

    module.def("add_poisson_noise",
        &utils::add_poisson_noise_to_signal,
        py::arg("signal"),
        "Applies Poisson-distributed noise in-place to a non-negative signal buffer."
    );

}
