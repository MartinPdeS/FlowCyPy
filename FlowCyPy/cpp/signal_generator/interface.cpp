#include "signal_generator.h"


namespace py = pybind11;

PYBIND11_MODULE(interface_core, module) {
    module.doc() = "SignalGenerator bindings";

    py::class_<SignalGenerator>(module, "SignalGenerator")
        .def(
            py::init<py::buffer>(),
            py::arg("signal")
        )
        .def(
            "pulse_generation",
            &SignalGenerator::pulse_generation,
            py::arg("widths"),
            py::arg("centers"),
            py::arg("coupling_power"),
            py::arg("time_array"),
            py::arg("background_power"),
            "Sums background power plus Gaussian pulses for each scatterer."
        )

        .def(
            "add_gaussian_noise",
            &SignalGenerator::add_gaussian_noise,
            py::arg("mean"),
            py::arg("standard_deviation"),
            "Adds Gaussian noise in-place to the given output buffer.")

        .def("add_poisson_noise",
            &SignalGenerator::add_poisson_noise,
            "Applies Poisson-distributed noise in-place to a non-negative signal buffer.")

        .def("fft_filtering",
            &SignalGenerator::fft_filtering,
            py::arg("dt"),
            py::arg("cutoff_freq"),
            py::arg("order") = 1,
            "In-place low-pass FFT filter on output array")

            .def("apply_baseline_restoration",
                &SignalGenerator::apply_baseline_restoration,
                py::arg("window_size"),
                "In-place baseline restoration")
            ;
}
