#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "classifier.h"

namespace py = pybind11;

PYBIND11_MODULE(classifier, module) {
    py::class_<KmeansClassifier>(module, "KMEANSCLASSIFIER")
        .def(py::init<size_t>(), py::arg("number_of_clusters"))

        // Expose the run method with numpy array input
        .def("_cpp_run",
            [](KmeansClassifier &classifier,
               py::array_t<double, py::array::c_style | py::array::forcecast> input_matrix,
               unsigned int random_state)
            {
                py::buffer_info info = input_matrix.request();

                if (info.ndim != 2) {
                    throw std::runtime_error("Input must be a two dimensional array");
                }

                const size_t number_of_samples = info.shape[0];
                const size_t number_of_features = info.shape[1];

                const double *data_ptr = static_cast<double *>(info.ptr);

                std::vector<std::vector<double>> data_matrix(
                    number_of_samples,
                    std::vector<double>(number_of_features)
                );

                for (size_t i = 0; i < number_of_samples; i++) {
                    for (size_t f = 0; f < number_of_features; f++) {
                        data_matrix[i][f] = data_ptr[i * number_of_features + f];
                    }
                }

                return classifier.run(data_matrix, random_state);
            },
            py::arg("data_matrix"),
            py::arg("random_state") = 42
        );


    py::class_<DbscanClassifier>(module, "DBSCANCLASSIFIER")
        .def(py::init<double, std::size_t>(),
        py::arg("epsilon"),
        py::arg("minimum_samples")
    )
        .def(
            "_cpp_run",
            [](const DbscanClassifier &classifier,
               py::array_t<double, py::array::c_style | py::array::forcecast> input_matrix)
            {
                py::buffer_info info = input_matrix.request();

                if (info.ndim != 2) {
                    throw std::runtime_error("Input must be a two dimensional array");
                }

                std::size_t number_of_samples = static_cast<std::size_t>(info.shape[0]);
                std::size_t number_of_features = static_cast<std::size_t>(info.shape[1]);

                const double *data_pointer = static_cast<double *>(info.ptr);

                std::vector<std::vector<double>> data_matrix(
                    number_of_samples,
                    std::vector<double>(number_of_features)
                );

                for (std::size_t i = 0; i < number_of_samples; i++) {
                    for (std::size_t f = 0; f < number_of_features; f++) {
                        data_matrix[i][f] = data_pointer[i * number_of_features + f];
                    }
                }

                std::vector<int> labels = classifier.run(data_matrix);

                py::array_t<int> result(number_of_samples);
                py::buffer_info result_info = result.request();
                int *result_pointer = static_cast<int *>(result_info.ptr);

                for (std::size_t i = 0; i < number_of_samples; i++) {
                    result_pointer[i] = labels[i];
                }

                return result;
            },
            py::arg("data_matrix")
        );
}
