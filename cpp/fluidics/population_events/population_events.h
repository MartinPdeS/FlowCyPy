#pragma once

#include <memory>
#include <string>

#include <pybind11/pybind11.h>

namespace py = pybind11;

/**
 * @brief Unit-aware event block generated for one particle population.
 *
 * The dataframe and semantic simulation objects remain Python-owned objects;
 * this class provides the event-container protocol and metadata management in
 * native code.
 */
class PopulationEvents {
public:
    py::object dataframe;
    py::object population;
    py::object sampling_method;
    std::string name;
    std::string scatterer_type;
    py::dict metadata;

    PopulationEvents(
        py::object dataframe,
        py::object population,
        py::object sampling_method,
        std::string name,
        std::string scatterer_type,
        py::object metadata = py::none()
    );

    std::size_t size() const;
    std::shared_ptr<PopulationEvents> copy() const;
    py::object get_item(const py::object& key) const;
    void set_item(const py::object& key, const py::object& value);
    bool empty() const;
    py::object columns() const;
    py::object get_quantity(const std::string& column_name) const;
    void set_quantity_column(const std::string& column_name, const py::object& value);
    py::object to_dataframe(bool include_metadata_in_attrs = true) const;

private:
    void synchronize_dataframe_metadata();
};
