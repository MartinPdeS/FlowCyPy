#include "coupling.h"

#include <stdexcept>

namespace {

py::object keyword_call(
    const py::object& callable,
    const py::kwargs& keywords
) {
    return callable(*py::tuple(), **keywords);
}

py::object get_column(const py::object& dataframe, const char* name) {
    return dataframe.attr("__getitem__")(name);
}

}

ScatteringModel::ScatteringModel(py::object source, py::object detector)
    : source_(std::move(source)), detector_(std::move(detector)) {}

void ScatteringModel::run(
    const py::object& event_frames,
    const bool compute_cross_section
) {
    py::gil_scoped_acquire gil;

    for (const py::handle frame_handle : py::reinterpret_borrow<py::iterable>(event_frames)) {
        py::object event_dataframe = py::reinterpret_borrow<py::object>(frame_handle);
        const std::size_t count = py::len(event_dataframe);
        if (count == 0) {
            continue;
        }

        write_results(
            event_dataframe,
            build_experiment(event_dataframe),
            compute_cross_section
        );
    }
}

py::object ScatteringModel::build_experiment(const py::object& event_dataframe) {
    const std::size_t count = py::len(event_dataframe);

    py::kwargs keywords;
    keywords["source_set"] = build_source_set(event_dataframe, count);
    keywords["scatterer_set"] = build_scatterer_set(event_dataframe, count);
    keywords["detector_set"] = build_detector_set(count);

    py::object experiment_module = py::module_::import("PyMieSim.experiment");
    return keyword_call(experiment_module.attr("Setup"), keywords);
}

py::object ScatteringModel::build_source_set(
    const py::object& event_dataframe,
    const std::size_t count
) {
    py::object x_coordinates = get_column(event_dataframe, "x");
    py::object y_coordinates = get_column(event_dataframe, "y");
    py::object numpy = py::module_::import("numpy");
    py::object z_coordinates = numpy.attr("zeros")(count) * x_coordinates.attr("units");

    py::kwargs amplitude_keywords;
    amplitude_keywords["x"] = x_coordinates;
    amplitude_keywords["y"] = y_coordinates;
    amplitude_keywords["z"] = z_coordinates;
    py::object amplitude = keyword_call(
        source_.attr("get_amplitude_signal"),
        amplitude_keywords
    );

    py::object typed_unit = py::module_::import("TypedUnit");
    py::object ureg = typed_unit.attr("ureg");
    py::object polarization = py::int_(0) * ureg.attr("degree");

    py::kwargs keywords;
    keywords["target_size"] = count;
    keywords["wavelength"] = source_.attr("wavelength");
    keywords["polarization"] = polarization;
    keywords["amplitude"] = amplitude;

    py::object experiment_module = py::module_::import("PyMieSim.experiment");
    return keyword_call(
        experiment_module.attr("source_set").attr("PlaneWaveSet").attr("build_sequential"),
        keywords
    );
}

py::object ScatteringModel::build_detector_set(const std::size_t count) {
    // PyMieSim registers detector material definitions on importing this module.
    py::module_::import("PyMieSim.material");
    py::object experiment_module = py::module_::import("PyMieSim.experiment");

    py::kwargs keywords;
    keywords["target_size"] = count;
    keywords["numerical_aperture"] = detector_.attr("numerical_aperture");
    keywords["cache_numerical_aperture"] = detector_.attr("cache_numerical_aperture");
    keywords["gamma_offset"] = detector_.attr("gamma_angle");
    keywords["phi_offset"] = detector_.attr("phi_angle");
    keywords["sampling"] = detector_.attr("sampling");
    keywords["medium"] = 1.0;

    return keyword_call(
        experiment_module.attr("detector_set").attr("PhotodiodeSet").attr("build_sequential"),
        keywords
    );
}

py::object ScatteringModel::build_scatterer_set(
    const py::object& event_dataframe,
    const std::size_t count
) {
    const std::string scatterer_type =
        py::str(event_dataframe.attr("scatterer_type"));
    py::object experiment_module = py::module_::import("PyMieSim.experiment");

    py::kwargs keywords;
    keywords["target_size"] = count;

    if (scatterer_type == "SpherePopulation") {
        py::object refractive_index = get_column(event_dataframe, "RefractiveIndex");
        py::object medium_refractive_index = get_column(
            event_dataframe,
            "MediumRefractiveIndex"
        );
        keywords["diameter"] = get_column(event_dataframe, "Diameter");
        keywords["material"] = refractive_index.attr("magnitude");
        keywords["medium"] = medium_refractive_index.attr("magnitude");

        return keyword_call(
            experiment_module.attr("scatterer_set").attr("SphereSet").attr("build_sequential"),
            keywords
        );
    }

    if (scatterer_type == "CoreShellPopulation") {
        keywords["core_diameter"] = get_column(event_dataframe, "CoreDiameter");
        keywords["core_refractive_index"] = get_column(
            event_dataframe,
            "CoreRefractiveIndex"
        );
        keywords["shell_thickness"] = get_column(event_dataframe, "ShellThickness");
        keywords["shell_refractive_index"] = get_column(
            event_dataframe,
            "ShellRefractiveIndex"
        );
        keywords["medium_refractive_index"] = get_column(
            event_dataframe,
            "MediumRefractiveIndex"
        );

        py::object pymiesim = py::module_::import("PyMieSim");
        return keyword_call(
            pymiesim.attr("scatterer").attr("CoreShellSet").attr("build_sequential"),
            keywords
        );
    }

    throw py::value_error("Unknown scatterer type: " + scatterer_type);
}

void ScatteringModel::write_results(
    const py::object& event_dataframe,
    const py::object& experiment,
    const bool compute_cross_section
) {
    py::object typed_unit = py::module_::import("TypedUnit");
    py::object ureg = typed_unit.attr("ureg");
    py::object dataframe = event_dataframe.attr("dataframe");

    py::object coupling = experiment.attr("get_sequential")("coupling") * ureg.attr("watt");
    py::kwargs coupling_keywords;
    coupling_keywords["column_name"] = detector_.attr("name");
    coupling_keywords["values"] = coupling;
    keyword_call(dataframe.attr("set_column"), coupling_keywords);

    if (compute_cross_section) {
        py::object cross_section = experiment.attr("get_sequential")("Csca") *
            (ureg.attr("meter") * ureg.attr("meter"));
        py::kwargs cross_section_keywords;
        cross_section_keywords["column_name"] = "Csca";
        cross_section_keywords["values"] = cross_section;
        keyword_call(dataframe.attr("set_column"), cross_section_keywords);
    }
}
