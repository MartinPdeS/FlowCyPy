#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <vector>
#include <string>
#include <stdexcept>

#include "classifier.h"

namespace py = pybind11;

namespace
{
    py::object get_default_detectors(py::object dataframe)
    {
        py::object columns = dataframe.attr("columns");
        py::object detector_values = columns.attr("get_level_values")("Detector");
        return detector_values.attr("unique")().attr("tolist")();
    }

    py::object filter_dataframe(
        py::object dataframe,
        py::object features,
        py::object detectors
    ) {
        if (detectors.is_none()) {
            detectors = get_default_detectors(dataframe);
        }

        return dataframe.attr("loc").attr("__getitem__")(
            py::make_tuple(
                py::slice(py::none(), py::none(), py::none()),
                py::make_tuple(features, detectors)
            )
        );
    }

    py::object dequantify_dataframe_if_needed(py::object dataframe)
    {
        if (py::hasattr(dataframe, "pint")) {
            dataframe = dataframe.attr("pint").attr("dequantify")();
            dataframe = dataframe.attr("droplevel")("unit", py::arg("axis") = 1);
        }

        return dataframe;
    }

    std::vector<std::vector<double>> dataframe_to_matrix(py::object dataframe)
    {
        py::array_t<double, py::array::c_style | py::array::forcecast> values =
            dataframe.attr("to_numpy")().cast<py::array_t<double, py::array::c_style | py::array::forcecast>>();

        py::buffer_info buffer = values.request();

        if (buffer.ndim != 2) {
            throw std::runtime_error("Filtered dataframe values must be a two dimensional array.");
        }

        const std::size_t number_of_samples = static_cast<std::size_t>(buffer.shape[0]);
        const std::size_t number_of_features = static_cast<std::size_t>(buffer.shape[1]);

        const double* data_pointer = static_cast<double*>(buffer.ptr);

        std::vector<std::vector<double>> data_matrix(
            number_of_samples,
            std::vector<double>(number_of_features)
        );

        for (std::size_t sample_index = 0; sample_index < number_of_samples; ++sample_index) {
            for (std::size_t feature_index = 0; feature_index < number_of_features; ++feature_index) {
                data_matrix[sample_index][feature_index] =
                    data_pointer[sample_index * number_of_features + feature_index];
            }
        }

        return data_matrix;
    }

    py::array_t<int> vector_to_numpy_array(const std::vector<int>& labels)
    {
        py::array_t<int> label_array(labels.size());

        py::buffer_info buffer = label_array.request();
        int* output_pointer = static_cast<int*>(buffer.ptr);

        for (std::size_t label_index = 0; label_index < labels.size(); ++label_index) {
            output_pointer[label_index] = labels[label_index];
        }

        return label_array;
    }

    py::object prepare_feature_dataframe(
        py::object dataframe,
        py::object features,
        py::object detectors
    ) {
        py::object sub_dataframe = filter_dataframe(
            dataframe,
            features,
            detectors
        );

        return dequantify_dataframe_if_needed(sub_dataframe);
    }

    py::object finalize_classified_dataframe(
        py::object wide_dataframe,
        py::array_t<int> label_array
    ) {
        py::module_ pandas = py::module_::import("pandas");

        py::object stacked_dataframe = wide_dataframe.attr("stack")(
            "Detector",
            py::arg("future_stack") = true
        );

        py::object event_labels = pandas.attr("Series")(
            label_array,
            py::arg("index") = wide_dataframe.attr("index")
        );

        py::object stacked_event_index = stacked_dataframe.attr("index").attr("droplevel")("Detector");
        py::object repeated_labels = stacked_event_index.attr("map")(event_labels);

        stacked_dataframe.attr("__setitem__")("Label", repeated_labels);

        py::object classifier_dataframe_type =
            py::module_::import("FlowCyPy.sub_frames.classifier").attr("ClassifierDataFrame");

        return classifier_dataframe_type(stacked_dataframe);
    }
}

