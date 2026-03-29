#pragma once

#include <vector>
#include <string>
#include <stdexcept>
#include <sstream>
#include <complex>
#include <memory>
#include <limits>
#include <cmath>

#include <pybind11/pybind11.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;
using complex128 = std::complex<double>;

namespace Casting {


    template <typename dtype>
    std::vector<dtype> cast_py_to_vector(
        const py::object& object,
        const std::string& units = ""
    ) {
        py::object value_object = object;

        if (!units.empty()) {
            if (!py::hasattr(object, "to")) {
                std::ostringstream oss;
                oss << "Expected a quantity with units compatible with '" << units
                    << "', but received an object without units.";
                throw std::invalid_argument(oss.str());
            }

            try {
                value_object = py::reinterpret_borrow<py::object>(
                    object.attr("to")(units).attr("magnitude")
                );
            }
            catch (const py::error_already_set&) {
                std::ostringstream oss;
                oss << "Failed to convert object to '" << units
                    << "'. Ensure the object has compatible units using FlowCyPy.units.ureg.";
                throw std::invalid_argument(oss.str());
            }
        }

        if (py::isinstance<py::array>(value_object)) {
            py::array array = py::reinterpret_borrow<py::array>(value_object);

            if (array.ndim() == 0) {
                return {py::cast<dtype>(array.attr("item")())};
            }

            if (array.ndim() == 1) {
                return value_object.cast<std::vector<dtype>>();
            }

            throw std::invalid_argument("Only scalar or 1D array inputs are supported.");
        }

        try {
            return {value_object.cast<dtype>()};
        }
        catch (const py::cast_error&) {
        }

        if (py::isinstance<py::sequence>(value_object) && !py::isinstance<py::str>(value_object)) {
            return value_object.cast<std::vector<dtype>>();
        }

        throw std::invalid_argument("Object cannot be converted to a scalar or sequence.");
    }

    template <typename dtype>
    std::vector<dtype> cast_py_to_broadcasted_vector(
        const std::string& name,
        const py::object& object,
        const size_t target_size,
        const std::string& units = ""
    ) {
        if (target_size == 0) {
            std::ostringstream oss;
            oss << "Parameter '" << name << "' cannot be broadcast because target_size is 0.";
            throw std::invalid_argument(oss.str());
        }

        std::vector<dtype> values = cast_py_to_vector<dtype>(object, units);

        if (values.empty()) {
            std::ostringstream oss;
            oss << "Parameter '" << name << "' is empty. Provide a scalar or a non empty array.";
            throw std::invalid_argument(oss.str());
        }

        if (values.size() == 1) {
            return std::vector<dtype>(target_size, values[0]);
        }

        if (values.size() != target_size) {
            std::ostringstream oss;
            oss << "Inconsistent sizes: '" << name << "' has size " << values.size() << " but expected 1 or " << target_size << ".";
            throw std::invalid_argument(oss.str());
        }

        return values;
    }

    template <typename dtype>
    dtype cast_py_to_scalar(
        const py::object& object,
        const std::string& name,
        const std::string& units = ""
    ) {
        std::vector<dtype> values = cast_py_to_vector<dtype>(object, units);

        if (values.empty()) {
            std::ostringstream oss;
            oss << "Parameter '" << name << "' is empty. Provide a scalar or a size 1 array.";
            throw std::invalid_argument(oss.str());
        }

        if (values.size() != 1) {
            std::ostringstream oss;
            oss << "Parameter '" << name << "' must be a scalar or a size 1 array.";
            throw std::invalid_argument(oss.str());
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

}
