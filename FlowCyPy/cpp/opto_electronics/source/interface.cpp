#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <opto_electronics/source/source.h>
#include <pint/pint.h>

namespace py = pybind11;


PYBIND11_MODULE(source, module) {
    py::object ureg = get_shared_ureg();

    py::class_<BaseSource, std::shared_ptr<BaseSource>>(
        module,
        "BaseSource",
        R"doc(
            Base class for optical sources.

            This class stores the fundamental properties of an optical source,
            including wavelength, optical power, polarization, and relative
            intensity noise. It exposes both electric field amplitude based
            quantities and optical power based quantities.

            Notes
            -----
            The `generate_pulses`, `get_power_at`, and `get_power_signal`
            methods return values in watt on the Python side.
        )doc"
    )
        .def_property_readonly(
            "wavelength",
            [ureg](const BaseSource& source) {
                return py::cast(source.wavelength) * ureg.attr("meter");
            }
        )
        .def_readwrite(
            "include_shot_noise",
            &BaseSource::include_shot_noise
        )
        .def_readwrite(
            "include_rin_noise",
            &BaseSource::include_rin_noise
        )
        .def_property_readonly(
            "rin",
            [](const BaseSource& source) {
                return source.rin;
            }
        )
        .def_property_readonly(
            "optical_power",
            [ureg](const BaseSource& source) {
                return py::cast(source.optical_power) * ureg.attr("watt");
            }
        )
        .def_property_readonly(
            "amplitude",
            [ureg](const BaseSource& source) {
                return py::cast(source.amplitude) * ureg.attr("volt_per_meter");
            }
        )
        .def_property_readonly(
            "polarization",
            [ureg](const BaseSource& source) {
                return py::cast(source.polarization) * ureg.attr("radian");
            }
        )
        .def_property_readonly(
            "frequency",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_frequency()) * ureg.attr("hertz");
            }
        )
        .def_property_readonly(
            "photon_energy",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_photon_energy()) * ureg.attr("joule");
            }
        )
        .def_property_readonly(
            "rin_linear",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_rin_linear()) / ureg.attr("hertz");
            }
        )
        .def(
            "add_rin_to_signal",
            [ureg](const BaseSource& source, std::vector<double> signal_values, const py::object& bandwidth) {
                const double bandwidth_hertz =
                    bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                source.add_rin_to_signal(signal_values, bandwidth_hertz);

                py::array_t<double> output(signal_values.size());
                auto mutable_view = output.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(signal_values.size()); ++index) {
                    mutable_view(index) = signal_values[index];
                }

                return output;
            },
            py::arg("signal_values"),
            py::arg("bandwidth"),
            R"doc(
                Add relative intensity noise to an input signal.

                Parameters
                ----------
                signal_values : array-like
                    Input signal values.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                numpy.ndarray
                    Noisy signal values as a dimensionless array.
            )doc"
        )
        .def(
            "amplitude_at",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z
            ) {
                double amplitude_value = source.get_amplitude_at(
                    x.attr("to")("meter").attr("magnitude").cast<double>(),
                    y.attr("to")("meter").attr("magnitude").cast<double>(),
                    z.attr("to")("meter").attr("magnitude").cast<double>()
                );

                return py::cast(amplitude_value) * ureg.attr("volt_per_meter");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z") = py::float_(0.0) * ureg.attr("meter")
        )
        .def(
            "get_power_at",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z
            ) {
                double values = source.get_power_at(
                    x.attr("to")("meter").attr("magnitude").cast<double>(),
                    y.attr("to")("meter").attr("magnitude").cast<double>(),
                    z.attr("to")("meter").attr("magnitude").cast<double>()
                );
                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z") = py::float_(0.0) * ureg.attr("meter"),
            R"doc(
                Evaluate optical power at a spatial position.

                Returns
                -------
                pint.Quantity
                    Optical power in watt.
            )doc"
        )
        .def(
            "get_amplitude_signal",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z,
                const py::object& bandwidth
            ) {
                std::vector<double> values = source.get_amplitude_signal(
                    x.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    y.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    z.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    bandwidth.attr("to")("hertz").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("volt / meter");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z"),
            py::arg("bandwidth")
        )
        .def(
            "get_power_signal",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z,
                const py::object& bandwidth
            ) {
                std::vector<double> values = source.get_power_signal(
                    x.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    y.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    z.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    bandwidth.attr("to")("hertz").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z"),
            py::arg("bandwidth"),
            R"doc(
                Evaluate optical power over multiple particle positions.

                Returns
                -------
                pint.Quantity
                    Array of optical powers in watt.
            )doc"
        )
        .def(
            "get_particle_width",
            [ureg](const BaseSource& source, const py::object& velocity) {
                std::vector<double> velocity_values = velocity.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>();

                std::vector<double> widths = source.get_particle_width(velocity_values);

                return py::cast(widths) * ureg.attr("second");
            },
            py::arg("velocity")
        )
        .def(
            "generate_pulses",
            [ureg](
                const BaseSource& source,
                const py::object& velocities,
                const py::object& pulse_centers,
                const py::object& pulse_amplitudes,
                const py::object& time_array,
                const py::object& base_level,
                const py::object& bandwidth
            ) {
                std::vector<double> values = source.generate_pulses(
                    velocities.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>(),
                    pulse_centers.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    pulse_amplitudes.attr("to")("watt").attr("magnitude").cast<std::vector<double>>(),
                    time_array.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    base_level.attr("to")("watt").attr("magnitude").cast<double>(),
                    bandwidth.attr("to")("hertz").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("velocities"),
            py::arg("pulse_centers"),
            py::arg("pulse_amplitudes"),
            py::arg("time_array"),
            py::arg("base_level"),
            py::arg("bandwidth"),
            R"doc(
                Generate a pulse train.

                Parameters
                ----------
                pulse_widths : sequence[pint.Quantity]
                    Pulse widths in seconds.
                pulse_centers : sequence[pint.Quantity]
                    Pulse center times in seconds.
                pulse_amplitudes : sequence[pint.Quantity]
                    Pulse amplitudes in watt.
                time_array : sequence[pint.Quantity]
                    Time axis in seconds.
                base_level : pint.Quantity
                    Baseline signal in watt.

                Returns
                -------
                pint.Quantity
                    Pulse train in watt.
            )doc"
        );

    py::class_<Gaussian, BaseSource, std::shared_ptr<Gaussian>>(
        module,
        "Gaussian",
        R"doc(
            Astigmatic Gaussian optical source defined by waist_y and waist_z.
        )doc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& wavelength,
                    const py::object& optical_power,
                    const py::object& waist_y,
                    const py::object& waist_z,
                    const double rin,
                    const py::object& polarization,
                    const bool include_shot_noise,
                    const bool include_rin_noise
                ) {
                    const double wavelength_meter =
                        wavelength.attr("to")("meter").attr("magnitude").cast<double>();

                    const double optical_power_watt =
                        optical_power.attr("to")("watt").attr("magnitude").cast<double>();

                    const double waist_y_meter =
                        waist_y.attr("to")("meter").attr("magnitude").cast<double>();

                    const double waist_z_meter =
                        waist_z.attr("to")("meter").attr("magnitude").cast<double>();

                    const double polarization_radian =
                        polarization.attr("to")("radian").attr("magnitude").cast<double>();

                    return std::make_shared<Gaussian>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_y_meter,
                        waist_z_meter,
                        polarization_radian,
                        include_shot_noise,
                        include_rin_noise
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("optical_power"),
            py::arg("waist_y"),
            py::arg("waist_z"),
            py::arg("rin") = -120.0,
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            }
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            }
        )
        .def(
            "set_waist",
            [](Gaussian& source, const py::object& waist_y, const py::object& waist_z) {
                const double waist_y_meter =
                    waist_y.attr("to")("meter").attr("magnitude").cast<double>();

                const double waist_z_meter =
                    waist_z.attr("to")("meter").attr("magnitude").cast<double>();

                source.set_waist(waist_y_meter, waist_z_meter);
            },
            py::arg("waist_y"),
            py::arg("waist_z")
        );

    py::class_<FlatTop, BaseSource, std::shared_ptr<FlatTop>>(
        module,
        "FlatTop",
        R"doc(
            Astigmatic flat top optical source defined by waist_y and waist_z.
        )doc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& wavelength,
                    const py::object& optical_power,
                    const py::object& waist_y,
                    const py::object& waist_z,
                    const double rin,
                    const py::object& polarization,
                    const bool include_shot_noise,
                    const bool include_rin_noise
                ) {
                    const double wavelength_meter =
                        wavelength.attr("to")("meter").attr("magnitude").cast<double>();

                    const double optical_power_watt =
                        optical_power.attr("to")("watt").attr("magnitude").cast<double>();

                    const double waist_y_meter =
                        waist_y.attr("to")("meter").attr("magnitude").cast<double>();

                    const double waist_z_meter =
                        waist_z.attr("to")("meter").attr("magnitude").cast<double>();

                    const double polarization_radian =
                        polarization.attr("to")("radian").attr("magnitude").cast<double>();

                    return std::make_shared<FlatTop>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_y_meter,
                        waist_z_meter,
                        polarization_radian,
                        include_shot_noise,
                        include_rin_noise
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("optical_power"),
            py::arg("waist_y"),
            py::arg("waist_z"),
            py::arg("rin") = -120.0,
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            }
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            }
        )
        .def(
            "set_waist",
            [](FlatTop& source, const py::object& waist_y, const py::object& waist_z) {
                const double waist_y_meter =
                    waist_y.attr("to")("meter").attr("magnitude").cast<double>();

                const double waist_z_meter =
                    waist_z.attr("to")("meter").attr("magnitude").cast<double>();

                source.set_waist(waist_y_meter, waist_z_meter);
            },
            py::arg("waist_y"),
            py::arg("waist_z")
        );
}