PYBIND11_MODULE(classifier, module)
{
    py::class_<KmeansClassifier>(module, "KmeansClassifier")
        .def(
            py::init<std::size_t>(),
            py::arg("number_of_clusters")
        )
        .def_readonly(
            "number_of_clusters",
            &KmeansClassifier::number_of_cluster
        )
        .def(
            "run",
            [](KmeansClassifier& classifier,
               py::object dataframe,
               py::object features,
               py::object detectors,
               unsigned int random_state)
            {
                py::object filtered_dataframe = prepare_feature_dataframe(
                    dataframe,
                    features,
                    detectors
                );

                std::vector<std::vector<double>> data_matrix = dataframe_to_matrix(filtered_dataframe);

                std::vector<int> labels;
                {
                    py::gil_scoped_release release;
                    labels = classifier.run(data_matrix, random_state);
                }

                py::array_t<int> label_array = vector_to_numpy_array(labels);

                return finalize_classified_dataframe(dataframe, label_array);
            },
            py::arg("dataframe"),
            py::arg("features") = py::cast(std::vector<std::string>{"Height"}),
            py::arg("detectors") = py::none(),
            py::arg("random_state") = 42,
            R"pbdoc(
                Run KMeans clustering on selected features from a pandas DataFrame.

                This method expects a wide DataFrame, typically produced using
                ``unstack("Detector")`` on a peaks table. The selected feature and detector
                columns are filtered, converted to a numerical matrix, clustered in C++, and
                the resulting event labels are mapped back onto the stacked detector-wise
                DataFrame.

                Parameters
                ----------
                dataframe : pandas.DataFrame
                    Wide input DataFrame containing event features in a column MultiIndex.
                    The columns must include a level named ``"Detector"``.
                features : list of str, default=["Height"]
                    Feature names to use for clustering.
                detectors : list of str or None, default=None
                    Detector names to include in the clustering. If ``None``, all detectors
                    found in the ``"Detector"`` column level are used.
                random_state : int, default=42
                    Seed used by the KMeans initialization procedure.

                Returns
                -------
                ClassifierDataFrame
                    Classified dataframe in stacked detector format with a 1D ``Label``
                    column.

                Raises
                ------
                RuntimeError
                    If the filtered data cannot be interpreted as a two dimensional numerical
                    array.
                KeyError
                    If one or more requested features or detectors are not present.
                AttributeError
                    If the DataFrame does not expose the expected pandas interface.

                Examples
                --------
                >>> classifier = KMEANSCLASSIFIER(number_of_clusters=2)
                >>> classified = classifier.run(
                ...     dataframe=run_record.peaks.unstack("Detector"),
                ...     features=["Height"],
                ...     detectors=["side", "forward"],
                ... )
                >>> classified.plot(x=("side", "Height"), y=("forward", "Height"))
            )pbdoc"
        );

    py::class_<DbscanClassifier>(module, "DBScanClassifier")
        .def(
            py::init<double, std::size_t>(),
            py::arg("epsilon"),
            py::arg("minimum_samples")
        )
        .def_readonly(
            "epsilon",
            &DbscanClassifier::epsilon
        )
        .def_readonly(
            "minimum_samples",
            &DbscanClassifier::minimum_samples
        )
        .def(
            "run",
            [](const DbscanClassifier& classifier,
               py::object dataframe,
               py::object features,
               py::object detectors)
            {
                py::object filtered_dataframe = prepare_feature_dataframe(
                    dataframe,
                    features,
                    detectors
                );

                std::vector<std::vector<double>> data_matrix = dataframe_to_matrix(filtered_dataframe);

                std::vector<int> labels;
                {
                    py::gil_scoped_release release;
                    labels = classifier.run(data_matrix);
                }

                py::array_t<int> label_array = vector_to_numpy_array(labels);

                return finalize_classified_dataframe(dataframe, label_array);
            },
            py::arg("dataframe"),
            py::arg("features") = py::cast(std::vector<std::string>{"Height"}),
            py::arg("detectors") = py::none(),
            R"pbdoc(
                Run DBSCAN clustering on selected features from a pandas DataFrame.

                This method expects a wide DataFrame, typically produced using
                ``unstack("Detector")`` on a peaks table. The selected feature and detector
                columns are filtered, converted to a numerical matrix, clustered in C++, and
                the resulting event labels are mapped back onto the stacked detector-wise
                DataFrame.

                Parameters
                ----------
                dataframe : pandas.DataFrame
                    Wide input DataFrame containing event features in a column MultiIndex.
                    The columns must include a level named ``"Detector"``.
                features : list of str, default=["Height"]
                    Feature names to use for clustering.
                detectors : list of str or None, default=None
                    Detector names to include in the clustering. If ``None``, all detectors
                    found in the ``"Detector"`` column level are used.

                Returns
                -------
                ClassifierDataFrame
                    Classified dataframe in stacked detector format with a 1D ``Label``
                    column.

                Raises
                ------
                RuntimeError
                    If the filtered data cannot be interpreted as a two dimensional numerical
                    array.
                KeyError
                    If one or more requested features or detectors are not present.
                AttributeError
                    If the DataFrame does not expose the expected pandas interface.
            )pbdoc"
        );
}
