#include "population_events.h"

#include <stdexcept>

namespace {

py::dict copy_mapping_values(const py::dict& source) {
    py::dict output;
    for (const auto& item : source) {
        py::object value = py::reinterpret_borrow<py::object>(item.second);
        output[item.first] = py::isinstance<py::dict>(value)
            ? value.attr("copy")()
            : value;
    }
    return output;
}

py::object dataframe_copy(const py::object& dataframe) {
    py::kwargs keywords;
    keywords["deep"] = true;
    return dataframe.attr("copy")(**keywords);
}

void set_dataframe_column(
    const py::object& dataframe,
    const std::string& column_name,
    const py::object& values
) {
    py::kwargs keywords;
    keywords["column_name"] = column_name;
    keywords["values"] = values;
    dataframe.attr("set_column")(**keywords);
}

}

PopulationEvents::PopulationEvents(
    py::object dataframe,
    py::object population,
    py::object sampling_method,
    std::string name,
    std::string scatterer_type,
    py::object metadata
)
    : dataframe(std::move(dataframe)),
      population(std::move(population)),
      sampling_method(std::move(sampling_method)),
      name(std::move(name)),
      scatterer_type(std::move(scatterer_type)),
      metadata(metadata.is_none() ? py::dict() : metadata.cast<py::dict>()) {
    synchronize_dataframe_metadata();
}

void PopulationEvents::synchronize_dataframe_metadata() {
    dataframe.attr("scatterer_type") = scatterer_type;
    py::dict attrs = dataframe.attr("attrs").cast<py::dict>();
    if (!attrs.contains("units")) {
        attrs["units"] = py::dict();
    }
}

std::size_t PopulationEvents::size() const {
    return py::len(dataframe);
}

std::shared_ptr<PopulationEvents> PopulationEvents::copy() const {
    py::object copied_dataframe = dataframe_copy(dataframe);
    copied_dataframe.attr("attrs") = copy_mapping_values(
        dataframe.attr("attrs").cast<py::dict>()
    );

    return std::make_shared<PopulationEvents>(
        copied_dataframe,
        population,
        sampling_method,
        name,
        scatterer_type,
        copy_mapping_values(metadata)
    );
}

py::object PopulationEvents::get_item(const py::object& key) const {
    return dataframe.attr("__getitem__")(key);
}

void PopulationEvents::set_item(
    const py::object& key,
    const py::object& value
) {
    dataframe.attr("__setitem__")(key, value);
}

bool PopulationEvents::empty() const {
    return dataframe.attr("empty").cast<bool>();
}

py::object PopulationEvents::columns() const {
    return dataframe.attr("columns");
}

py::object PopulationEvents::get_quantity(
    const std::string& column_name
) const {
    return dataframe.attr("get_quantity")(column_name);
}

void PopulationEvents::set_quantity_column(
    const std::string& column_name,
    const py::object& value
) {
    set_dataframe_column(dataframe, column_name, value);
}

py::object PopulationEvents::to_dataframe(
    const bool include_metadata_in_attrs
) const {
    py::object output = dataframe_copy(dataframe);
    output.attr("attrs") = copy_mapping_values(
        dataframe.attr("attrs").cast<py::dict>()
    );
    output.attr("scatterer_type") = scatterer_type;

    py::dict attrs = output.attr("attrs").cast<py::dict>();
    attrs["Name"] = name;
    attrs["PopulationType"] = scatterer_type;
    attrs["ScattererType"] = scatterer_type;
    attrs["SamplingMethod"] = sampling_method.attr("__class__").attr("__name__");

    if (include_metadata_in_attrs) {
        for (const auto& item : metadata) {
            attrs[item.first] = item.second;
        }
    }

    return output;
}
