#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "signal_generator.h"

namespace py = pybind11;

PYBIND11_MODULE(interface_signal_generator, module) {
    module.doc() = "SignalGenerator bindings";


    py::class_<SignalGenerator>(module, "SignalGenerator")
        .def(
            py::init<const size_t>(),
            py::arg("n_elements"),
            "Initializes the SignalGenerator with a specified number of elements."
        )
        .def(
            "add_signal",
            &SignalGenerator::add_signal,
            py::arg("signal_name"),
            py::arg("signal_data"),
            "Adds a signal with the given name and data to the data dictionary."
        )
        .def(
            "get_signal",
            &SignalGenerator::get_signal,
            py::arg("signal_name"),
            "Retrieves a signal by its name from the data dictionary."
        )
        .def(
            "add_constant",
            &SignalGenerator::add_constant,
            py::arg("constant"),
            "Adds a constant value to all the signal."
        )
        .def("multiply",
            &SignalGenerator::multiply,
            py::arg("factor"),
            "Multiplies all signals by a constant factor."
        )
        .def(
            "multiply_signal",
            &SignalGenerator::multiply_signal,
            py::arg("signal_name"),
            py::arg("factor"),
            "Multiplies the specified signal by a constant factor."
        )
        .def(
            "round",
            &SignalGenerator::round,
            "Rounds all signals to the nearest integer."
        )
        .def(
            "round_signal",
            &SignalGenerator::round_signal,
            py::arg("signal_name"),
            "Rounds the specified signal to the nearest integer."
        )
        .def(
            "create_zero_signal",
            &SignalGenerator::create_zero_signal,
            py::arg("signal_name"),
            "Creates a zero signal with the given name."
        )
        .def(
            "apply_baseline_restoration",
            &SignalGenerator::apply_baseline_restoration,
            py::arg("window_size"),
            "Applies baseline restoration to all signals in the data dictionary."
        )
        .def(
            "apply_butterworth_lowpass_filter",
            &SignalGenerator::apply_butterworth_lowpass_filter,
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Applies a Butterworth low-pass filter to all signals in the data dictionary."
        )
        .def(
            "apply_butterworth_lowpass_filter_to_signal",
            &SignalGenerator::apply_butterworth_lowpass_filter_to_signal,
            py::arg("signal_name"),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Applies a Butterworth low-pass filter to all signals in the data dictionary."
        )
        .def(
            "generate_pulses",
            &SignalGenerator::generate_pulses,
            py::arg("widths"),
            py::arg("centers"),
            py::arg("coupling_power"),
            py::arg("background_power"),
            "Generates pulses in all signals in the data dictionary."
        )
        .def(
            "generate_pulses_signal",
            &SignalGenerator::generate_pulses_signal,
            py::arg("signal_name"),
            py::arg("widths"),
            py::arg("centers"),
            py::arg("coupling_power"),
            py::arg("background_power"),
            "Generates pulses in all signals in the data dictionary."
        )
        .def(
            "add_gaussian_noise",
            &SignalGenerator::add_gaussian_noise,
            py::arg("mean"),
            py::arg("standard_deviation"),
            "Adds Gaussian noise to all signals in the data dictionary."
        )
        .def(
            "add_gaussian_noise_to_signal",
            &SignalGenerator::add_gaussian_noise_to_signal,
            py::arg("signal_name"),
            py::arg("mean"),
            py::arg("standard_deviation"),
            "Adds Gaussian noise to all signals in the data dictionary."
        )
        .def(
            "apply_bessel_lowpass_filter",
            &SignalGenerator::apply_bessel_lowpass_filter,
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Applies a Bessel low-pass filter to all signals in the data dictionary."
        )
        .def(
            "apply_poisson_noise",
            &SignalGenerator::apply_poisson_noise,
            "Adds Poisson noise to all signals in the data dictionary."
        )
        .def(
            "apply_poisson_noise_to_signal",
            &SignalGenerator::apply_poisson_noise_to_signal,
            py::arg("signal_name"),
            "Adds Poisson noise to the specified signal."
        )
        ;

}
