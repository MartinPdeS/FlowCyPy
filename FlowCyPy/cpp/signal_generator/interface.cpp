#include "signal_generator.h"


namespace py = pybind11;

PYBIND11_MODULE(interface_signal_generator, module) {
    module.doc() = "SignalGenerator bindings";

    module.def(
        "butterworth_lowpass_filter",
        &butterworth_lowpass_filter,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain")
    );

    module.def(
        "apply_bessel_lowpass_filter",
        &apply_bessel_lowpass_filter_to_signal,
        py::arg("signal"),
        py::arg("sampling_rate"),
        py::arg("cutoff_frequency"),
        py::arg("order"),
        py::arg("gain")
    );

    module.def("baseline_restoration",
        &apply_baseline_restoration_to_signal,
        py::arg("signal"),
        py::arg("window_size"),
        "In-place baseline restoration"
    );

    module.def(
        "generate_pulses",
        &generate_pulses,
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
        &add_gaussian_noise_to_signal,
        py::arg("signal"),
        py::arg("mean"),
        py::arg("standard_deviation"),
        "Adds Gaussian noise in-place to the given output buffer."
    );

    module.def("add_poisson_noise",
        &add_poisson_noise_to_signal,
        py::arg("signal"),
        "Applies Poisson-distributed noise in-place to a non-negative signal buffer."
    );

}
