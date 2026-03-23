#include <limits>
#include <memory>
#include <cmath>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pint/pint.h>

#include "amplifier.h"

namespace py = pybind11;

PYBIND11_MODULE(amplifier, module) {
    py::object ureg = get_shared_ureg();

    py::class_<Amplifier, std::shared_ptr<Amplifier>>(
        module,
        "Amplifier",
        R"pdoc(
            Represents a transimpedance amplifier applied to a one dimensional current signal.

            This model converts an input current signal into an output voltage signal using
            the configured transimpedance gain. It can optionally include a finite analog
            bandwidth and additive Gaussian noise derived from voltage and current noise
            densities.

            If a sampling rate is provided during amplification and the amplifier bandwidth
            is defined, a realistic low-pass filter is applied. If no sampling rate is
            provided, waveform filtering is skipped, but the bandwidth is still used for
            integrated noise estimation.

            Parameters
            ----------
            gain : Quantity
                Transimpedance gain in volt / ampere.
            bandwidth : Quantity | None, optional
                Amplifier bandwidth in hertz. If None, no bandwidth-limited filtering or
                bandwidth-based noise integration is applied.
            voltage_noise_density : Quantity | None, optional
                Output referred voltage noise spectral density in volt / hertz ** 0.5.
            current_noise_density : Quantity | None, optional
                Input referred current noise spectral density in ampere / hertz ** 0.5.
            filter_order : int, optional
                Order of the low-pass filter used when bandwidth filtering is enabled.

            Attributes
            ----------
            gain : Quantity
                Transimpedance gain in volt / ampere.
            bandwidth : Quantity | None
                Bandwidth in hertz, or None if unlimited.
            voltage_noise_density : Quantity
                Voltage noise spectral density in volt / hertz ** 0.5.
            current_noise_density : Quantity
                Current noise spectral density in ampere / hertz ** 0.5.
            filter_order : int
                Order of the low-pass filter.
        )pdoc"
    )
        .def(
            py::init(
                [](
                    const py::object& gain,
                    const py::object& bandwidth,
                    const py::object& voltage_noise_density,
                    const py::object& current_noise_density,
                    const int filter_order
                ) {
                    const double gain_value =
                        gain.attr("to")("volt / ampere").attr("magnitude").cast<double>();

                    if (gain_value <= 0.0) {
                        throw std::runtime_error("gain must be strictly positive.");
                    }

                    double bandwidth_hertz = std::numeric_limits<double>::quiet_NaN();
                    if (!bandwidth.is_none()) {
                        bandwidth_hertz =
                            bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                        if (bandwidth_hertz <= 0.0) {
                            throw std::runtime_error("bandwidth must be strictly positive.");
                        }
                    }

                    double voltage_noise_density_value = 0.0;
                    if (!voltage_noise_density.is_none()) {
                        voltage_noise_density_value =
                            voltage_noise_density
                                .attr("to")("volt / hertz ** 0.5")
                                .attr("magnitude")
                                .cast<double>();

                        if (voltage_noise_density_value < 0.0) {
                            throw std::runtime_error(
                                "voltage_noise_density must be non negative."
                            );
                        }
                    }

                    double current_noise_density_value = 0.0;
                    if (!current_noise_density.is_none()) {
                        current_noise_density_value =
                            current_noise_density
                                .attr("to")("ampere / hertz ** 0.5")
                                .attr("magnitude")
                                .cast<double>();

                        if (current_noise_density_value < 0.0) {
                            throw std::runtime_error(
                                "current_noise_density must be non negative."
                            );
                        }
                    }

                    if (filter_order <= 0) {
                        throw std::runtime_error("filter_order must be strictly positive.");
                    }

                    return std::make_shared<Amplifier>(
                        gain_value,
                        bandwidth_hertz,
                        voltage_noise_density_value,
                        current_noise_density_value,
                        filter_order
                    );
                }
            ),
            py::arg("gain"),
            py::arg("bandwidth") = py::none(),
            py::arg("voltage_noise_density") = py::none(),
            py::arg("current_noise_density") = py::none(),
            py::arg("filter_order") = 2,
            R"pbdoc(
                Create an Amplifier instance.

                Parameters
                ----------
                gain : pint.Quantity
                    Transimpedance gain in volt / ampere.
                bandwidth : pint.Quantity | None, optional
                    Amplifier bandwidth in hertz. If None, no bandwidth-limited behavior
                    is applied.
                voltage_noise_density : pint.Quantity | None, optional
                    Voltage noise density in volt / hertz ** 0.5.
                    Defaults to 0 volt / hertz ** 0.5.
                current_noise_density : pint.Quantity | None, optional
                    Current noise density in ampere / hertz ** 0.5.
                    Defaults to 0 ampere / hertz ** 0.5.
                filter_order : int, optional
                    Order of the low-pass filter used when waveform filtering is enabled.
            )pbdoc"
        )
        .def_property_readonly(
            "gain",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.gain) * ureg.attr("volt") / ureg.attr("ampere");
            },
            R"pbdoc(
                Transimpedance gain returned as a pint.Quantity in volt / ampere.
            )pbdoc"
        )
        .def_property_readonly(
            "bandwidth",
            [ureg](const Amplifier& amplifier) -> py::object {
                if (std::isnan(amplifier.bandwidth)) {
                    return py::none();
                }

                return py::cast(amplifier.bandwidth) * ureg.attr("hertz");
            },
            R"pbdoc(
                Bandwidth returned as a pint.Quantity in hertz, or None if unlimited.
            )pbdoc"
        )
        .def_property_readonly(
            "voltage_noise_density",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.voltage_noise_density)
                    * ureg.attr("volt / hertz ** 0.5");
            },
            R"pbdoc(
                Voltage noise spectral density returned as a pint.Quantity in volt / hertz ** 0.5.
            )pbdoc"
        )
        .def_property_readonly(
            "current_noise_density",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.current_noise_density)
                    * ureg.attr("ampere / hertz ** 0.5");
            },
            R"pbdoc(
                Current noise spectral density returned as a pint.Quantity in ampere / hertz ** 0.5.
            )pbdoc"
        )
        .def_property_readonly(
            "filter_order",
            [](const Amplifier& amplifier) {
                return amplifier.filter_order;
            },
            R"pbdoc(
                Order of the low-pass filter used when bandwidth filtering is enabled.
            )pbdoc"
        )
        .def(
            "get_rms_noise",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.get_rms_noise()) * ureg.attr("volt");
            },
            R"pbdoc(
                Calculate the RMS output noise of the amplifier.

                Returns
                -------
                pint.Quantity
                    RMS noise expressed in volts.
            )pbdoc"
        )
        .def(
            "amplify",
            [ureg](
                const Amplifier& amplifier,
                const py::object& signal,
                const py::object& sampling_rate
            ) {
                if (!py::hasattr(signal, "units") || !py::hasattr(signal, "magnitude")) {
                    throw std::runtime_error(
                        "signal must be a Pint quantity backed by a NumPy array."
                    );
                }

                py::object signal_in_ampere = signal.attr("to")("ampere");

                std::vector<double> input_signal =
                    signal_in_ampere.attr("magnitude").cast<std::vector<double>>();

                double sampling_rate_value = std::numeric_limits<double>::quiet_NaN();
                if (!sampling_rate.is_none()) {
                    sampling_rate_value =
                        sampling_rate.attr("to")("hertz").attr("magnitude").cast<double>();

                    if (sampling_rate_value <= 0.0) {
                        throw std::runtime_error("sampling_rate must be strictly positive.");
                    }
                }

                std::vector<double> output_signal =
                    amplifier.amplify(input_signal, sampling_rate_value);

                py::array_t<double> output_array(output_signal.size());
                auto mutable_view = output_array.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(output_signal.size()); ++index) {
                    mutable_view(index) = output_signal[static_cast<size_t>(index)];
                }

                return output_array * ureg.attr("volt");
            },
            py::arg("signal"),
            py::arg("sampling_rate"),
            R"pbdoc(
                Amplify a one dimensional current signal and return the output voltage signal.

                Parameters
                ----------
                signal : pint.Quantity
                    One dimensional signal with units of ampere.
                sampling_rate : pint.Quantity | None, optional
                    Sampling rate in hertz. If provided and the amplifier bandwidth is defined,
                    bandwidth-limited filtering is applied. If omitted, waveform filtering is
                    skipped.

                Returns
                -------
                pint.Quantity
                    Amplified output signal with units of volt.
            )pbdoc"
        );
}
