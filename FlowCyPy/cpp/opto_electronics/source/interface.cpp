#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <opto_electronics/source/source.h>
#include <pint/pint.h>

namespace py = pybind11;


PYBIND11_MODULE(source, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"doc(
        Optical source models for time domain flow cytometry simulations.

        This module exposes beam models that can generate spatially varying optical
        fields, optical power traces, stochastic gamma-based aggregate power traces,
        and time domain pulse signals. All physical inputs and outputs are unit aware
        on the Python side through Pint.
    )doc";

    py::class_<BaseSource, std::shared_ptr<BaseSource>>(
        module,
        "BaseSource",
        R"doc(
            Abstract base class for optical source models.
        )doc"
        )
        .def_property_readonly(
            "wavelength",
            [ureg](const BaseSource& source) {
                return py::cast(source.wavelength) * ureg.attr("meter");
            }
        )
        .def("test_openmp", &BaseSource::test_openmp)
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
        .def_property(
            "optical_power",
            [ureg](const BaseSource& source) {
                return py::cast(source.optical_power) * ureg.attr("watt");
            },
            [ureg](BaseSource& source, const py::object& power) {
                source.optical_power = power.attr("to")("watt").attr("magnitude").cast<double>();
                source.update_amplitude();
            }
        )
        .def_property_readonly(
            "amplitude",
            [ureg](const BaseSource& source) {
                return py::cast(source.amplitude) * ureg.attr("volt / meter");
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
        .def_property(
            "bandwidth",
            [ureg](const BaseSource& source) {
                return py::cast(source.bandwidth) * ureg.attr("hertz");
            },
            [ureg](BaseSource& source, const py::object& bandwidth) {
                source.bandwidth = bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();
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
            "add_shot_noise_to_signal",
            [ureg](const BaseSource& source, const py::object& signal, const py::object& time_array) {
                const double time_step = source.get_time_step_from_time_array(
                    time_array.attr("to")("second").attr("magnitude").cast<std::vector<double>>()
                );

                std::vector<double> signal_values =
                    signal.attr("to")("watt").attr("magnitude").cast<std::vector<double>>();

                source.add_shot_noise_to_signal(signal_values, time_step);

                py::array_t<double> output(signal_values.size());
                auto mutable_view = output.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(signal_values.size()); ++index) {
                    mutable_view(index) = signal_values[static_cast<size_t>(index)];
                }

                return output * ureg.attr("watt");
            },
            py::arg("signal"),
            py::arg("time"),
            R"doc(
                Add shot noise to an optical power signal.
            )doc"
        )
        .def(
            "add_rin_to_signal",
            [ureg](const BaseSource& source, const py::object& signal) {
                std::vector<double> signal_values =
                    signal.attr("to")("watt").attr("magnitude").cast<std::vector<double>>();

                source.add_rin_to_signal(signal_values);
                py::array_t<double> output(signal_values.size());
                auto mutable_view = output.mutable_unchecked<1>();

                for (ssize_t index = 0; index < static_cast<ssize_t>(signal_values.size()); ++index) {
                    mutable_view(index) = signal_values[static_cast<size_t>(index)];
                }

                return output * ureg.attr("watt");
            },
            py::arg("signal"),
            R"doc(
                Add source RIN to a single optical power signal.
            )doc"
        )
        .def(
            "add_rin_to_signal_dict",
            [ureg](const BaseSource& source, const py::dict& signal_dict) {
                if (!signal_dict.contains("Time")) {
                    throw std::runtime_error("signal_dict must contain a 'Time' entry.");
                }

                std::vector<std::string> detector_names;
                std::vector<std::vector<double>> detector_signals;

                for (auto item : signal_dict) {
                    const std::string key = py::cast<std::string>(item.first);

                    if (key == "Time") {
                        continue;
                    }

                    py::object value = py::reinterpret_borrow<py::object>(item.second);

                    if (!py::hasattr(value, "units") || !py::hasattr(value, "magnitude")) {
                        throw std::runtime_error(
                            "Each detector entry in signal_dict must be a Pint quantity."
                        );
                    }

                    py::object signal_in_watt = value.attr("to")("watt");

                    detector_names.push_back(key);
                    detector_signals.push_back(
                        signal_in_watt.attr("magnitude").cast<std::vector<double>>()
                    );
                }

                source.add_common_rin_to_signals(detector_signals);

                py::dict output_signal_dict;
                output_signal_dict["Time"] = signal_dict["Time"];

                for (size_t channel_index = 0; channel_index < detector_names.size(); ++channel_index) {
                    py::array_t<double> output_array(detector_signals[channel_index].size());
                    auto mutable_view = output_array.mutable_unchecked<1>();

                    for (ssize_t sample_index = 0; sample_index < static_cast<ssize_t>(detector_signals[channel_index].size()); ++sample_index) {
                        mutable_view(sample_index) =
                            detector_signals[channel_index][static_cast<size_t>(sample_index)];
                    }

                    output_signal_dict[py::str(detector_names[channel_index])] =
                        output_array * ureg.attr("watt");
                }

                return output_signal_dict;
            },
            py::arg("signal_dict"),
            R"doc(
                Apply one common source RIN realization to all detector channels in a signal dictionary.
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

                return py::cast(amplitude_value) * ureg.attr("volt / meter");
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
                double value = source.get_power_at(
                    x.attr("to")("meter").attr("magnitude").cast<double>(),
                    y.attr("to")("meter").attr("magnitude").cast<double>(),
                    z.attr("to")("meter").attr("magnitude").cast<double>()
                );
                return py::cast(value) * ureg.attr("watt");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z") = py::float_(0.0) * ureg.attr("meter")
        )
        .def(
            "get_amplitude_signal",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z
            ) {
                std::vector<double> values = source.get_amplitude_signal(
                    x.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    y.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    z.attr("to")("meter").attr("magnitude").cast<std::vector<double>>()
                );

                return py::cast(values) * ureg.attr("volt / meter");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z")
        )
        .def(
            "get_power_signal",
            [ureg](
                const BaseSource& source,
                const py::object& x,
                const py::object& y,
                const py::object& z,
                const py::object& time_step
            ) {
                std::vector<double> values = source.get_power_signal(
                    x.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    y.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    z.attr("to")("meter").attr("magnitude").cast<std::vector<double>>(),
                    time_step.attr("to")("second").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z"),
            py::arg("time_step")
        )
        .def(
            "get_particle_width",
            [ureg](const BaseSource& source, const py::object& velocity) {
                std::vector<double> velocity_values =
                    velocity.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>();

                std::vector<double> widths = source.get_particle_width(velocity_values);

                return py::cast(widths) * ureg.attr("second");
            },
            py::arg("velocity")
        )
        .def(
            "get_gamma_trace",
            [ureg](
                const BaseSource& source,
                const py::object& time_array,
                const double shape,
                const py::object& scale,
                const py::object& mean_velocity
            ) {
                std::vector<double> values = source.get_gamma_trace(
                    time_array.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    shape,
                    scale.attr("to")("watt").attr("magnitude").cast<double>(),
                    mean_velocity.attr("to")("meter / second").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("time_array"),
            py::arg("shape"),
            py::arg("scale"),
            py::arg("mean_velocity"),
            R"doc(
                Generate a gamma-distributed optical power trace using the intrinsic source kernel.
            )doc"
        )
        .def(
            "generate_pulses",
            [ureg](
                const BaseSource& source,
                const py::object& velocities,
                const py::object& pulse_centers,
                const py::object& pulse_amplitudes,
                const py::object& time_array,
                const py::object& base_level
            ) {

                std::vector<double> values = source.generate_pulses(
                    velocities.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>(),
                    pulse_centers.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    pulse_amplitudes.attr("to")("watt").attr("magnitude").cast<std::vector<double>>(),
                    time_array.attr("to")("second").attr("magnitude").cast<std::vector<double>>(),
                    base_level.attr("to")("watt").attr("magnitude").cast<double>()
                );

                return py::cast(values) * ureg.attr("watt");
            },
            py::arg("velocities"),
            py::arg("pulse_centers"),
            py::arg("pulse_amplitudes"),
            py::arg("time_array"),
            py::arg("base_level")
        );

    py::class_<Gaussian, BaseSource, std::shared_ptr<Gaussian>>(
        module,
        "Gaussian"
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
                    const py::object& bandwidth,
                    const bool include_shot_noise,
                    const bool include_rin_noise,
                    const bool debug_mode
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

                    const double bandwidth_hertz = bandwidth.is_none()
                        ? std::numeric_limits<double>::quiet_NaN()
                        : bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<Gaussian>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_y_meter,
                        waist_z_meter,
                        polarization_radian,
                        bandwidth_hertz,
                        include_shot_noise,
                        include_rin_noise,
                        debug_mode
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("optical_power"),
            py::arg("waist_y"),
            py::arg("waist_z"),
            py::arg("rin") = -120.0,
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("bandwidth") = py::none(),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true,
            py::arg("debug_mode") = false
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
        "FlatTop"
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
                    const py::object& bandwidth,
                    const bool include_shot_noise,
                    const bool include_rin_noise,
                    const bool debug_mode
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

                    const double bandwidth_hertz = bandwidth.is_none()
                        ? std::numeric_limits<double>::quiet_NaN()
                        : bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                    return std::make_shared<FlatTop>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_y_meter,
                        waist_z_meter,
                        polarization_radian,
                        bandwidth_hertz,
                        include_shot_noise,
                        include_rin_noise,
                        debug_mode
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("optical_power"),
            py::arg("waist_y"),
            py::arg("waist_z"),
            py::arg("rin") = -120.0,
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("bandwidth") = py::none(),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true,
            py::arg("debug_mode") = false
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
