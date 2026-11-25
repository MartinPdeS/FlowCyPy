#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "scatterer_collection.h"

namespace py = pybind11;

PYBIND11_MODULE(scatterer_collection, module) {
    module.doc() = R"pdoc(
        C++-accelerated containers for scatterer populations.

        The :class:`ScattererCollection` stores the populations present in a
        simulated sample and provides common concentration operations. Population
        objects remain shared with Python, so changing a population through the
        collection changes the original object as well.
    )pdoc";

    py::class_<ScattererCollection, std::shared_ptr<ScattererCollection>>(
        module,
        "ScattererCollection",
        R"pdoc(
            Collection of particle populations used by a flow-cytometry simulation.

            The collection is deliberately lightweight: it stores population
            objects and applies operations that affect the sample as a whole.
            Concentrations are exposed as Pint quantities in particle / liter,
            while the C++ implementation stores their magnitudes in SI units.

            Parameters
            ----------
            populations : sequence of BasePopulation, optional
                Initial populations. The default is an empty collection.

            Notes
            -----
            Population objects are held by shared reference. Consequently,
            ``collection.dilute(2)`` also updates the concentration observed on
            each population object passed to the constructor.
        )pdoc"
    )
        .def(
            py::init([](const py::object& values) {
                if (values.is_none()) {
                    return std::make_shared<ScattererCollection>();
                }
                return std::make_shared<ScattererCollection>(
                    values.cast<std::vector<std::shared_ptr<BasePopulation>>>()
                );
            }),
            py::arg("populations") = py::none(),
            R"pdoc(
                Create a collection from an optional sequence of populations.

                Parameters
                ----------
                populations : sequence of BasePopulation, optional
                    Populations to store initially.
            )pdoc"
        )
        .def_property(
            "populations",
            [](const ScattererCollection& self) { return self.populations; },
            [](ScattererCollection& self,
               const std::vector<std::shared_ptr<BasePopulation>>& values) {
                self.populations = values;
            },
            R"pdoc(
                Populations stored in the collection.

                Getting this property returns a Python list. Assigning a list
                replaces the collection contents; population objects themselves
                continue to be shared with Python.
            )pdoc"
        )
        .def(
            "get_population_ratios",
            &ScattererCollection::get_population_ratios,
            R"pdoc(
                Return each population's fraction of the total concentration.

                Returns
                -------
                list of float
                    One dimensionless ratio per population, in collection order.

                Raises
                ------
                ValueError
                    If the total concentration is zero.
            )pdoc"
        )
        .def(
            "add_population",
            [](ScattererCollection& self, const py::args& values)
                -> ScattererCollection& {
                std::vector<std::shared_ptr<BasePopulation>> populations;
                populations.reserve(values.size());
                for (const py::handle& value : values) {
                    populations.push_back(value.cast<std::shared_ptr<BasePopulation>>());
                }
                return self.add_population(populations);
            },
            py::return_value_policy::reference_internal,
            R"pdoc(
                Append one or more populations.

                Parameters
                ----------
                *population : BasePopulation
                    One or more population objects to append.

                Returns
                -------
                ScattererCollection
                    This collection, allowing calls to be chained.
            )pdoc"
        )
        .def_property_readonly(
            "concentrations",
            [](const ScattererCollection& self) {
                py::object ureg = py::module_::import("FlowCyPy.units").attr("ureg");
                py::list output;
                for (double value : self.concentrations()) {
                    output.append(py::float_(value) * ureg.attr("particle / liter"));
                }
                return output;
            },
            R"pdoc(
                Concentration of each population.

                Returns
                -------
                list of pint.Quantity
                    Concentrations in particle / liter, in collection order.
            )pdoc"
        )
        .def(
            "set_concentrations",
            [](ScattererCollection& self, const py::object& values) {
                if (py::isinstance<py::list>(values) || py::isinstance<py::tuple>(values)) {
                    std::vector<double> magnitudes;
                    for (const py::handle& value : values) {
                        magnitudes.push_back(
                            value.attr("to")("particle / liter")
                                .attr("magnitude").cast<double>()
                        );
                    }
                    self.set_concentrations(magnitudes);
                    return;
                }

                const double magnitude = values.attr("to")("particle / liter")
                    .attr("magnitude").cast<double>();
                self.set_concentrations(magnitude);
            },
            py::arg("values"),
            R"pdoc(
                Set population concentrations.

                Parameters
                ----------
                values : pint.Quantity or sequence of pint.Quantity
                    A single concentration applied to every population, or one
                    concentration per population. Values must be convertible to
                    particle / liter.

                Raises
                ------
                ValueError
                    If a sequence has the wrong length or a value has incompatible
                    units.
            )pdoc"
        )
        .def(
            "dilute",
            &ScattererCollection::dilute,
            py::arg("factor"),
            R"pdoc(
                Divide every population concentration by ``factor``.

                Parameters
                ----------
                factor : float
                    Finite, strictly positive dilution factor.

                Raises
                ------
                ValueError
                    If ``factor`` is not finite and greater than zero.
            )pdoc"
        )
        .def(
            "__repr__",
            [](const ScattererCollection& self) {
                return "ScattererCollection(populations=" +
                    std::to_string(self.populations.size()) + ")";
            }
        );
}
