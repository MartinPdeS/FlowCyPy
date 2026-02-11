#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <memory>

#include <utils/numpy.h>
#include <pint/pint.h>
#include "distributions.h"

namespace py = pybind11;

PYBIND11_MODULE(distributions, module) {
    py::object ureg = get_shared_ureg();
    py::class_<BaseDistribution, std::shared_ptr<BaseDistribution>>(module, "BaseDistribution")
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
        ;

    py::class_<Normal, BaseDistribution, std::shared_ptr<Normal>>(module, "Normal")
        .def(
            py::init(
                [](
                    const py::object& mean,
                    const py::object& standard_deviation,
                    const py::object& low_cutoff,
                    const py::object& high_cutoff
                ) {
                    py::object units = mean.attr("units");
                    double _low_cutoff, _high_cutoff, _mean, _standard_deviation;

                    _mean = mean.attr("magnitude").cast<double>();
                    _standard_deviation = standard_deviation.attr("to")(units).attr("magnitude").cast<double>();

                    if (low_cutoff.is(py::none()))
                        _low_cutoff = std::numeric_limits<double>::lowest();
                    else
                        _low_cutoff = low_cutoff.attr("to")(units).attr("magnitude").cast<double>();

                    if (high_cutoff.is(py::none()))
                        _high_cutoff = std::numeric_limits<double>::infinity();
                    else
                        _high_cutoff = high_cutoff.attr("to")(units).attr("magnitude").cast<double>();

                    std::shared_ptr<Normal> output = std::make_shared<Normal>(
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
            "Constructor for Normal distribution. Mean and standard deviation must be of the same type (either Length or RefractiveIndex). Cutoff must be of the same type as mean or None."
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
        ;

    py::class_<Uniform, BaseDistribution, std::shared_ptr<Uniform>>(module, "Uniform")
        .def(
            py::init(
                [](
                    const py::object& lower_bound,
                    const py::object& upper_bound
                ) {
                    py::object units = lower_bound.attr("units");

                    double _lower_bound = lower_bound.attr("magnitude").cast<double>();
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
            "Constructor for Uniform distribution. Lower and upper bounds must be of type Length."
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
        ;

    py::class_<RosinRammler, BaseDistribution, std::shared_ptr<RosinRammler>>(module, "RosinRammler")
        .def(
            py::init(
                [](
                    const py::object& scale,
                    const py::object& shape,
                    const py::object& low_cutoff,
                    const py::object& high_cutoff
                ) {
                    py::object units = scale.attr("units");

                    double _scale = scale.attr("to")(units).attr("magnitude").cast<double>();
                    double _shape = shape.attr("to")(units).attr("magnitude").cast<double>();

                    double _low_cutoff, _high_cutoff;

                    if (low_cutoff.is(py::none()))
                        _low_cutoff = std::numeric_limits<double>::lowest();
                    else
                        _low_cutoff = low_cutoff.attr("to")(units).attr("magnitude").cast<double>();

                    if (high_cutoff.is(py::none()))
                        _high_cutoff = std::numeric_limits<double>::infinity();
                    else
                        _high_cutoff = high_cutoff.attr("to")(units).attr("magnitude").cast<double>();


                    std::shared_ptr<RosinRammler> output = std::make_shared<RosinRammler>(
                        _scale,
                        _shape,
                        _low_cutoff,
                        _high_cutoff
                    );

                    output->units = units.attr("__str__")().cast<std::string>();

                    return output;

                }
            ),
            py::arg("scale"),
            py::arg("shape"),
            py::arg("low_cutoff") = py::none(),
            py::arg("high_cutoff") = py::none(),
            "Constructor for RosinRammler distribution. Scale and shape parameters must be of type Length."
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
        ;

    py::class_<LogNormal, BaseDistribution, std::shared_ptr<LogNormal>>(module, "LogNormal")
        .def(
            py::init(
                [](
                    const py::object& mean,
                    const py::object& standard_deviation,
                    const py::object& low_cutoff,
                    const py::object& high_cutoff
                ) {
                    py::object units = mean.attr("units");

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
            "Constructor for LogNormal distribution. Mean and standard deviation must be of type Length."
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
        ;

    py::class_<Delta, BaseDistribution, std::shared_ptr<Delta>>(module, "Delta")
        .def(
            py::init(
                [](
                    const py::object& value
                ) {
                    py::object units = value.attr("units");

                    double _value = value.attr("to")(units).attr("magnitude").cast<double>();


                    std::shared_ptr<Delta> output = std::make_shared<Delta>(
                        _value
                    );

                    output->units = units.attr("__str__")().cast<std::string>();

                    return output;
                }
            ),
            py::arg("value"),
            "Constructor for Delta distribution. Value must be of type Length."
        )
        .def_property(
            "value",
            [ureg](const Delta& self){return py::float_(self.value) * ureg.attr(py::str(self.units));},
            [ureg](Delta& self, const py::object& value){self.value = value.attr("to")(py::str(self.units)).cast<double>();}
        )
        ;

}
