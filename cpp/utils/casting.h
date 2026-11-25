#pragma once

#include <vector>
#include <string>
#include <sstream>
#include <complex>
#include <memory>
#include <limits>
#include <cmath>
#include <type_traits>

#include <pybind11/pybind11.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;
using complex128 = std::complex<double>;

namespace Casting {

    inline void raise_type_error(
        const std::string& name,
        const std::string& message
    ) {
        std::ostringstream output_stream;
        output_stream << "Parameter '" << name << "': " << message;
        throw py::type_error(output_stream.str());
    }

    inline void raise_value_error(
        const std::string& name,
        const std::string& message
    ) {
        std::ostringstream output_stream;
        output_stream << "Parameter '" << name << "': " << message;
        throw py::value_error(output_stream.str());
    }

    template <typename dtype>
    std::vector<dtype> cast_py_to_vector(
        const py::object& object,
        const std::string& name,
        const std::string& units = ""
    ) {
        py::object value_object = object;

        if (!units.empty()) {
            if (object.is_none()) {
                raise_type_error(
                    name,
                    "expected a quantity with units compatible with '" + units + "', but received None."
                );
            }

            if (!py::hasattr(object, "to")) {
                raise_type_error(
                    name,
                    "expected a quantity with units compatible with '" + units + "', but received an object without a '.to(...)' method."
                );
            }

            try {
                value_object = py::reinterpret_borrow<py::object>(
                    object.attr("to")(units).attr("magnitude")
                );
            }
            catch (const py::error_already_set&) {
                raise_value_error(
                    name,
                    "failed unit conversion to '" + units + "'. Ensure the object carries compatible units."
                );
            }
        }

        if (py::isinstance<py::array>(value_object)) {
            py::array array = py::reinterpret_borrow<py::array>(value_object);

            if (array.ndim() == 0) {
                try {
                    return {py::cast<dtype>(array.attr("item")())};
                }
                catch (const py::cast_error&) {
                    raise_type_error(
                        name,
                        "scalar array value cannot be converted to the requested numeric type."
                    );
                }
            }

            if (array.ndim() == 1) {
                try {
                    return value_object.cast<std::vector<dtype>>();
                }
                catch (const py::cast_error&) {
                    raise_type_error(
                        name,
                        "1D array elements cannot be converted to the requested numeric type."
                    );
                }
            }

            raise_value_error(
                name,
                "only scalar or 1D array inputs are supported."
            );
        }

        try {
            return {value_object.cast<dtype>()};
        }
        catch (const py::cast_error&) {
        }

        if (py::isinstance<py::sequence>(value_object) && !py::isinstance<py::str>(value_object)) {
            try {
                return value_object.cast<std::vector<dtype>>();
            }
            catch (const py::cast_error&) {
                raise_type_error(
                    name,
                    "sequence elements cannot be converted to the requested numeric type."
                );
            }
        }

        raise_type_error(
            name,
            "object cannot be converted to a scalar or 1D numeric sequence."
        );
    }

    template <typename dtype>
    std::vector<dtype> cast_py_to_broadcasted_vector(
        const std::string& name,
        const py::object& object,
        const size_t target_size,
        const std::string& units = ""
    ) {
        if (target_size == 0) {
            raise_value_error(
                name,
                "cannot be broadcast because target_size is 0."
            );
        }

        std::vector<dtype> values = cast_py_to_vector<dtype>(object, name, units);

        if (values.empty()) {
            raise_value_error(
                name,
                "is empty. Provide a scalar or a non empty array."
            );
        }

        if (values.size() == 1) {
            return std::vector<dtype>(target_size, values[0]);
        }

        if (values.size() != target_size) {
            std::ostringstream output_stream;
            output_stream
                << "has size " << values.size()
                << " but expected size 1 or " << target_size << ".";
            raise_value_error(name, output_stream.str());
        }

        return values;
    }

    template <typename dtype>
    dtype cast_py_to_scalar(
        const py::object& object,
        const std::string& name,
        const std::string& units = ""
    ) {
        std::vector<dtype> values = cast_py_to_vector<dtype>(object, name, units);

        if (values.empty()) {
            raise_value_error(
                name,
                "is empty. Provide a scalar or a size 1 array."
            );
        }

        if (values.size() != 1) {
            raise_value_error(
                name,
                "must be a scalar or a size 1 array."
            );
        }

        return values[0];
    }

    template <typename dtype>
    dtype cast_py_to_optional_scalar(
        const py::object& object,
        const std::string& name,
        const std::string& units = "",
        const dtype none_value = std::numeric_limits<dtype>::quiet_NaN()
    ) {
        if (object.is_none()) {
            return none_value;
        }

        return cast_py_to_scalar<dtype>(object, name, units);
    }

    template <typename dtype>
    py::object cast_scalar_to_py_noneable(const dtype value) {
        if constexpr (std::is_floating_point_v<dtype>) {
            if (std::isnan(value)) {
                return py::none();
            }
        }

        return py::cast(value);
    }

    std::map<std::string, std::vector<double>> cast_py_dict_to_flat_data_map(
        const py::dict& data_dict
    ) {
        std::map<std::string, std::vector<double>> input_data_map;

        for (const auto& item : data_dict) {
            const std::string channel_name = py::reinterpret_borrow<py::object>(item.first).cast<std::string>();

            const py::object channel_object = py::reinterpret_borrow<py::object>(item.second);

            if (channel_name == "segment_id") {
                input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                    channel_object,
                    channel_name
                );
            }
            else if (channel_name == "Time") {
                input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                    channel_object,
                    channel_name,
                    "second"
                );
            }
            else {
                input_data_map[channel_name] = Casting::cast_py_to_vector<double>(
                    channel_object,
                    channel_name,
                    "volt"
                );
            }
        }

        return input_data_map;
    }

}
