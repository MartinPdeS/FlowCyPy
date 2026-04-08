#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <string>
#include <vector>
#include <limits>
#include <cmath>

#include "detector.h"
#include <utils/casting.h>
#include <pint/pint.h>

namespace py = pybind11;


namespace {

py::object as_angle_quantity(
    const py::object& unit_registry,
    const double value
) {
    return (py::float_(value) * unit_registry.attr("radian")).attr("to_compact")();
}


py::object as_frequency_quantity(
    const py::object& unit_registry,
    const double value
) {
    return (py::float_(value) * unit_registry.attr("hertz")).attr("to_compact")();
}


py::object as_responsivity_quantity(
    const py::object& unit_registry,
    const double value
) {
    return (
        py::float_(value) *
        unit_registry.attr("ampere") /
        unit_registry.attr("watt")
    ).attr("to_compact")();
}


}  // namespace


PYBIND11_MODULE(detector, module) {
    py::object unit_registry = get_shared_ureg();

    module.doc() = R"pbdoc(
        Detector models for FlowCyPy.

        This module exposes the detector component used in the opto electronic
        acquisition chain of a flow cytometry simulation.

        A detector defines the geometric collection configuration of a channel,
        together with the electrical conversion from collected optical power to
        detector current through its responsivity.

        The detector can also apply bandwidth dependent dark current noise to a
        current trace.

        Quantities are expected to be provided as Pint compatible values:

        - angles in units compatible with radians
        - current in units compatible with amperes
        - current noise density in units compatible with ampere per square root hertz
        - bandwidth in units compatible with hertz
        - responsivity in units compatible with ampere per watt
    )pbdoc";

    py::class_<Detector>(
        module,
        "Detector",
        R"pbdoc(
            Detector model for a flow cytometry acquisition channel.

            A :class:`Detector` represents the collection geometry and electrical
            response of a single detector channel.

            It stores the angular placement of the detector, its numerical
            aperture, optional obscuration by a central cache, the current
            responsivity, the dark current level, an optional additive current
            noise density, and an optional bandwidth used for bandwidth
            dependent noise calculations.

            In a typical FlowCyPy workflow, detector objects are assembled into an
            :class:`OptoElectronics` configuration and are used to convert channel
            specific optical power into detector current prior to amplification and
            digitization.

            Notes
            -----
            This class represents the detector level response of the acquisition
            chain.

            It does not model downstream analog amplification or digitization.
            Those stages are handled by the amplifier and digitizer components.
        )pbdoc"
    )
        .def(
            py::init([](
                const py::object& phi_angle,
                const double numerical_aperture,
                const double cache_numerical_aperture,
                const py::object& gamma_angle,
                const int sampling,
                const py::object& responsivity,
                const py::object& dark_current,
                const py::object& current_noise_density,
                const py::object& bandwidth,
                const py::object& name
            ) {
                const double phi_angle_value = Casting::cast_py_to_scalar<double>(
                    phi_angle,
                    "phi_angle",
                    "radian"
                );

                const double gamma_angle_value = gamma_angle.is_none()
                    ? 0.0
                    : Casting::cast_py_to_scalar<double>(
                        gamma_angle,
                        "gamma_angle",
                        "radian"
                    );

                const double responsivity_value = responsivity.is_none()
                    ? 1.0
                    : Casting::cast_py_to_scalar<double>(
                        responsivity,
                        "responsivity",
                        "ampere / watt"
                    );

                const double dark_current_value = dark_current.is_none()
                    ? 0.0
                    : Casting::cast_py_to_scalar<double>(
                        dark_current,
                        "dark_current",
                        "ampere"
                    );

                const double current_noise_density_value =
                    current_noise_density.is_none()
                    ? 0.0
                    : Casting::cast_py_to_scalar<double>(
                        current_noise_density,
                        "current_noise_density",
                        "ampere / hertz**0.5"
                    );

                const double bandwidth_value = bandwidth.is_none()
                    ? std::numeric_limits<double>::quiet_NaN()
                    : Casting::cast_py_to_scalar<double>(
                        bandwidth,
                        "bandwidth",
                        "hertz"
                    );

                const std::string detector_name = name.is_none()
                    ? std::string("")
                    : py::cast<std::string>(name);

                return Detector(
                    phi_angle_value,
                    numerical_aperture,
                    cache_numerical_aperture,
                    gamma_angle_value,
                    sampling,
                    responsivity_value,
                    dark_current_value,
                    current_noise_density_value,
                    bandwidth_value,
                    detector_name
                );
            }),
            py::arg("phi_angle"),
            py::arg("numerical_aperture"),
            py::arg("cache_numerical_aperture") = 0.0,
            py::arg("gamma_angle") = py::none(),
            py::arg("sampling") = 200,
            py::arg("responsivity") = py::none(),
            py::arg("dark_current") = py::none(),
            py::arg("current_noise_density") = py::none(),
            py::arg("bandwidth") = py::none(),
            py::arg("name") = py::none(),
            R"pbdoc(
                Initialize a detector channel.

                Parameters
                ----------
                phi_angle : pint.Quantity
                    Azimuthal detector angle.
                numerical_aperture : float
                    Numerical aperture of the detector collection cone.
                cache_numerical_aperture : float, optional
                    Numerical aperture of the central obscuration. A value of zero means that no central cache or obscuration is applied.
                gamma_angle : pint.Quantity or None, optional
                    Longitudinal detector angle. If omitted, a value of zero is used.
                sampling : int, optional
                    Number of internal sampling points used to represent the
                    detector support.
                responsivity : pint.Quantity or None, optional
                    Detector responsivity in ampere per watt. If omitted, a unit responsivity of ``1 ampere / watt`` is used.
                dark_current : pint.Quantity or None, optional
                    Mean detector dark current. If omitted, a value of ``0 ampere`` is used.
                current_noise_density : pint.Quantity or None, optional
                    Additional detector current-noise density in ``ampere / sqrt(hertz)``. If omitted, a value of ``0 ampere / sqrt(hertz)`` is used.
                bandwidth : pint.Quantity or None, optional
                    Detector bandwidth used by bandwidth dependent noise calculations. If omitted, no bandwidth is stored on the detector.
                name : str or None, optional
                    Detector name. If omitted, the detector is created with an empty name.

                Notes
                -----
                The detector bandwidth stored here acts as a default for methods
                such as :meth:`apply_dark_current_noise`. A method level bandwidth argument, when provided, overrides the
                stored detector bandwidth.
            )pbdoc"
        )

        .def_property(
            "phi_angle",
            [unit_registry](const Detector& self) -> py::object {
                return as_angle_quantity(unit_registry, self.phi_angle);
            },
            [](Detector& self, const py::object& value) {
                self.phi_angle = Casting::cast_py_to_scalar<double>(
                    value,
                    "phi_angle",
                    "radian"
                );

                if (std::isnan(self.phi_angle)) {
                    throw std::invalid_argument("Detector phi_angle must be defined.");
                }
            },
            R"pbdoc(
                Azimuthal detector angle.

                This angle defines the detector position around the optical axis
                in the transverse plane.
            )pbdoc"
        )

        .def_readwrite(
            "numerical_aperture",
            &Detector::numerical_aperture,
            R"pbdoc(
                Numerical aperture of the detector collection cone.

                Larger values correspond to a wider collection angle and therefore
                a larger accepted range of scattered directions.
            )pbdoc"
        )

        .def_readwrite(
            "cache_numerical_aperture",
            &Detector::cache_numerical_aperture,
            R"pbdoc(
                Numerical aperture of the central obscuration.

                This value can be used to represent a masked or blocked central
                region in the detector collection geometry, such as the obscuration
                often present in forward scatter configurations.
            )pbdoc"
        )

        .def_property(
            "gamma_angle",
            [unit_registry](const Detector& self) -> py::object {
                return as_angle_quantity(unit_registry, self.gamma_angle);
            },
            [](Detector& self, const py::object& value) {
                self.gamma_angle = Casting::cast_py_to_scalar<double>(
                    value,
                    "gamma_angle",
                    "radian"
                );

                if (std::isnan(self.gamma_angle)) {
                    throw std::invalid_argument("Detector gamma_angle must be defined.");
                }
            },
            R"pbdoc(
                Longitudinal detector angle.

                This angle complements :attr:`phi_angle` and defines the detector
                orientation relative to the optical axis.
            )pbdoc"
        )

        .def_readwrite(
            "sampling",
            &Detector::sampling,
            R"pbdoc(
                Internal sampling density used to represent the detector support.

                Increasing this value may improve geometric resolution at the cost
                of additional computation.
            )pbdoc"
        )

        .def_property(
            "responsivity",
            [unit_registry](const Detector& self) -> py::object {
                return as_responsivity_quantity(unit_registry, self.responsivity);
            },
            [](Detector& self, const py::object& value) {
                self.responsivity = Casting::cast_py_to_scalar<double>(
                    value,
                    "responsivity",
                    "ampere / watt"
                );

                if (std::isnan(self.responsivity) || self.responsivity < 0.0) {
                    throw std::invalid_argument(
                        "Detector responsivity must be non negative."
                    );
                }
            },
            R"pbdoc(
                Detector responsivity.

                Responsivity defines the conversion factor between collected optical
                power and detector current.
            )pbdoc"
        )

        .def_property(
            "dark_current",
            [unit_registry](const Detector& self) -> py::object {
                return (py::float_(self.dark_current) * unit_registry.attr("ampere")).attr("to_compact")();
            },
            [](Detector& self, const py::object& value) {
                self.dark_current = Casting::cast_py_to_scalar<double>(
                    value,
                    "dark_current",
                    "ampere"
                );

                if (std::isnan(self.dark_current) || self.dark_current < 0.0) {
                    throw std::invalid_argument(
                        "Detector dark_current must be non negative."
                    );
                }
            },
            R"pbdoc(
                Mean detector dark current.

                This value is used to model detector dark-current shot noise and
                the mean dark-current offset when a valid bandwidth is available.
            )pbdoc"
        )

        .def_property(
            "current_noise_density",
            [unit_registry](const Detector& self) -> py::object {
                return (
                    py::float_(self.current_noise_density) *
                    unit_registry.attr("ampere") /
                    unit_registry.attr("sqrt_hertz")
                ).attr("to_compact")();
            },
            [](Detector& self, const py::object& value) {
                self.current_noise_density = Casting::cast_py_to_scalar<double>(
                    value,
                    "current_noise_density",
                    "ampere / hertz**0.5"
                );

                if (
                    std::isnan(self.current_noise_density) ||
                    self.current_noise_density < 0.0
                ) {
                    throw std::invalid_argument(
                        "Detector current_noise_density must be non negative."
                    );
                }
            },
            R"pbdoc(
                Detector current-noise density.

                This value represents an additive current-noise spectral density
                expressed in ``ampere / sqrt(hertz)``.
            )pbdoc"
        )

        .def_property(
            "bandwidth",
            [unit_registry](const Detector& self) -> py::object {
                if (std::isnan(self.bandwidth)) {
                    return py::none();
                }

                return as_frequency_quantity(unit_registry, self.bandwidth);
            },
            [](Detector& self, const py::object& value) {
                self.bandwidth = Casting::cast_py_to_optional_scalar<double>(
                    value,
                    "bandwidth",
                    "hertz"
                );

                if (!std::isnan(self.bandwidth) && self.bandwidth <= 0.0) {
                    throw std::invalid_argument(
                        "Detector bandwidth must be strictly positive when provided."
                    );
                }
            },
            R"pbdoc(
                Optional detector bandwidth.

                When defined, this bandwidth is used as the default bandwidth for
                bandwidth dependent detector operations. Setting this attribute to ``None`` removes the stored bandwidth.
            )pbdoc"
        )

        .def_readwrite(
            "name",
            &Detector::name,
            R"pbdoc(
                Detector identifier.

                This name is typically used to label detector channels in the
                acquisition pipeline and in exported results.
            )pbdoc"
        )

        .def(
            "has_bandwidth",
            &Detector::has_bandwidth,
            R"pbdoc(
                Return whether the detector has a stored bandwidth.

                Returns
                -------
                bool
                    ``True`` if :attr:`bandwidth` is defined, otherwise ``False``.
            )pbdoc"
        )

        .def(
            "clear_bandwidth",
            &Detector::clear_bandwidth,
            R"pbdoc(
                Remove the stored detector bandwidth.

                After calling this method, bandwidth dependent operations require an
                explicit method level bandwidth argument in order to use a finite
                bandwidth.
            )pbdoc"
        )

        .def(
            "apply_dark_current_noise",
            [unit_registry](
                const Detector& self,
                const py::object& signal,
                const py::object& bandwidth
            ) -> py::object {
                const std::vector<double> signal_vector =
                    Casting::cast_py_to_vector<double>(signal, "signal", "ampere");

                const double bandwidth_value = bandwidth.is_none()
                    ? std::numeric_limits<double>::quiet_NaN()
                    : Casting::cast_py_to_scalar<double>(
                        bandwidth,
                        "bandwidth",
                        "hertz"
                    );

                const std::vector<double> output_signal =
                    self.apply_dark_current_noise(signal_vector, bandwidth_value);

                return py::array_t<double>(output_signal.size(), output_signal.data()) * unit_registry.attr("ampere");
            },
            py::arg("signal"),
            py::arg("bandwidth") = py::none(),
            R"pbdoc(
                Add dark current noise to a detector current signal.

                Dark current noise depends on the effective bandwidth used for the
                calculation. The bandwidth is resolved in the following order:

                1. the method argument ``bandwidth``, when provided
                2. the detector attribute :attr:`bandwidth`
                3. no finite bandwidth, in which case the input signal is returned unchanged

                Parameters
                ----------
                signal : pint.Quantity
                    Input current trace expressed in amperes.
                bandwidth : pint.Quantity or None, optional
                    Bandwidth to use for the noise calculation. If omitted, the detector stored bandwidth is used.

                Returns
                -------
                pint.Quantity
                    Output current trace with dark current noise added.

                Notes
                -----
                This method operates directly on detector current, before any
                downstream amplifier or digitizer stage.

                The total RMS current noise is computed from the quadrature sum of
                dark-current shot noise and additive current-noise density.
            )pbdoc"
        )

        .def(
            "__repr__",
            [](const Detector& self) {
                return self.repr();
            }
        );
}
