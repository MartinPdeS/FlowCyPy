#include <limits>
#include <memory>
#include <cmath>

#include <pybind11/pybind11.h>
#include <pint/pint.h>
#include "amplifier.h"

namespace py = pybind11;

PYBIND11_MODULE(amplifier, module) {
    py::object ureg = get_shared_ureg();

    py::class_<Amplifier, std::shared_ptr<Amplifier>>(module, "Amplifier",
            R"pdoc(
                Represents a transimpedance amplifier used to convert photocurrent into voltage.

                This model simulates an amplifier with a specified transimpedance gain and bandwidth,
                while including input referred voltage noise and current noise. It is intended for
                photodetection systems where amplifier noise and finite bandwidth affect signal quality
                and signal to noise ratio.

                Parameters
                ----------
                gain : Quantity
                    Transimpedance gain of the amplifier in ohms.
                bandwidth : Quantity | None, optional
                    The amplifier bandwidth in hertz. If None, the amplifier is treated as having
                    no bandwidth limit.
                voltage_noise_density : Quantity | None, optional
                    Input referred voltage noise spectral density in volt / hertz ** 0.5.
                current_noise_density : Quantity | None, optional
                    Input referred current noise spectral density in ampere / hertz ** 0.5.

                Attributes
                ----------
                gain : Quantity
                    Transimpedance gain in ohms.
                bandwidth : Quantity | None
                    Bandwidth in hertz, or None if unlimited.
                voltage_noise_density : Quantity
                    Voltage noise spectral density in volt / hertz ** 0.5.
                current_noise_density : Quantity
                    Current noise spectral density in ampere / hertz ** 0.5.
            )pdoc"
        )
        .def(
            py::init(
                [](
                    const py::object& gain,
                    const py::object& bandwidth,
                    const py::object& voltage_noise_density,
                    const py::object& current_noise_density
                ) {
                    double gain_ohm = gain.attr("to")("ohm").attr("magnitude").cast<double>();

                    if (gain_ohm <= 0.0) {
                        throw std::runtime_error("gain must be strictly positive.");
                    }

                    double bandwidth_hertz = std::numeric_limits<double>::quiet_NaN();
                    if (!bandwidth.is_none()) {
                        bandwidth_hertz = bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                        if (bandwidth_hertz <= 0.0) {
                            throw std::runtime_error("bandwidth must be strictly positive.");
                        }
                    }

                    double voltage_noise_density_value = 0.0;
                    if (!voltage_noise_density.is_none()) {
                        voltage_noise_density_value = voltage_noise_density.attr("to")("volt / hertz ** 0.5").attr("magnitude").cast<double>();

                        if (voltage_noise_density_value < 0.0) {
                            throw std::runtime_error("voltage_noise_density must be non negative.");
                        }
                    }

                    double current_noise_density_value = 0.0;
                    if (!current_noise_density.is_none()) {
                        current_noise_density_value = current_noise_density.attr("to")("ampere / hertz ** 0.5").attr("magnitude").cast<double>();

                        if (current_noise_density_value < 0.0) {
                            throw std::runtime_error("current_noise_density must be non negative.");
                        }
                    }

                    return std::make_shared<Amplifier>(
                        gain_ohm,
                        bandwidth_hertz,
                        voltage_noise_density_value,
                        current_noise_density_value
                    );
                }
            ),
            py::arg("gain"),
            py::arg("bandwidth") = py::none(),
            py::arg("voltage_noise_density") = py::none(),
            py::arg("current_noise_density") = py::none(),
            R"pbdoc(
                Create an Amplifier instance.

                Parameters
                ----------
                gain : pint.Quantity
                    Transimpedance gain in ohms.
                bandwidth : pint.Quantity | None, optional
                    Amplifier bandwidth in hertz. If None, no bandwidth limit is applied.
                voltage_noise_density : pint.Quantity | None, optional
                    Input referred voltage noise density in volt / hertz ** 0.5.
                    Defaults to 0 volt / hertz ** 0.5.
                current_noise_density : pint.Quantity | None, optional
                    Input referred current noise density in ampere / hertz ** 0.5.
                    Defaults to 0 ampere / hertz ** 0.5.
            )pbdoc"
        )
        .def_property_readonly(
            "gain",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.gain) * ureg.attr("ohm");
            },
            R"pbdoc(
                Transimpedance gain returned as a pint.Quantity in ohms.
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
                return py::cast(amplifier.voltage_noise_density) * ureg.attr("volt / hertz ** 0.5");
            },
            R"pbdoc(
                Voltage noise spectral density returned as a pint.Quantity in volt / hertz ** 0.5.
            )pbdoc"
        )
        .def_property_readonly(
            "current_noise_density",
            [ureg](const Amplifier& amplifier) {
                return py::cast(amplifier.current_noise_density) * ureg.attr("ampere / hertz ** 0.5");
            },
            R"pbdoc(
                Current noise spectral density returned as a pint.Quantity in ampere / hertz ** 0.5.
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
            &Amplifier::amplify,
            py::arg("signal_generator"),
            R"pbdoc(
                Amplify a signal using the amplifier characteristics.

                Parameters
                ----------
                signal_generator : SignalGenerator
                    The signal generator providing the input signal to be amplified. The amplifier modifies the signal in place.
            )pbdoc"
        );
}
