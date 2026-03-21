#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <opto_electronics/source/source.h>
#include <pint/pint.h>

namespace py = pybind11;


void register_source(py::module& module) {
    py::object ureg = get_shared_ureg();

    py::class_<BaseSource, std::shared_ptr<BaseSource>>(
        module,
        "BaseSource",
        R"doc(
            Base class for optical sources.

            This class stores common source parameters such as wavelength,
            relative intensity noise, optical power, on axis electric field amplitude,
            and polarization. It also provides helper methods for frequency,
            photon energy, spatial amplitude evaluation, and source noise injection.

            Notes
            -----
            All internal values are stored in SI units on the C++ side.
            The Python interface returns Pint quantities for physical values.
        )doc"
    )
        .def_property_readonly(
            "wavelength",
            [ureg](const BaseSource& source) {
                return py::cast(source.wavelength) * ureg.attr("meter");
            },
            R"doc(
                Wavelength returned as a Pint quantity in meters.
            )doc"
        )
        .def_property_readonly(
            "rin",
            [](const BaseSource& source) {
                return source.rin;
            },
            R"doc(
                Relative intensity noise in dB / Hz.
            )doc"
        )
        .def_property_readonly(
            "optical_power",
            [ureg](const BaseSource& source) {
                return py::cast(source.optical_power) * ureg.attr("watt");
            },
            R"doc(
                Optical power returned as a Pint quantity in watts.
            )doc"
        )
        .def_property_readonly(
            "amplitude",
            [ureg](const BaseSource& source) {
                return py::cast(source.amplitude) * ureg.attr("volt_per_meter");
            },
            R"doc(
                On axis electric field amplitude at focus returned as volt per meter.
            )doc"
        )
        .def_property_readonly(
            "polarization",
            [ureg](const BaseSource& source) {
                return py::cast(source.polarization) * ureg.attr("radian");
            },
            R"doc(
                Polarization angle returned as a Pint quantity in radians.
            )doc"
        )
        .def_property_readonly(
            "frequency",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_frequency()) * ureg.attr("hertz");
            },
            R"doc(
                Optical frequency returned as a Pint quantity in hertz.
            )doc"
        )
        .def_property_readonly(
            "photon_energy",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_photon_energy()) * ureg.attr("joule");
            },
            R"doc(
                Photon energy returned as a Pint quantity in joules.
            )doc"
        )
        .def_property_readonly(
            "rin_linear",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_rin_linear()) / ureg.attr("hertz");
            },
            R"doc(
                Relative intensity noise converted to linear scale, returned as 1 / hertz.
            )doc"
        )
        .def(
            "add_rin_to_signal",
            [](const BaseSource& source, std::vector<double> amplitudes, const py::object& bandwidth) {
                const double bandwidth_hertz = bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                source.add_rin_to_signal(amplitudes, bandwidth_hertz);

                return amplitudes;
            },
            py::arg("amplitudes"),
            py::arg("bandwidth"),
            R"doc(
                Add relative intensity noise to a signal amplitude vector.

                Parameters
                ----------
                amplitudes : list[float]
                    Signal amplitudes to perturb.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                list[float]
                    Noisy amplitudes.
            )doc"
        )
        .def(
            "amplitude_at",
            [](const BaseSource& source, const py::object& x, const py::object& y, const py::object& z) {
                const double x_meter = x.attr("to")("meter").attr("magnitude").cast<double>();
                const double y_meter = y.attr("to")("meter").attr("magnitude").cast<double>();
                const double z_meter = z.attr("to")("meter").attr("magnitude").cast<double>();

                return py::cast(source.get_amplitude_at(x_meter, y_meter, z_meter)) * ureg.attr("volt_per_meter");
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z") = py::float_(0.0) * ureg.attr("meter"),
            R"doc(
                Evaluate the electric field amplitude at a given position.

                Parameters
                ----------
                x : pint.Quantity
                    X position in meters.
                y : pint.Quantity
                    Y position in meters.
                z : pint.Quantity, optional
                    Z position in meters.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude in volt per meter.
            )doc"
        )
        .def(
            "get_amplitude_signal",
            [](const BaseSource& source,
               const std::vector<double>& x,
               const std::vector<double>& y,
               const std::vector<double>& z,
               const py::object& bandwidth,
               const bool include_source_noise) {
                const double bandwidth_hertz = bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();

                return source.get_amplitude_signal(
                    x,
                    y,
                    z,
                    bandwidth_hertz,
                    include_source_noise
                );
            },
            py::arg("x"),
            py::arg("y"),
            py::arg("z"),
            py::arg("bandwidth"),
            py::arg("include_source_noise") = true,
            R"doc(
                Evaluate the source amplitude over multiple particle positions.

                Parameters
                ----------
                x : list[float]
                    X positions in meters.
                y : list[float]
                    Y positions in meters.
                z : list[float]
                    Z positions in meters.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.
                include_source_noise : bool, optional
                    Whether to include source RIN noise.

                Returns
                -------
                list[float]
                    Signal amplitudes in volt per meter.
            )doc"
        )
        .def(
            "get_particle_width",
            [ureg](const BaseSource& source, const py::object& velocity) {
                const double velocity_meter_per_second = velocity.attr("to")("meter / second").attr("magnitude").cast<double>();

                return py::cast(source.get_particle_width(velocity_meter_per_second)) * ureg.attr("meter");
            },
            py::arg("velocity"),
            R"doc(
                Compute the effective particle width associated with the source profile.

                Parameters
                ----------
                velocity : pint.Quantity
                    Particle velocity in meter per second.

                Returns
                -------
                pint.Quantity
                    Effective width in meters.
            )doc"
        );

    py::class_<Gaussian, BaseSource, std::shared_ptr<Gaussian>>(
        module,
        "Gaussian",
        R"doc(
            Symmetric Gaussian optical source defined by a single beam waist.
        )doc"
    )
        .def(
            py::init(
                [](
                    const py::object& wavelength,
                    const double rin,
                    const py::object& optical_power,
                    const py::object& waist,
                    const py::object& polarization
                ) {
                    const double wavelength_meter = wavelength.attr("to")("meter").attr("magnitude").cast<double>();
                    const double optical_power_watt = optical_power.attr("to")("watt").attr("magnitude").cast<double>();
                    const double waist_meter = waist.attr("to")("meter").attr("magnitude").cast<double>();
                    const double polarization_radian = polarization.attr("to")("radian").attr("magnitude").cast<double>();

                    return std::make_shared<Gaussian>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_meter,
                        polarization_radian
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("rin") = -120.0,
            py::arg("optical_power"),
            py::arg("waist"),
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            R"doc(
                Create a symmetric Gaussian beam.

                Parameters
                ----------
                wavelength : pint.Quantity
                    Wavelength in meters.
                rin : float, optional
                    Relative intensity noise in dB / Hz.
                optical_power : pint.Quantity
                    Optical power in watts.
                waist : pint.Quantity
                    Beam waist in meters.
                polarization : pint.Quantity, optional
                    Polarization angle in radians.
            )doc"
        )
        .def_property_readonly(
            "waist",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist) * ureg.attr("meter");
            },
            R"doc(
                Beam waist returned as a Pint quantity in meters.
            )doc"
        )
        .def(
            "set_waist",
            [](Gaussian& source, const py::object& waist) {
                const double waist_meter = waist.attr("to")("meter").attr("magnitude").cast<double>();
                source.set_waist(waist_meter);
            },
            py::arg("waist"),
            R"doc(
                Set the beam waist.

                Parameters
                ----------
                waist : pint.Quantity
                    Beam waist in meters.
            )doc"
        );

    py::class_<AsymetricGaussian, BaseSource, std::shared_ptr<AsymetricGaussian>>(
        module,
        "AsymetricGaussian",
        R"doc(
            Astigmatic Gaussian optical source defined by two beam waists.
        )doc"
    )
        .def(
            py::init(
                [](
                    const py::object& wavelength,
                    const double rin,
                    const py::object& optical_power,
                    const py::object& waist_y,
                    const py::object& waist_z,
                    const py::object& polarization
                ) {
                    const double wavelength_meter = wavelength.attr("to")("meter").attr("magnitude").cast<double>();
                    const double optical_power_watt = optical_power.attr("to")("watt").attr("magnitude").cast<double>();
                    const double waist_y_meter = waist_y.attr("to")("meter").attr("magnitude").cast<double>();
                    const double waist_z_meter = waist_z.attr("to")("meter").attr("magnitude").cast<double>();
                    const double polarization_radian = polarization.attr("to")("radian").attr("magnitude").cast<double>();

                    return std::make_shared<AsymetricGaussian>(
                        wavelength_meter,
                        rin,
                        optical_power_watt,
                        waist_y_meter,
                        waist_z_meter,
                        polarization_radian
                    );
                }
            ),
            py::arg("wavelength"),
            py::arg("rin") = 0.0,
            py::arg("optical_power"),
            py::arg("waist_y"),
            py::arg("waist_z"),
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            R"doc(
                Create an astigmatic Gaussian beam.

                Parameters
                ----------
                wavelength : pint.Quantity
                    Wavelength in meters.
                rin : float, optional
                    Relative intensity noise in dB / Hz.
                optical_power : pint.Quantity
                    Optical power in watts.
                waist_y : pint.Quantity
                    Beam waist along Y in meters.
                waist_z : pint.Quantity
                    Beam waist along Z in meters.
                polarization : pint.Quantity, optional
                    Polarization angle in radians.
            )doc"
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const AsymetricGaussian& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            },
            R"doc(
                Beam waist along Y returned as a Pint quantity in meters.
            )doc"
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const AsymetricGaussian& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            },
            R"doc(
                Beam waist along Z returned as a Pint quantity in meters.
            )doc"
        )
        .def(
            "set_waist",
            [](AsymetricGaussian& source, const py::object& waist_y, const py::object& waist_z) {
                const double waist_y_meter = waist_y.attr("to")("meter").attr("magnitude").cast<double>();
                const double waist_z_meter = waist_z.attr("to")("meter").attr("magnitude").cast<double>();

                source.set_waist(waist_y_meter, waist_z_meter);
            },
            py::arg("waist_y"),
            py::arg("waist_z"),
            R"doc(
                Set the Y and Z beam waists.

                Parameters
                ----------
                waist_y : pint.Quantity
                    Beam waist along Y in meters.
                waist_z : pint.Quantity
                    Beam waist along Z in meters.
            )doc"
        );
}
