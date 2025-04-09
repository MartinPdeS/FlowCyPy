#pragma once
#include <pybind11/pybind11.h>
// #include <pybind11/numpy.h>
#include <vector>

// pybind11::array to_array_double(const std::vector<double>& vector) {
//     // This returns a NumPy array (copy) with dtype=float64
//     return pybind11::array(
//         pybind11::dtype("float64"),                      // explicitly set dtype
//         vector.size(),                                // shape
//         vector.data()                                 // data pointer
//     );
// }

// pybind11::array to_array_int(const std::vector<int>& vector) {
//     // This returns a NumPy array (copy) with dtype=float64
//     return pybind11::array(
//         pybind11::dtype("int32"),                        // explicitly set dtype
//         vector.size(),                                // shape
//         vector.data()                                 // data pointer
//     );
// }
