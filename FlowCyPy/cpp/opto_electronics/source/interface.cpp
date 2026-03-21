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
        fields, optical power traces, and time domain pulse signals. All physical
        inputs and outputs are unit aware on the Python side through Pint.

        Available source types
        ----------------------
        BaseSource
            Abstract base interface shared by all optical source models.
        Gaussian
            Astigmatic Gaussian beam with independent waists along the Y and Z axes.
        FlatTop
            Astigmatic flat top beam with independent support widths along the Y and Z axes.

        General notes
        -------------
        - Length inputs are expressed in meter.
        - Time inputs are expressed in second.
        - Optical power outputs are expressed in watt.
        - Electric field amplitude outputs are expressed in volt / meter.
        - Photon statistics based shot noise can optionally be enabled at construction.
        - Relative intensity noise can optionally be enabled at construction.
    )doc";

    py::class_<BaseSource, std::shared_ptr<BaseSource>>(
        module,
        "BaseSource",
        R"doc(
            Abstract base class for optical source models.

            This class stores the core physical parameters of an optical source and
            provides common operations used by all derived beam models.

            Exposed physical quantities
            ---------------------------
            wavelength
                Optical wavelength.
            optical_power
                Total optical power carried by the source.
            polarization
                Polarization angle.
            rin
                Relative intensity noise specified in dB / Hz.
            rin_linear
                Relative intensity noise converted to linear units of 1 / Hz.
            frequency
                Optical frequency derived from the wavelength.
            photon_energy
                Energy of a single photon at the source wavelength.

            Noise model flags
            -----------------
            include_shot_noise
                If true, shot noise is included when generating power based pulse signals.
            include_rin_noise
                If true, relative intensity noise is included in methods that apply source noise.

            Notes
            -----
            This class is not intended to be instantiated directly from Python.
            Use a concrete subclass such as Gaussian or FlatTop instead.
        )doc"
    )
        .def_property_readonly(
            "wavelength",
            [ureg](const BaseSource& source) {
                return py::cast(source.wavelength) * ureg.attr("meter");
            },
            R"doc(
                Optical wavelength of the source.

                Returns
                -------
                pint.Quantity
                    Wavelength in meter.
            )doc"
        )
        .def_readwrite(
            "include_shot_noise",
            &BaseSource::include_shot_noise,
            R"doc(
                Whether shot noise is enabled for power based signal generation.

                Shot noise is modeled from photon counting statistics using the source
                wavelength and the provided detection bandwidth.

                Returns
                -------
                bool
                    True if shot noise is enabled.
            )doc"
        )
        .def_readwrite(
            "include_rin_noise",
            &BaseSource::include_rin_noise,
            R"doc(
                Whether relative intensity noise is enabled for source signal generation.

                Returns
                -------
                bool
                    True if relative intensity noise is enabled.
            )doc"
        )
        .def_property_readonly(
            "rin",
            [](const BaseSource& source) {
                return source.rin;
            },
            R"doc(
                Relative intensity noise of the source.

                The value is stored as a scalar in dB / Hz.

                Returns
                -------
                float
                    Relative intensity noise in dB / Hz.
            )doc"
        )
        .def_property_readonly(
            "optical_power",
            [ureg](const BaseSource& source) {
                return py::cast(source.optical_power) * ureg.attr("watt");
            },
            R"doc(
                Total optical power of the source.

                Returns
                -------
                pint.Quantity
                    Optical power in watt.
            )doc"
        )
        .def_property_readonly(
            "amplitude",
            [ureg](const BaseSource& source) {
                return py::cast(source.amplitude) * ureg.attr("volt / meter");
            },
            R"doc(
                On axis electric field amplitude at focus.

                This value corresponds to the peak electric field amplitude of the beam
                model at the focal position.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude in volt / meter.
            )doc"
        )
        .def_property_readonly(
            "polarization",
            [ureg](const BaseSource& source) {
                return py::cast(source.polarization) * ureg.attr("radian");
            },
            R"doc(
                Polarization angle of the source.

                Returns
                -------
                pint.Quantity
                    Polarization angle in radian.
            )doc"
        )
        .def_property_readonly(
            "frequency",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_frequency()) * ureg.attr("hertz");
            },
            R"doc(
                Optical frequency derived from the source wavelength.

                Returns
                -------
                pint.Quantity
                    Frequency in hertz.
            )doc"
        )
        .def_property_readonly(
            "photon_energy",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_photon_energy()) * ureg.attr("joule");
            },
            R"doc(
                Energy of a single photon at the source wavelength.

                Returns
                -------
                pint.Quantity
                    Photon energy in joule.
            )doc"
        )
        .def_property_readonly(
            "rin_linear",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_rin_linear()) / ureg.attr("hertz");
            },
            R"doc(
                Relative intensity noise converted to linear units.

                Returns
                -------
                pint.Quantity
                    Linear RIN in 1 / hertz.
            )doc"
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
                Add relative intensity noise to a signal array.

                This method perturbs an input signal according to the source RIN and
                the specified detection bandwidth. The returned values are plain scalar
                values and keep the same numerical convention as the input array.

                Parameters
                ----------
                signal_values : array-like of float
                    Signal values to perturb.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                numpy.ndarray
                    Noisy signal values as a dimensionless NumPy array.

                Notes
                -----
                This is a low level utility method. It does not attach physical units
                to the returned array.
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
            py::arg("z") = py::float_(0.0) * ureg.attr("meter"),
            R"doc(
                Evaluate the electric field amplitude at a spatial position.

                Parameters
                ----------
                x : pint.Quantity
                    X position in meter.
                y : pint.Quantity
                    Y position in meter.
                z : pint.Quantity, optional
                    Z position in meter. Defaults to 0 meter.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude in volt / meter.
            )doc"
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
            py::arg("z") = py::float_(0.0) * ureg.attr("meter"),
            R"doc(
                Evaluate optical power at a spatial position.

                Parameters
                ----------
                x : pint.Quantity
                    X position in meter.
                y : pint.Quantity
                    Y position in meter.
                z : pint.Quantity, optional
                    Z position in meter. Defaults to 0 meter.

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
            py::arg("bandwidth"),
            R"doc(
                Evaluate the electric field amplitude over multiple particle positions.

                Parameters
                ----------
                x : pint.Quantity
                    Array of X positions in meter.
                y : pint.Quantity
                    Array of Y positions in meter.
                z : pint.Quantity
                    Array of Z positions in meter.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                pint.Quantity
                    Array of electric field amplitudes in volt / meter.

                Notes
                -----
                Source level RIN can be included depending on the source configuration.
            )doc"
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

                Parameters
                ----------
                x : pint.Quantity
                    Array of X positions in meter.
                y : pint.Quantity
                    Array of Y positions in meter.
                z : pint.Quantity
                    Array of Z positions in meter.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                pint.Quantity
                    Array of optical power values in watt.

                Notes
                -----
                Depending on the source configuration, this method may include
                relative intensity noise and shot noise.
            )doc"
        )
        .def(
            "get_particle_width",
            [ureg](const BaseSource& source, const py::object& velocity) {
                std::vector<double> velocity_values = velocity.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>();
                std::vector<double> widths = source.get_particle_width(velocity_values);
                return py::cast(widths) * ureg.attr("second");
            },
            py::arg("velocity"),
            R"doc(
                Compute pulse widths induced by particle transit through the beam.

                Parameters
                ----------
                velocity : pint.Quantity
                    Particle velocities in meter / second.

                Returns
                -------
                pint.Quantity
                    Pulse widths in second.

                Notes
                -----
                These widths are temporal widths derived from the source profile and
                the particle velocities. They are intended to be used as inputs to
                pulse synthesis routines.
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
                Generate a time domain optical power signal.

                This method synthesizes a pulse train using the source specific pulse
                model. Pulse widths are computed internally from the provided particle
                velocities and the source geometry.

                Parameters
                ----------
                velocities : pint.Quantity
                    Particle velocities in meter / second.
                pulse_centers : pint.Quantity
                    Pulse center times in second.
                pulse_amplitudes : pint.Quantity
                    Pulse amplitudes in watt.
                time_array : pint.Quantity
                    Time axis in second.
                base_level : pint.Quantity
                    Baseline optical power in watt.
                bandwidth : pint.Quantity
                    Detection bandwidth in hertz.

                Returns
                -------
                pint.Quantity
                    Time domain optical power signal in watt.

                Notes
                -----
                Shot noise and relative intensity noise are included according to the
                source configuration.
            )doc"
        );

    py::class_<Gaussian, BaseSource, std::shared_ptr<Gaussian>>(
        module,
        "Gaussian",
        R"doc(
            Astigmatic Gaussian optical source.

            This class represents a Gaussian beam with independent waists along the
            Y and Z axes. The beam profile decays smoothly away from the optical axis
            and supports both spatial power evaluation and time domain pulse synthesis.

            Parameters
            ----------
            wavelength : pint.Quantity
                Optical wavelength in meter.
            optical_power : pint.Quantity
                Total optical power in watt.
            waist_y : pint.Quantity
                Beam waist along the Y axis in meter.
            waist_z : pint.Quantity
                Beam waist along the Z axis in meter.
            rin : float, optional
                Relative intensity noise in dB / Hz. Default is -120.0.
            polarization : pint.Quantity, optional
                Polarization angle in radian. Default is 0 radian.
            include_shot_noise : bool, optional
                Whether shot noise is enabled. Default is True.
            include_rin_noise : bool, optional
                Whether relative intensity noise is enabled. Default is True.
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
            py::arg("include_rin_noise") = true,
            R"doc(
                Construct an astigmatic Gaussian source.
            )doc"
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            },
            R"doc(
                Beam waist along the Y axis.

                Returns
                -------
                pint.Quantity
                    Waist along Y in meter.
            )doc"
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            },
            R"doc(
                Beam waist along the Z axis.

                Returns
                -------
                pint.Quantity
                    Waist along Z in meter.
            )doc"
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
            py::arg("waist_z"),
            R"doc(
                Update the Gaussian beam waists.

                Parameters
                ----------
                waist_y : pint.Quantity
                    New waist along the Y axis in meter.
                waist_z : pint.Quantity
                    New waist along the Z axis in meter.

                Notes
                -----
                Updating the beam waists also updates the internally stored focal
                electric field amplitude.
            )doc"
        );

    py::class_<FlatTop, BaseSource, std::shared_ptr<FlatTop>>(
        module,
        "FlatTop",
        R"doc(
            Astigmatic flat top optical source.

            This class represents a beam with approximately uniform optical power
            inside its support and sharp transitions at the beam edges. Independent
            support widths are used along the Y and Z axes.

            Parameters
            ----------
            wavelength : pint.Quantity
                Optical wavelength in meter.
            optical_power : pint.Quantity
                Total optical power in watt.
            waist_y : pint.Quantity
                Support half width along the Y axis in meter.
            waist_z : pint.Quantity
                Support half width along the Z axis in meter.
            rin : float, optional
                Relative intensity noise in dB / Hz. Default is -120.0.
            polarization : pint.Quantity, optional
                Polarization angle in radian. Default is 0 radian.
            include_shot_noise : bool, optional
                Whether shot noise is enabled. Default is True.
            include_rin_noise : bool, optional
                Whether relative intensity noise is enabled. Default is True.
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
            py::arg("include_rin_noise") = true,
            R"doc(
                Construct an astigmatic flat top source.
            )doc"
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            },
            R"doc(
                Support width along the Y axis.

                Returns
                -------
                pint.Quantity
                    Width along Y in meter.
            )doc"
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            },
            R"doc(
                Support width along the Z axis.

                Returns
                -------
                pint.Quantity
                    Width along Z in meter.
            )doc"
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
            py::arg("waist_z"),
            R"doc(
                Update the flat top support widths.

                Parameters
                ----------
                waist_y : pint.Quantity
                    New support width along the Y axis in meter.
                waist_z : pint.Quantity
                    New support width along the Z axis in meter.

                Notes
                -----
                Updating the support widths also updates the internally stored focal
                electric field amplitude.
            )doc"
        );
}
