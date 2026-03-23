#include <memory>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <pint/pint.h>

#include "signal_generator.h"


namespace py = pybind11;


PYBIND11_MODULE(signal_generator, module) {
    module.doc() = R"doc(
        Signal generator backend for FlowCyPy.

        This module exposes a C++ class that stores multiple named channels on a shared
        time axis and provides utilities for synthetic signal generation, filtering,
        noise injection, FFT based Gaussian convolution, and pulse synthesis.
        )doc";

    py::object ureg = get_shared_ureg();

    py::class_<SignalGenerator, std::shared_ptr<SignalGenerator>>(module, "SignalGenerator",
            R"doc(
                Container and operations for synthetic channels defined on a shared time axis.

                Notes
                -----
                This backend stores raw `double` values internally.
                The Python binding accepts and returns Pint quantities for time and power related
                methods where appropriate.
            )doc"
        )
        .def(
            py::init<size_t>(),
            py::arg("n_elements"),
            R"doc(
                Initialize a signal generator with a fixed number of samples.

                Parameters
                ----------
                n_elements : int
                    Number of samples for every stored channel.
            )doc"
        )
        .def(
            "set_seed",
            &SignalGenerator::set_seed,
            py::arg("seed"),
            R"doc(
                Seed the internal random generator.

                Parameters
                ----------
                seed : int
                    Deterministic seed used by the noise generators.
            )doc"
        )
        .def_property_readonly(
            "n_elements",
            &SignalGenerator::get_number_of_elements,
            R"doc(
                Number of samples stored in every channel.
            )doc"
        )
        .def(
            "has_channel",
            &SignalGenerator::has_channel,
            py::arg("channel"),
            R"doc(
                Return whether a channel exists.
            )doc"
        )
        .def(
            "has_time_channel",
            &SignalGenerator::has_time_channel,
            R"doc(
                Return whether the shared time channel exists.
            )doc"
        )
        .def(
            "get_channel_names",
            &SignalGenerator::get_channel_names,
            R"doc(
                Return the names of all stored channels except the time channel.
            )doc"
        )

        .def(
            "set_time_channel",
            [](SignalGenerator& self, const py::object& time_values) {
                self.set_time_channel(
                    time_values.attr("to")("second").attr("magnitude").cast<std::vector<double>>()
                );
            },
            py::arg("time_values"),
            R"doc(
                Set the shared time channel.

                Parameters
                ----------
                time_values : pint.Quantity
                    One dimensional quantity array convertible to seconds.
            )doc"
        )
        .def(
            "get_time_channel",
            [ureg](const SignalGenerator& self) {
                const std::vector<double>& time_channel = self.get_time_channel_const();

                py::array_t<double> output(time_channel.size());
                auto output_view = output.mutable_unchecked<1>();

                for (size_t index = 0; index < time_channel.size(); ++index) {
                    output_view(index) = time_channel[index];
                }

                return output * ureg.attr("second");
            },
            R"doc(
                Return the shared time channel as a Pint quantity in seconds.
            )doc"
        )
        .def(
            "get_time_step",
            [ureg](const SignalGenerator& self) {
                return py::cast(self.get_time_step()) * ureg.attr("second");
            },
            R"doc(
                Return the sampling period from the first two time samples.
            )doc"
        )
        .def(
            "get_sampling_rate",
            [ureg](const SignalGenerator& self) {
                return py::cast(self.get_sampling_rate()) * ureg.attr("hertz");
            },
            R"doc(
                Return the sampling rate computed as `1 / dt`.
            )doc"
        )
        .def(
            "add_channel",
            [](SignalGenerator& self, const std::string& channel, const py::object& channel_data) {
                self.add_channel(
                    channel,
                    channel_data.attr("to")("watt").attr("magnitude").cast<std::vector<double>>()
                );
            },
            py::arg("channel"),
            py::arg("channel_data"),
            R"doc(
                Add a new channel from a Pint quantity array convertible to watts.

                Parameters
                ----------
                channel : str
                    Channel name.
                channel_data : pint.Quantity
                    One dimensional quantity array convertible to watts.
            )doc"
        )
        .def(
            "create_channel",
            [ureg](SignalGenerator& self, const std::string& channel, const py::object& constant_value) {
                self.create_channel(
                    channel,
                    constant_value.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("channel"),
            py::arg("constant_value") = py::float_(0.0) * ureg.attr("watt"),
            R"doc(
                Create a new channel initialized with a constant value.

                Parameters
                ----------
                channel : str
                    Channel name.
                constant_value : pint.Quantity, default = 0 watt
                    Constant fill value convertible to watts.
            )doc"
        )
        .def(
            "create_zero_channel",
            &SignalGenerator::create_zero_channel,
            py::arg("channel"),
            R"doc(
                Create a new channel initialized with zeros.
            )doc"
        )
        .def(
            "get_channel",
            [ureg](const SignalGenerator& self, const std::string& channel) {
                const std::vector<double>& channel_values = self.get_channel_const(channel);

                py::array_t<double> output(channel_values.size());
                auto output_view = output.mutable_unchecked<1>();

                for (size_t index = 0; index < channel_values.size(); ++index) {
                    output_view(index) = channel_values[index];
                }

                return output;
            },
            py::arg("channel"),
            R"doc(
                Return a channel as a Pint quantity in watts.
            )doc"
        )

        .def(
            "add_constant",
            [](SignalGenerator& self, const py::object& constant_value) {
                self.add_constant(
                    constant_value.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("constant_value"),
            R"doc(
                Add a constant value to all non time channels.

                Parameters
                ----------
                constant_value : pint.Quantity
                    Scalar quantity convertible to watts.
            )doc"
        )
        .def(
            "add_constant_to_channel",
            [](SignalGenerator& self, const std::string& channel, const py::object& constant_value) {
                self.add_constant_to_channel(
                    channel,
                    constant_value.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("channel"),
            py::arg("constant_value"),
            R"doc(
                Add a constant value to one channel.

                Parameters
                ----------
                channel : str
                    Channel name.
                constant_value : pint.Quantity
                    Scalar quantity convertible to watts.
            )doc"
        )
        .def(
            "multiply",
            &SignalGenerator::multiply,
            py::arg("factor"),
            R"doc(
                Multiply all non time channels by a scalar factor.
            )doc"
        )
        .def(
            "multiply_channel",
            &SignalGenerator::multiply_channel,
            py::arg("channel"),
            py::arg("factor"),
            R"doc(
                Multiply one channel by a scalar factor.
            )doc"
        )
        .def(
            "round",
            &SignalGenerator::round,
            R"doc(
                Round all non time channels to the nearest integer.
            )doc"
        )
        .def(
            "round_channel",
            &SignalGenerator::round_channel,
            py::arg("channel"),
            R"doc(
                Round one channel to the nearest integer.
            )doc"
        )
        .def(
            "add_array_to_channel",
            [](SignalGenerator& self, const std::string& channel, const py::object& added_array) {
                self.add_array_to_channel(
                    channel,
                    added_array.attr("to")("watt").attr("magnitude").cast<std::vector<double>>()
                );
            },
            py::arg("channel"),
            py::arg("added_array"),
            R"doc(
                Add a Pint quantity array to a channel element wise.

                Parameters
                ----------
                channel : str
                    Channel name.
                added_array : pint.Quantity
                    One dimensional quantity array convertible to watts.
            )doc"
        )
        .def(
            "apply_baseline_restoration",
            &SignalGenerator::apply_baseline_restoration,
            py::arg("window_size"),
            R"doc(
                Apply baseline restoration to all non time channels.
            )doc"
        )
        .def(
            "apply_butterworth_lowpass_filter",
            [](
                SignalGenerator& self,
                const py::object& sampling_rate,
                const py::object& cutoff_frequency,
                int order,
                double gain
            ) {
                self.apply_butterworth_lowpass_filter(
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>(),
                    cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>(),
                    order,
                    gain
                );
            },
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"doc(
                Apply a Butterworth low pass filter to all non time channels.

                Parameters
                ----------
                sampling_rate : pint.Quantity
                    Sampling rate convertible to hertz.
                cutoff_frequency : pint.Quantity
                    Cutoff frequency convertible to hertz.
                order : int
                    Filter order.
                gain : float
                    Gain applied after filtering.
            )doc"
        )
        .def(
            "apply_butterworth_lowpass_filter_to_channel",
            [](
                SignalGenerator& self,
                const std::string& channel,
                const py::object& sampling_rate,
                const py::object& cutoff_frequency,
                int order,
                double gain
            ) {
                self.apply_butterworth_lowpass_filter_to_channel(
                    channel,
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>(),
                    cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>(),
                    order,
                    gain
                );
            },
            py::arg("channel"),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"doc(
                Apply a Butterworth low pass filter to one channel.
            )doc"
        )
        .def(
            "apply_bessel_lowpass_filter",
            [](
                SignalGenerator& self,
                const py::object& sampling_rate,
                const py::object& cutoff_frequency,
                int order,
                double gain
            ) {
                self.apply_bessel_lowpass_filter(
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>(),
                    cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>(),
                    order,
                    gain
                );
            },
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"doc(
                Apply a Bessel low pass filter to all non time channels.
            )doc"
        )
        .def(
            "apply_bessel_lowpass_filter_to_channel",
            [](
                SignalGenerator& self,
                const std::string& channel,
                const py::object& sampling_rate,
                const py::object& cutoff_frequency,
                int order,
                double gain
            ) {
                self.apply_bessel_lowpass_filter_to_channel(
                    channel,
                    sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>(),
                    cutoff_frequency.attr("to")("hertz").attr("magnitude").cast<double>(),
                    order,
                    gain
                );
            },
            py::arg("channel"),
            py::arg("sampling_rate"),
            py::arg("cutoff_frequency"),
            py::arg("order"),
            py::arg("gain"),
            R"doc(
                Apply a Bessel low pass filter to one channel.
            )doc"
        )
        .def(
            "generate_pulses",
            [](
                SignalGenerator& self,
                const py::object& sigmas,
                const py::object& centers,
                const py::object& coupling_power,
                const py::object& background_power
            ) {
                self.generate_pulses(
                    sigmas.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    centers.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    coupling_power.attr("to")("watt").attr("magnitude").cast<std::vector<double>>(),
                    background_power.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("sigmas"),
            py::arg("centers"),
            py::arg("coupling_power"),
            py::arg("background_power"),
            R"doc(
                Generate Gaussian pulses in all non time channels.

                Parameters
                ----------
                sigmas : pint.Quantity
                    One dimensional quantity array convertible to seconds.
                centers : pint.Quantity
                    One dimensional quantity array convertible to seconds.
                coupling_power : pint.Quantity
                    One dimensional quantity array convertible to watts.
                background_power : pint.Quantity
                    Scalar quantity convertible to watts.
            )doc"
        )
        .def(
            "generate_pulses_to_channel",
            [](
                SignalGenerator& self,
                const std::string& channel,
                const py::object& sigmas,
                const py::object& centers,
                const py::object& coupling_power,
                const py::object& background_power
            ) {
                self.generate_pulses_to_channel(
                    channel,
                    sigmas.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    centers.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    coupling_power.attr("to")("watt").attr("magnitude").cast<std::vector<double>>(),
                    background_power.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("channel"),
            py::arg("sigmas"),
            py::arg("centers"),
            py::arg("coupling_power"),
            py::arg("background_power"),
            R"doc(
                Generate Gaussian pulses in one channel.
            )doc"
        )
        .def(
            "add_gaussian_noise",
            [](SignalGenerator& self, const py::object& mean, const py::object& standard_deviation) {
                self.add_gaussian_noise(
                    mean.attr("to")("watt").attr("magnitude").cast<double>(),
                    standard_deviation.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("mean"),
            py::arg("standard_deviation"),
            R"doc(
                Add Gaussian noise to all non time channels.

                Parameters
                ----------
                mean : pint.Quantity
                    Scalar quantity convertible to watts.
                standard_deviation : pint.Quantity
                    Scalar quantity convertible to watts.
            )doc"
        )
        .def(
            "add_gaussian_noise_to_channel",
            [](SignalGenerator& self, const std::string& channel, const py::object& mean, const py::object& standard_deviation) {
                self.add_gaussian_noise_to_channel(
                    channel,
                    mean.attr("to")("watt").attr("magnitude").cast<double>(),
                    standard_deviation.attr("to")("watt").attr("magnitude").cast<double>()
                );
            },
            py::arg("channel"),
            py::arg("mean"),
            py::arg("standard_deviation"),
            R"doc(
                Add Gaussian noise to one channel.
            )doc"
        )
        .def(
            "apply_poisson_noise",
            &SignalGenerator::apply_poisson_noise,
            R"doc(
                Apply Poisson noise to all non time channels.
            )doc"
        )
        .def(
            "apply_poisson_noise_to_channel",
            &SignalGenerator::apply_poisson_noise_to_channel,
            py::arg("channel"),
            R"doc(
                Apply Poisson noise to one channel.
            )doc"
        )
        .def(
            "apply_poisson_noise_through_conversion",
            &SignalGenerator::apply_poisson_noise_through_conversion,
            py::arg("channel"),
            py::arg("watt_to_photon"),
            R"doc(
                Apply Poisson noise after scaling a channel by a positive watt to photon conversion factor.
            )doc"
        )
        .def(
            "convolve_channel_with_gaussian",
            [](SignalGenerator& self, const std::string& channel, const py::object& sigma) {
                self.convolve_channel_with_gaussian(
                    channel,
                    sigma.attr("to")("second").attr("magnitude").cast<double>()
                );
            },
            py::arg("channel"),
            py::arg("sigma"),
            R"doc(
                Convolve a channel with a Gaussian kernel.

                Parameters
                ----------
                channel : str
                    Channel name.
                sigma : pint.Quantity
                    Gaussian sigma convertible to seconds.
            )doc"
        )
        .def(
            "add_gamma_trace_to_channel",
            [ureg](
                SignalGenerator& self,
                const std::string& channel,
                double shape,
                double scale,
                const py::object& gaussian_sigma
            ) {
                std::vector<double> gamma_trace = self.add_gamma_trace_to_channel(
                    channel,
                    shape,
                    scale,
                    gaussian_sigma.attr("to")("second").attr("magnitude").cast<double>()
                );

                py::array_t<double> output(gamma_trace.size());
                auto output_view = output.mutable_unchecked<1>();

                for (size_t index = 0; index < gamma_trace.size(); ++index) {
                    output_view(index) = gamma_trace[index];
                }

                return output * ureg.attr("watt");
            },
            py::arg("channel"),
            py::arg("shape"),
            py::arg("scale"),
            py::arg("gaussian_sigma") = py::float_(0.0) * ureg.attr("second"),
            R"doc(
                Generate a gamma trace, optionally convolve it with a Gaussian kernel, add it to a channel, and return it.

                Parameters
                ----------
                channel : str
                    Target channel name.
                shape : float
                    Positive gamma shape parameter.
                scale : float
                    Positive gamma scale parameter.
                gaussian_sigma : pint.Quantity, default = 0 second
                    Gaussian convolution sigma convertible to seconds.

                Returns
                -------
                pint.Quantity
                    Generated trace returned in watts.
            )doc"
        )
        .def(
            "get_gamma_trace",
            [ureg](
                SignalGenerator& self,
                double shape,
                double scale,
                const py::object& gaussian_sigma
            ) {
                std::vector<double> gamma_trace = self.get_gamma_trace(
                    shape,
                    scale,
                    gaussian_sigma.attr("to")("second").attr("magnitude").cast<double>()
                );

                py::array_t<double> output(gamma_trace.size());
                auto output_view = output.mutable_unchecked<1>();

                for (size_t index = 0; index < gamma_trace.size(); ++index) {
                    output_view(index) = gamma_trace[index];
                }

                return output;
            },
            py::arg("shape"),
            py::arg("scale"),
            py::arg("gaussian_sigma") = py::float_(0.0) * ureg.attr("second"),
            R"doc(
                Generate a gamma trace, optionally convolve it with a Gaussian kernel, add it to a channel, and return it.

                Parameters
                ----------
                channel : str
                    Target channel name.
                shape : float
                    Positive gamma shape parameter.
                scale : float
                    Positive gamma scale parameter.
                gaussian_sigma : pint.Quantity, default = 0 second
                    Gaussian convolution sigma convertible to seconds.

                Returns
                -------
                pint.Quantity
                    Generated trace returned in watts.
            )doc"
        );
}
