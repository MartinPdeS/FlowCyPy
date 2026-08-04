#include <pybind11/pybind11.h>

#include "population_events.h"

namespace py = pybind11;

PYBIND11_MODULE(_population_events, module) {
    module.doc() = R"pdoc(
        Native population-level event containers.

        The extension stores event data in FlowCyPy's unit-aware
        :class:`EventDataFrame` objects and keeps the associated population,
        sampling method, and metadata available to the Python simulation layer.
    )pdoc";

    py::class_<PopulationEvents, std::shared_ptr<PopulationEvents>>(
        module,
        "PopulationEvents",
        R"pdoc(
            Structured event data for one simulated population.

            Parameters
            ----------
            dataframe : EventDataFrame
                Unit-aware table containing one row per event.
            population : object
                Population object that generated the events.
            sampling_method : object
                Sampling strategy used to generate the event block.
            name : str
                Population name.
            scatterer_type : str
                Scatterer type label, such as ``SpherePopulation``.
            metadata : dict, optional
                Population-level diagnostic and simulation metadata.

            Notes
            -----
            Construction synchronizes ``dataframe.scatterer_type`` and ensures
            that ``dataframe.attrs["units"]`` exists, including for empty blocks.
        )pdoc"
    )
        .def(
            py::init<py::object, py::object, py::object, std::string, std::string, py::object>(),
            py::arg("dataframe"),
            py::arg("population"),
            py::arg("sampling_method"),
            py::arg("name"),
            py::arg("scatterer_type"),
            py::arg("metadata") = py::none(),
            R"pdoc(
                Create a population event block and synchronize dataframe metadata.
            )pdoc"
        )
        .def_readwrite("dataframe", &PopulationEvents::dataframe,
            "Underlying unit-aware event dataframe.")
        .def_readwrite("population", &PopulationEvents::population,
            "Population object that generated the events.")
        .def_readwrite("sampling_method", &PopulationEvents::sampling_method,
            "Sampling strategy used to generate the events.")
        .def_readwrite("name", &PopulationEvents::name,
            "Human-readable population name.")
        .def_readwrite("scatterer_type", &PopulationEvents::scatterer_type,
            "Scatterer type label associated with the population.")
        .def_readwrite("metadata", &PopulationEvents::metadata,
            "Population-level metadata dictionary.")
        .def("__len__", &PopulationEvents::size,
            "Return the number of event rows.")
        .def("copy", &PopulationEvents::copy,
            "Return a detached copy with copied dataframe and metadata mappings.")
        .def("__getitem__", &PopulationEvents::get_item,
            py::arg("key"), "Return a dataframe column.")
        .def("__setitem__", &PopulationEvents::set_item,
            py::arg("key"), py::arg("value"), "Assign a dataframe column.")
        .def_property_readonly("empty", &PopulationEvents::empty,
            "Whether the event dataframe contains no rows.")
        .def_property_readonly("columns", &PopulationEvents::columns,
            "Return the dataframe columns.")
        .def("get_quantity", &PopulationEvents::get_quantity,
            py::arg("column_name"),
            "Return a column as a unit-aware quantity when a unit is registered.")
        .def("set_quantity_column", &PopulationEvents::set_quantity_column,
            py::arg("column_name"), py::arg("value"),
            "Store a quantity column in the underlying dataframe.")
        .def("to_dataframe", &PopulationEvents::to_dataframe,
            py::arg("include_metadata_in_attrs") = true,
            R"pdoc(
                Export a detached dataframe copy.

                Parameters
                ----------
                include_metadata_in_attrs : bool, default=True
                    Include population metadata in the exported dataframe attrs.
            )pdoc"
        );
}
