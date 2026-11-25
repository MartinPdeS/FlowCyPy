#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <memory>

#include <utils/numpy.h>
#include <pint/pint.h>
#include "distributions.h"


namespace py = pybind11;

namespace {
std::string format_parameter(const py::object& registry, const std::string& units, double value) {
    auto quantity = py::float_(value) * registry.attr(units.c_str());
    return py::str("{:.8g}").format(quantity.attr("to_compact")()).cast<std::string>();
}

std::string format_cutoffs(const py::object& registry, const std::string& units, double low, double high) {
    std::string bounds;
    if (low != std::numeric_limits<double>::lowest()) {
        bounds += ", low_cutoff=" + format_parameter(registry, units, low);
    }
    if (high != std::numeric_limits<double>::infinity()) {
        bounds += ", high_cutoff=" + format_parameter(registry, units, high);
    }
    return bounds;
}
} // namespace

PYBIND11_MODULE(distributions, module) {
    py::object ureg = get_shared_ureg();
    py::class_<BaseDistribution, std::shared_ptr<BaseDistribution>>(module, "BaseDistribution", R"doc(
        Sample a one-dimensional particle property. sample(n_samples) returns a quantity
        array with one draw per element in the distribution's units.
    )doc")
        .def(
            "sample",
            [ureg](const BaseDistribution& self, const size_t n_samples){
                std::vector<double> output = self.sample(n_samples);
                py::array_t<double> py_output = vector_move_from_numpy(output, {output.size(),});

                return (py_output * ureg.attr(py::str(self.units)));
            },
            py::arg("n_samples")
        )
        .def(
            "proportion_within_cutoffs",
            &BaseDistribution::proportion_within_cutoffs
        )
        .def(
            "seed",
            &BaseDistribution::seed,
            py::arg("value"),
            "Seed the distribution's random number generator."
        )
        .def(
            "__repr__",
            [](const BaseDistribution& self) {
                return "BaseDistribution(units='" + self.units + "')";
            }
        )
        ;

    py::class_<Normal, BaseDistribution, std::shared_ptr<Normal>>(module, "Normal", R"doc(
        Draw normally distributed values with the specified mean and standard deviation.
        Optional low_cutoff and high_cutoff restrict the sampled interval. Supply
        compatible quantities throughout, or use numbers for dimensionless draws.
    )doc")
        .def(
            py::init(
                [](
                    const py::object& mean_py,
                    const py::object& standard_deviation_py,
                    const py::object& low_cutoff_py,
                    const py::object& high_cutoff_py
                ) {
                    py::object units;
                    double mean, standard_deviation, low_cutoff, high_cutoff;


                    if (py::hasattr(mean_py, "to_base_units")) {
                        units = mean_py.attr("to_base_units")().attr("units");
                        mean = mean_py.attr("to")(units).attr("magnitude").cast<double>();
                        standard_deviation = standard_deviation_py.attr("to")(units).attr("magnitude").cast<double>();
                        if (low_cutoff_py.is(py::none()))
                            low_cutoff = std::numeric_limits<double>::lowest();
                        else
                            low_cutoff = low_cutoff_py.attr("to")(units).attr("magnitude").cast<double>();

                        if (high_cutoff_py.is(py::none()))
                            high_cutoff = std::numeric_limits<double>::infinity();
                        else
                            high_cutoff = high_cutoff_py.attr("to")(units).attr("magnitude").cast<double>();
                    } else {
                        units = py::str("dimensionless");
                        mean = mean_py.cast<double>();
                        standard_deviation = standard_deviation_py.cast<double>();
                        if (low_cutoff_py.is(py::none()))
                            low_cutoff = std::numeric_limits<double>::lowest();
                        else
                            low_cutoff = low_cutoff_py.cast<double>();

                        if (high_cutoff_py.is(py::none()))
                            high_cutoff = std::numeric_limits<double>::infinity();
                        else
                            high_cutoff = high_cutoff_py.cast<double>();

                    }

                    std::shared_ptr<Normal> output = std::make_shared<Normal>(
                        mean,
                        standard_deviation,
                        low_cutoff,
                        high_cutoff
                    );

                    output->units = units.attr("__str__")().cast<std::string>();
                    return output;
                }
            ),
            py::arg("mean"),
            py::arg("standard_deviation"),
            py::arg("low_cutoff") = py::none(),
            py::arg("high_cutoff") = py::none(),
            "Set the mean, standard deviation and optional cutoffs in compatible units, or all as numbers."
        )
        .def_property(
            "mean",
            [ureg](const Normal& self){return py::float_(self.mean) * ureg.attr(py::str(self.units));},
            [ureg](Normal& self, const py::object& value){self.mean = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "standard_deviation",
            [ureg](const Normal& self){return py::float_(self.standard_deviation) * ureg.attr(py::str(self.units));},
            [ureg](Normal& self, const py::object& value){self.standard_deviation = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "low_cutoff",
            [ureg](const Normal& self){return py::float_(self.low_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](Normal& self, const py::object& value){self.low_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "high_cutoff",
            [ureg](const Normal& self){return py::float_(self.high_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](Normal& self, const py::object& value){self.high_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def(
            "__repr__",
            [ureg](const Normal& self) {
                return "Normal(mean=" +
                    format_parameter(ureg, self.units, self.mean) +
                    ", standard_deviation=" +
                    format_parameter(ureg, self.units, self.standard_deviation) +
                    format_cutoffs(ureg, self.units, self.low_cutoff, self.high_cutoff) + ")";
            }
        )
        ;

    py::class_<Uniform, BaseDistribution, std::shared_ptr<Uniform>>(module, "Uniform", R"doc(
        Draw uniformly between lower_bound and upper_bound. Both bounds are Pint
        quantities with compatible dimensions.
    )doc")
        .def(
            py::init(
                [](
                    const py::object& lower_bound,
                    const py::object& upper_bound
                ) {
                    py::object units = lower_bound.attr("to_base_units")().attr("units");

                    double _lower_bound = lower_bound.attr("to")(units).attr("magnitude").cast<double>();
                    double _upper_bound = upper_bound.attr("to")(units).attr("magnitude").cast<double>();

                    std::shared_ptr output = std::make_shared<Uniform>(
                        _lower_bound,
                        _upper_bound
                    );

                    output->units = units.attr("__str__")().cast<std::string>();
                    return output;
                }
            ),
            py::arg("lower_bound"),
            py::arg("upper_bound"),
            "Set the lower and upper limits using compatible quantities."
        )
        .def_property(
            "lower_bound",
            [ureg](const Uniform& self){return py::float_(self.lower_bound) * ureg.attr(py::str(self.units));},
            [ureg](Uniform& self, const py::object& value){self.lower_bound = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "upper_bound",
            [ureg](const Uniform& self){return py::float_(self.upper_bound) * ureg.attr(py::str(self.units));},
            [ureg](Uniform& self, const py::object& value){self.upper_bound = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def(
            "__repr__",
            [ureg](const Uniform& self) {
                return "Uniform(lower_bound=" +
                    format_parameter(ureg, self.units, self.lower_bound) +
                    ", upper_bound=" +
                    format_parameter(ureg, self.units, self.upper_bound) + ")";
            }
        )
        ;

    py::class_<RosinRammler, BaseDistribution, std::shared_ptr<RosinRammler>>(module, "RosinRammler", R"doc(
        Draw particle properties from a Rosin–Rammler distribution. The scale sets the
        characteristic size and shape is a dimensionless exponent. Optional cutoffs use
        the same units as scale.
    )doc")
        .def(
            py::init(
                [](
                    const py::object& scale_py,
                    const double& shape,
                    const py::object& low_cutoff_py,
                    const py::object& high_cutoff_py
                ) {

                    py::object units;
                    double scale, low_cutoff, high_cutoff;


                    if (py::hasattr(scale_py, "to_base_units")) {
                        units = scale_py.attr("to_base_units")().attr("units");
                        scale = scale_py.attr("to")(units).attr("magnitude").cast<double>();

                        if (low_cutoff_py.is(py::none()))
                            low_cutoff = std::numeric_limits<double>::lowest();
                        else
                            low_cutoff = low_cutoff_py.attr("to")(units).attr("magnitude").cast<double>();

                        if (high_cutoff_py.is(py::none()))
                            high_cutoff = std::numeric_limits<double>::infinity();
                        else
                            high_cutoff = high_cutoff_py.attr("to")(units).attr("magnitude").cast<double>();
                    } else {
                        units = py::str("dimensionless");
                        scale = scale_py.cast<double>();

                        if (low_cutoff_py.is(py::none()))
                            low_cutoff = std::numeric_limits<double>::lowest();
                        else
                            low_cutoff = low_cutoff_py.cast<double>();

                        if (high_cutoff_py.is(py::none()))
                            high_cutoff = std::numeric_limits<double>::infinity();
                        else
                            high_cutoff = high_cutoff_py.cast<double>();

                    }

                    std::shared_ptr<RosinRammler> output = std::make_shared<RosinRammler>(
                        scale,
                        shape,
                        low_cutoff,
                        high_cutoff
                    );

                    output->units = units.attr("__str__")().cast<std::string>();

                    return output;

                }
            ),
            py::arg("scale"),
            py::arg("shape"),
            py::arg("low_cutoff") = py::none(),
            py::arg("high_cutoff") = py::none(),
            "Set the characteristic scale, dimensionless shape exponent and optional cutoffs."
        )
        .def_property(
            "scale",
            [ureg](const RosinRammler& self){return py::float_(self.scale) * ureg.attr(py::str(self.units));},
            [ureg](RosinRammler& self, const py::object& value){self.scale = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "shape",
            [ureg](const RosinRammler& self){return py::float_(self.shape) * ureg.attr(py::str(self.units));},
            [ureg](RosinRammler& self, const py::object& value){self.shape = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "low_cutoff",
            [ureg](const RosinRammler& self){return py::float_(self.low_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](RosinRammler& self, const py::object& value){self.low_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "high_cutoff",
            [ureg](const RosinRammler& self){return py::float_(self.high_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](RosinRammler& self, const py::object& value){self.high_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def(
            "__repr__",
            [ureg](const RosinRammler& self) {
                return "RosinRammler(scale=" +
                    format_parameter(ureg, self.units, self.scale) +
                    ", shape=" + std::to_string(self.shape) +
                    format_cutoffs(ureg, self.units, self.low_cutoff, self.high_cutoff) + ")";
            }
        )
        ;

    py::class_<LogNormal, BaseDistribution, std::shared_ptr<LogNormal>>(module, "LogNormal", R"doc(
        Draw positive, lognormally distributed particle properties. Supply the mean,
        standard deviation and optional cutoffs as quantities with compatible units.
        The sampler uses the base-unit magnitudes of mean and standard_deviation as
        the location and scale of the underlying normal distribution in log space.
    )doc")
        .def(
            py::init(
                [](
                    const py::object& mean,
                    const py::object& standard_deviation,
                    const py::object& low_cutoff,
                    const py::object& high_cutoff
                ) {

                    py::object units = mean.attr("to_base_units")().attr("units");

                    double _mean = mean.attr("to")(units).attr("magnitude").cast<double>();
                    double _standard_deviation = standard_deviation.attr("to")(units).attr("magnitude").cast<double>();

                    double _low_cutoff, _high_cutoff;

                    if (low_cutoff.is(py::none()))
                        _low_cutoff = 1e-10; // LogNormal distribution is not defined for non-positive values, so we set the low cutoff to a very small positive number instead of negative infinity.
                    else
                        _low_cutoff = low_cutoff.attr("to")(units).attr("magnitude").cast<double>();

                    if (high_cutoff.is(py::none()))
                        _high_cutoff = std::numeric_limits<double>::infinity();
                    else
                        _high_cutoff = high_cutoff.attr("to")(units).attr("magnitude").cast<double>();

                    std::shared_ptr<LogNormal> output = std::make_shared<LogNormal>(
                        _mean,
                        _standard_deviation,
                        _low_cutoff,
                        _high_cutoff
                    );

                    output->units = units.attr("__str__")().cast<std::string>();

                    return output;
                }
            ),
            py::arg("mean"),
            py::arg("standard_deviation"),
            py::arg("low_cutoff") = py::none(),
            py::arg("high_cutoff") = py::none(),
            "Set the mean, standard deviation and optional cutoffs in compatible units."
        )
        .def_property(
            "mean",
            [ureg](const LogNormal& self){return py::float_(self.mean) * ureg.attr(py::str(self.units));},
            [ureg](LogNormal& self, const py::object& value){self.mean = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "standard_deviation",
            [ureg](const LogNormal& self){return py::float_(self.standard_deviation) * ureg.attr(py::str(self.units));},
            [ureg](LogNormal& self, const py::object& value){self.standard_deviation = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "low_cutoff",
            [ureg](const LogNormal& self){return py::float_(self.low_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](LogNormal& self, const py::object& value){self.low_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def_property(
            "high_cutoff",
            [ureg](const LogNormal& self){return py::float_(self.high_cutoff) * ureg.attr(py::str(self.units));},
            [ureg](LogNormal& self, const py::object& value){self.high_cutoff = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def(
            "__repr__",
            [ureg](const LogNormal& self) {
                return "LogNormal(mean=" +
                    format_parameter(ureg, self.units, self.mean) +
                    ", standard_deviation=" +
                    format_parameter(ureg, self.units, self.standard_deviation) +
                    format_cutoffs(ureg, self.units, self.low_cutoff, self.high_cutoff) + ")";
            }
        )
        ;

    py::class_<Delta, BaseDistribution, std::shared_ptr<Delta>>(module, "Delta", R"doc(
        Represent a fixed particle property. Every sample equals value, with its units
        preserved. A numeric value produces dimensionless samples.
    )doc")
        .def(
            py::init(
                [](
                    const py::object& object
                ) {
                    py::object units;
                    double value;
                    if (py::hasattr(object, "to_base_units")) {
                        units = object.attr("to_base_units")().attr("units");
                        value = object.attr("to")(units).attr("magnitude").cast<double>();
                    }
                    else {
                        units = py::str("dimensionless");
                        value = object.cast<double>();
                    }

                    std::shared_ptr<Delta> output = std::make_shared<Delta>(value);

                    output->units = units.attr("__str__")().cast<std::string>();

                    return output;
                }
            ),
            py::arg("value"),
            "Set the fixed value as a quantity or a dimensionless number."
        )
        .def_property(
            "value",
            [ureg](const Delta& self){return py::float_(self.value) * ureg.attr(py::str(self.units));},
            [ureg](Delta& self, const py::object& value){self.value = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        .def(
            "__repr__",
            [ureg](const Delta& self) {
                return "Delta(value=" +
                    format_parameter(ureg, self.units, self.value) + ")";
            }
        )
        ;

}
