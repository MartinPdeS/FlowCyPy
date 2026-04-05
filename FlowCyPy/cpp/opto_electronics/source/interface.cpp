#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <opto_electronics/source/source.h>
#include <pint/pint.h>
#include <limits>


namespace py = pybind11;


PYBIND11_MODULE(source, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"doc(
        Optical source models for FlowCyPy.

        This module exposes source models used to illuminate particles in the
        interrogation region of a flow cytometry simulation.
        %
        A source defines the spatial optical field, the corresponding optical
        power distribution, and optional stochastic noise contributions such as
        shot noise and relative intensity noise.
        %
        These source models are used upstream of detection and amplification and
        therefore control the optical excitation profile from which detector
        signals are ultimately derived.

        All physical inputs and outputs are Pint aware on the Python side.
    )doc";

    py::class_<BaseSource, std::shared_ptr<BaseSource>>(
        module,
        "BaseSource",
        R"doc(
            Abstract base class for optical source models.

            A :class:`BaseSource` represents an illumination model that can be
            queried in space and used to generate optical power traces in time.
            %
            Concrete subclasses implement specific beam profiles, such as
            Gaussian and flat top illumination.
            %
            In addition to deterministic field and power calculations, a source
            may optionally add stochastic fluctuations such as shot noise and
            relative intensity noise.
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
                    Source wavelength.
            )doc"
        )
        .def(
            "test_openmp",
            &BaseSource::test_openmp,
            R"doc(
                Run the internal OpenMP test routine.

                This method is primarily intended for debugging or validating the
                parallel execution environment used by the C++ backend.
            )doc"
        )
        .def_readwrite(
            "include_shot_noise",
            &BaseSource::include_shot_noise,
            R"doc(
                Whether shot noise should be included in source generated power signals.
            )doc"
        )
        .def_readwrite(
            "include_rin_noise",
            &BaseSource::include_rin_noise,
            R"doc(
                Whether relative intensity noise should be included in source generated signals.
            )doc"
        )
        .def_property(
            "rin",
            [ureg](const BaseSource& source) -> py::object {
                if (std::isnan(source.rin)) {
                    return py::none();
                } else {
                    return py::cast(source.rin) * ureg.attr("dB_per_Hz");
                }
            },
            [](BaseSource& source, const py::object& rin) {
                if (rin.is_none()) {
                    source.rin = std::numeric_limits<double>::quiet_NaN();
                } else {
                    source.rin = rin.attr("to")("dB_per_Hz").attr("magnitude").cast<double>();
                }
            },
            R"doc(
                Relative intensity noise level of the source.

                This quantity is expressed in decibel per hertz.
                %
                Setting this attribute to ``None`` removes the stored RIN value.
            )doc"
        )
        .def_property(
            "optical_power",
            [ureg](const BaseSource& source) {
                return py::cast(source.optical_power) * ureg.attr("watt");
            },
            [ureg](BaseSource& source, const py::object& power) {
                source.optical_power = power.attr("to")("watt").attr("magnitude").cast<double>();
                source.update_amplitude();
            },
            R"doc(
                Total optical power carried by the source.

                Updating this value also updates the corresponding field
                amplitude used internally by the source model.
            )doc"
        )
        .def_property_readonly(
            "amplitude",
            [ureg](const BaseSource& source) {
                return py::cast(source.amplitude) * ureg.attr("volt / meter");
            },
            R"doc(
                Peak electric field amplitude associated with the current optical power.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude.
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
                    Polarization angle in radians.
            )doc"
        )
        .def_property_readonly(
            "frequency",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_frequency()) * ureg.attr("hertz");
            },
            R"doc(
                Optical frequency corresponding to the current wavelength.

                Returns
                -------
                pint.Quantity
                    Optical frequency.
            )doc"
        )
        .def_property(
            "bandwidth",
            [ureg](const BaseSource& source) {
                return py::cast(source.bandwidth) * ureg.attr("hertz");
            },
            [ureg](BaseSource& source, const py::object& bandwidth) {
                source.bandwidth = bandwidth.attr("to")("hertz").attr("magnitude").cast<double>();
            },
            R"doc(
                Optional source bandwidth used in bandwidth dependent noise calculations.

                This value is typically used together with the source RIN model.
            )doc"
        )
        .def_property_readonly(
            "photon_energy",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_photon_energy()) * ureg.attr("joule");
            },
            R"doc(
                Energy of a single photon at the current wavelength.

                Returns
                -------
                pint.Quantity
                    Photon energy.
            )doc"
        )
        .def_property_readonly(
            "rin_linear",
            [ureg](const BaseSource& source) {
                return py::cast(source.get_rin_linear()) / ureg.attr("hertz");
            },
            R"doc(
                Relative intensity noise expressed on a linear scale.

                Returns
                -------
                pint.Quantity
                    Linear RIN spectral density.
            )doc"
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
                Add shot noise to an optical power trace.

                Parameters
                ----------
                signal : pint.Quantity
                    Input optical power trace.
                time : pint.Quantity
                    Time array associated with the signal samples.

                Returns
                -------
                pint.Quantity
                    Optical power trace with shot noise added.

                Notes
                -----
                The time array is used to infer the sample spacing and therefore
                the effective photon counting interval for each sample.
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
                Add relative intensity noise to an optical power trace.

                Parameters
                ----------
                signal : pint.Quantity
                    Input optical power trace.

                Returns
                -------
                pint.Quantity
                    Optical power trace with source RIN added.
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
                Apply a common RIN realization to all detector channels in a signal dictionary.

                Parameters
                ----------
                signal_dict : dict
                    Dictionary containing a ``"Time"`` entry and one or more
                    detector power traces.

                Returns
                -------
                dict
                    New signal dictionary in which all detector channels have
                    been perturbed by the same source RIN realization.

                Notes
                -----
                This method is useful when modeling a shared illumination source
                whose intensity fluctuations are seen simultaneously by all
                detector channels.
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
                Evaluate the source electric field amplitude at a single spatial position.

                Parameters
                ----------
                x : pint.Quantity
                    Axial position.
                y : pint.Quantity
                    Transverse position along the y axis.
                z : pint.Quantity, optional
                    Transverse position along the z axis.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude at the requested location.
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
                Evaluate the optical power density surrogate at a single spatial position.

                Parameters
                ----------
                x : pint.Quantity
                    Axial position.
                y : pint.Quantity
                    Transverse position along the y axis.
                z : pint.Quantity, optional
                    Transverse position along the z axis.

                Returns
                -------
                pint.Quantity
                    Optical power at the requested location.
            )doc"
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
            py::arg("z"),
            R"doc(
                Evaluate the source electric field amplitude along a trajectory.

                Parameters
                ----------
                x : pint.Quantity
                    Array of axial positions.
                y : pint.Quantity
                    Array of y positions.
                z : pint.Quantity
                    Array of z positions.

                Returns
                -------
                pint.Quantity
                    Electric field amplitude sampled along the requested trajectory.
            )doc"
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
            py::arg("time_step"),
            R"doc(
                Generate an optical power trace along a trajectory.

                Parameters
                ----------
                x : pint.Quantity
                    Array of axial positions.
                y : pint.Quantity
                    Array of y positions.
                z : pint.Quantity
                    Array of z positions.
                time_step : pint.Quantity
                    Sampling interval of the generated signal.

                Returns
                -------
                pint.Quantity
                    Optical power trace sampled along the requested trajectory.

                Notes
                -----
                This method may incorporate source noise depending on the current
                source configuration.
            )doc"
        )
        .def(
            "get_particle_width",
            [ureg](const BaseSource& source, const py::object& velocity) {
                std::vector<double> velocity_values =
                    velocity.attr("to")("meter / second").attr("magnitude").cast<std::vector<double>>();

                std::vector<double> widths = source.get_particle_width(velocity_values);

                return py::cast(widths) * ureg.attr("second");
            },
            py::arg("velocity"),
            R"doc(
                Estimate the temporal pulse width associated with particle transit through the beam.

                Parameters
                ----------
                velocity : pint.Quantity
                    Particle velocity or array of velocities.

                Returns
                -------
                pint.Quantity
                    Estimated pulse width in time for each provided velocity.
            )doc"
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
                Generate a gamma distributed optical power trace.

                Parameters
                ----------
                time_array : pint.Quantity
                    Time samples defining the output trace.
                shape : float
                    Shape parameter of the gamma model.
                scale : pint.Quantity
                    Scale parameter expressed in optical power units.
                mean_velocity : pint.Quantity
                    Mean particle velocity used to relate the intrinsic source
                    kernel to time.

                Returns
                -------
                pint.Quantity
                    Gamma distributed optical power trace.
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
            py::arg("base_level"),
            R"doc(
                Generate a synthetic pulse train from particle transit parameters.

                Parameters
                ----------
                velocities : pint.Quantity
                    Particle velocities.
                pulse_centers : pint.Quantity
                    Pulse center times.
                pulse_amplitudes : pint.Quantity
                    Pulse amplitudes expressed as optical power.
                time_array : pint.Quantity
                    Time samples of the output signal.
                base_level : pint.Quantity
                    Constant optical background level added to the signal.

                Returns
                -------
                pint.Quantity
                    Optical power trace containing the generated pulses.
            )doc"
        );

    py::class_<Gaussian, BaseSource, std::shared_ptr<Gaussian>>(
        module,
        "Gaussian",
        R"doc(
            Gaussian beam source model.

            This source uses a Gaussian transverse intensity profile with
            potentially different waists along the y and z directions.
            %
            It is appropriate for focused illumination geometries in which the
            field amplitude decays smoothly away from the beam center.
        )doc"
        )
        .def(
            py::init(
                [ureg](
                    const py::object& wavelength,
                    const py::object& optical_power,
                    const py::object& waist_y,
                    const py::object& waist_z,
                    const py::object& rin,
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

                    const double rin_value = rin.is_none()
                        ? std::numeric_limits<double>::quiet_NaN()
                        : rin.attr("to")("dB_per_Hz").attr("magnitude").cast<double>();

                    return std::make_shared<Gaussian>(
                        wavelength_meter,
                        rin_value,
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
            py::arg("rin") = py::none(),
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("bandwidth") = py::none(),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true,
            py::arg("debug_mode") = false,
            R"doc(
                Initialize a Gaussian beam source.

                Parameters
                ----------
                wavelength : pint.Quantity
                    Optical wavelength.
                optical_power : pint.Quantity
                    Total optical power.
                waist_y : pint.Quantity
                    Beam waist along the y direction.
                waist_z : pint.Quantity
                    Beam waist along the z direction.
                rin : pint.Quantity or None, optional
                    Relative intensity noise level in decibel per hertz.
                polarization : pint.Quantity, optional
                    Polarization angle.
                bandwidth : pint.Quantity or None, optional
                    Source bandwidth used in bandwidth dependent noise models.
                include_shot_noise : bool, optional
                    Whether shot noise should be included when generating noisy signals.
                include_rin_noise : bool, optional
                    Whether relative intensity noise should be included when generating noisy signals.
                debug_mode : bool, optional
                    Whether to enable internal debug behavior in the C++ backend.
            )doc"
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            },
            R"doc(
                Gaussian beam waist along the y direction.
            )doc"
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const Gaussian& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            },
            R"doc(
                Gaussian beam waist along the z direction.
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
                    New beam waist along the y direction.
                waist_z : pint.Quantity
                    New beam waist along the z direction.
            )doc"
        );

    py::class_<FlatTop, BaseSource, std::shared_ptr<FlatTop>>(
        module,
        "FlatTop",
        R"doc(
            Flat top beam source model.

            This source approximates an illumination profile with a more uniform
            intensity across the beam support than a Gaussian beam.
            %
            It is useful when modeling excitation geometries intended to produce
            a relatively homogeneous optical field over the interrogation region.
        )doc"
    )
        .def(
            py::init(
                [ureg](
                    const py::object& wavelength,
                    const py::object& optical_power,
                    const py::object& waist_y,
                    const py::object& waist_z,
                    const py::object& rin,
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

                    const double rin_value = rin.is_none()
                        ? std::numeric_limits<double>::quiet_NaN()
                        : rin.attr("to")("dB_per_Hz").attr("magnitude").cast<double>();

                    return std::make_shared<FlatTop>(
                        wavelength_meter,
                        rin_value,
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
            py::arg("rin") = py::none(),
            py::arg("polarization") = py::float_(0.0) * ureg.attr("radian"),
            py::arg("bandwidth") = py::none(),
            py::arg("include_shot_noise") = true,
            py::arg("include_rin_noise") = true,
            py::arg("debug_mode") = false,
            R"doc(
                Initialize a flat top beam source.

                Parameters
                ----------
                wavelength : pint.Quantity
                    Optical wavelength.
                optical_power : pint.Quantity
                    Total optical power.
                waist_y : pint.Quantity
                    Effective beam half width along the y direction.
                waist_z : pint.Quantity
                    Effective beam half width along the z direction.
                rin : pint.Quantity or None, optional
                    Relative intensity noise level in decibel per hertz.
                polarization : pint.Quantity, optional
                    Polarization angle.
                bandwidth : pint.Quantity or None, optional
                    Source bandwidth used in bandwidth dependent noise models.
                include_shot_noise : bool, optional
                    Whether shot noise should be included when generating noisy signals.
                include_rin_noise : bool, optional
                    Whether relative intensity noise should be included when generating noisy signals.
                debug_mode : bool, optional
                    Whether to enable internal debug behavior in the C++ backend.
            )doc"
        )
        .def_property_readonly(
            "waist_y",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_y) * ureg.attr("meter");
            },
            R"doc(
                Effective flat top beam extent along the y direction.
            )doc"
        )
        .def_property_readonly(
            "waist_z",
            [ureg](const FlatTop& source) {
                return py::cast(source.waist_z) * ureg.attr("meter");
            },
            R"doc(
                Effective flat top beam extent along the z direction.
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
                Update the effective flat top beam extents.

                Parameters
                ----------
                waist_y : pint.Quantity
                    New beam extent along the y direction.
                waist_z : pint.Quantity
                    New beam extent along the z direction.
            )doc"
        );
}
