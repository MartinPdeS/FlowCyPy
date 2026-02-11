#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pint/pint.h>
#include <utils/numpy.h>
#include <memory>

#include "signal_generator.h"









namespace py = pybind11;

PYBIND11_MODULE(signal_generator, module) {
    module.doc() = R"doc(
        A class to generate signals for flow cytometry applications.

        This class extends the SignalGenerator from the FlowCyPy binary interface
        to provide additional functionality specific to flow cytometry signal generation.
    )doc";

    py::object ureg = get_shared_ureg();

    py::class_<SignalGenerator, std::shared_ptr<SignalGenerator>>(module, "SignalGenerator")
        .def(
            py::init(
                [ureg](
                    const size_t sequence_length,
                    const py::object &time_units,
                    const py::object signal_units
                ) {

                    return std::make_shared<SignalGenerator>(sequence_length);
                }
            )
        )
        .def(
            "get_time",
            [ureg](const SignalGenerator& self)
            {
                py::array_t<double> output = vector_move_from_numpy(
                    self.data_dict.find("Time")->second,
                    self.n_elements
                );
                return output * ureg.attr("second");
            }
        )
        .def(
            "add_time",
            [ureg](
                SignalGenerator& self,
                const py::object& time_series
            ) {
                std::vector<double> time_series_c = time_series.attr("to")("second").attr("magnitude").cast<std::vector<double>>();
                std::string time_key = "Time";
                self.data_dict[time_key] = time_series_c;
            }
        )
        .def_readonly(
            "n_elements",
            &SignalGenerator::n_elements,
            "Returns the number of elements in the signal."
        )
        .def(
            py::init<const size_t>(),
            py::arg("n_elements"),
            "Initializes the SignalGenerator with a specified number of elements."
        )
        .def(
            "add_channel",
            &SignalGenerator::add_channel,
            py::arg("channel"),
            py::arg("signal_data"),
            "Adds a signal with the given name and data to the data dictionary."
        )
        .def(
            "get_signal",
            [ureg](
                const SignalGenerator& self,
                const std::string channel
            ) {
                py::array_t<double> output = vector_move_from_numpy(
                    self.data_dict.find(channel)->second,
                    self.n_elements
                );
                return output;
            },
            py::arg("channel"),
            "Retrieves a signal by its name from the data dictionary."
        )
        .def(
            "add_constant",
            &SignalGenerator::add_constant,
            py::arg("constant"),
            "Adds a constant value to all the signal."
        )
        .def(
            "add_constant_to_signal",
            &SignalGenerator::add_constant_to_signal,
            py::arg("channel"),
            py::arg("constant"),
            "Adds a constant value to the specified signal."
        )
        .def("multiply",
            &SignalGenerator::multiply,
            py::arg("factor"),
            "Multiplies all signals by a constant factor."
        )
        .def(
            "multiply_signal",
            &SignalGenerator::multiply_signal,
            py::arg("channel"),
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
            py::arg("channel"),
            "Rounds the specified signal to the nearest integer."
        )
        .def(
            "create_zero_signal",
            &SignalGenerator::create_zero_signal,
            py::arg("channel"),
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
            py::arg("channel"),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Applies a Butterworth low-pass filter to the specified signal."
        )
        .def(
            "generate_pulses",
            &SignalGenerator::generate_pulses,
            py::arg("sigmas"),
            py::arg("centers"),
            py::arg("amplitudes"),
            py::arg("base_level"),
            "Generates pulses in all signals in the data dictionary."
        )
        .def(
            "generate_pulses_to_signal",
            &SignalGenerator::generate_pulses_signal,
            py::arg("channel"),
            py::arg("sigmas"),
            py::arg("centers"),
            py::arg("amplitudes"),
            py::arg("base_level"),
            "Generates pulses in the specified signal."
        )
        .def(
            "apply_gaussian_noise",
            &SignalGenerator::add_gaussian_noise,
            py::arg("mean"),
            py::arg("standard_deviation"),
            "Adds Gaussian noise to all signals in the data dictionary."
        )
        .def(
            "apply_gaussian_noise_to_signal",
            &SignalGenerator::add_gaussian_noise_to_signal,
            py::arg("channel"),
            py::arg("mean"),
            py::arg("standard_deviation"),
            "Adds Gaussian noise to the specified signal."
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
            "apply_bessel_lowpass_filter_to_signal",
            &SignalGenerator::apply_bessel_lowpass_filter_to_signal,
            py::arg("channel"),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            "Applies a Bessel low-pass filter to the specified signal."
        )
        .def(
            "apply_poisson_noise",
            &SignalGenerator::apply_poisson_noise,
            "Adds Poisson noise to all signals in the data dictionary."
        )
        .def(
            "apply_poisson_noise_to_signal",
            &SignalGenerator::apply_poisson_noise_to_signal,
            py::arg("channel"),
            "Adds Poisson noise to the specified signal."
        )
        .def(
            "apply_poisson_noise_through_conversion",
            &SignalGenerator::add_poisson_noise_through_conversion,
            py::arg("channel"),
            py::arg("watt_to_photon")
        )
        .def(
            "get_channels",
            &SignalGenerator::get_channels,
            "Returns a list of all signal names in the data dictionary."
        )
        .def("add_array_to_signal",
            &SignalGenerator::add_array_to_signal,
            py::arg("channel"),
            py::arg("array"))

        .def("convolve_signal_with_gaussian",
            &SignalGenerator::convolve_signal_with_gaussian,
            py::arg("channel"),
            py::arg("sigma")
        )
        .def("add_gamma_trace_to_signal",
            &SignalGenerator::add_gamma_trace,
            py::arg("channel"),
            py::arg("shape"),
            py::arg("scale"),
            py::arg("gaussian_sigma") = 0.0
        )
        ;

}
