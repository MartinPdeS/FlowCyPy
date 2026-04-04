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


py::object as_current_quantity(
    const py::object& unit_registry,
    const double value
) {
    return (py::float_(value) * unit_registry.attr("ampere")).attr("to_compact")();
}


py::object as_current_quantity(
    const py::object& unit_registry,
    const std::vector<double>& values
) {
    return py::array_t<double>(values.size(), values.data()) * unit_registry.attr("ampere");
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
        FlowCyPy detector interface.

        This module exposes a detector model for flow cytometry simulations.
        The detector stores geometric and electrical properties and provides
        bandwidth dependent signal operations such as dark current noise.

        Angles are expected to be Pint quantities compatible with radians.
        Currents are expected to be Pint quantities compatible with amperes.
        Frequencies are expected to be Pint quantities compatible with hertz.
        Responsivity is expected to be compatible with ampere / watt.
    )pbdoc";

    py::class_<Detector>(
        module,
        "Detector",
        R"pbdoc(
            Represents a photodetector for flow cytometry simulations.

            This class simulates a photodetector that captures light scattering
            signals in a flow cytometry setup. It models detector response by
            incorporating detector specific transformations and optional noise
            sources into the signal processing workflow.

            The detector supports bandwidth dependent operations such as dark
            current noise modeling. The bandwidth can be provided explicitly
            to each method, or stored directly on the detector instance through
            the ``bandwidth`` attribute. If neither is defined, the corresponding
            bandwidth dependent computation is skipped.

            Parameters
            ----------
            phi_angle : pint.Quantity
                Primary azimuthal angle of incidence.
            numerical_aperture : float
                Numerical aperture of the detector.
            cache_numerical_aperture : float, default=0
                Numerical aperture of the caching element placed in front of
                the detector.
            gamma_angle : pint.Quantity, default=0 degree
                Complementary longitudinal angle of incidence.
            sampling : int, default=200
                Number of spatial sampling points used to define the detector support.
            responsivity : pint.Quantity, default=1 ampere / watt
                Detector responsivity.
            dark_current : pint.Quantity, default=0 ampere
                Detector dark current.
            bandwidth : pint.Quantity or None, default=None
                Detector bandwidth.
            name : str or None, default=None
                Unique identifier for the detector. If ``None``, a unique identifier
                derived from the object instance is generated.
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
            py::arg("bandwidth") = py::none(),
            py::arg("name") = py::none(),
            R"pbdoc(
                Initialize a detector.
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
            }
        )

        .def_readwrite(
            "numerical_aperture",
            &Detector::numerical_aperture
        )

        .def_readwrite(
            "cache_numerical_aperture",
            &Detector::cache_numerical_aperture
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
            }
        )

        .def_readwrite(
            "sampling",
            &Detector::sampling
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
            }
        )

        .def_property(
            "dark_current",
            [unit_registry](const Detector& self) -> py::object {
                return as_current_quantity(unit_registry, self.dark_current);
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
            }
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
            }
        )

        .def_readwrite(
            "name",
            &Detector::name
        )

        .def(
            "has_bandwidth",
            &Detector::has_bandwidth,
            R"pbdoc(
                Return whether a detector bandwidth is defined.

                Returns
                -------
                bool
                    ``True`` if ``bandwidth`` is set, otherwise ``False``.
            )pbdoc"
        )

        .def(
            "clear_bandwidth",
            &Detector::clear_bandwidth,
            R"pbdoc(
                Clear the stored detector bandwidth.
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
                    Casting::cast_py_to_vector<double>(signal, "ampere");

                const double bandwidth_value = bandwidth.is_none()
                    ? std::numeric_limits<double>::quiet_NaN()
                    : Casting::cast_py_to_scalar<double>(
                        bandwidth,
                        "bandwidth",
                        "hertz"
                    );

                const std::vector<double> output_signal =
                    self.apply_dark_current_noise(signal_vector, bandwidth_value);

                return as_current_quantity(unit_registry, output_signal);
            },
            py::arg("signal"),
            py::arg("bandwidth") = py::none(),
            R"pbdoc(
                Apply dark current noise directly to a detector current signal.

                Dark current noise is bandwidth dependent. The method first resolves
                the effective bandwidth from the method argument or from
                ``self.bandwidth``. If no bandwidth is available, the input signal
                is returned unchanged.

                Parameters
                ----------
                signal : pint.Quantity
                    Input detector current signal.
                bandwidth : pint.Quantity or None, optional
                    Signal bandwidth. If ``None``, ``self.bandwidth`` is used. If both
                    are undefined, dark current noise is skipped.

                Returns
                -------
                pint.Quantity
                    Signal with dark current noise added.
            )pbdoc"
        )

        .def(
            "__repr__",
            [](const Detector& self) {
                return self.repr();
            }
        );
}
