#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <pybind11/pybind11.h>
#include <fluidics/flow_cell/flow_cell.h>
#include <fluidics/population_events/population_events.h>
#include <fluidics/populations/sampling_methods.h>
#include <utils/numpy.h>

namespace {

// The transverse sampler takes an int. Check before allocating the dataframe
// or narrowing the count for that sampler.
int explicit_event_count(const py::object& expected_count) {
    const double particles = expected_count.attr("m_as")("particle").cast<double>();
    const double count = std::nearbyint(particles);
    if (!std::isfinite(count) || count < 0) {
        throw py::value_error("Expected particle count must be finite and non-negative.");
    }
    if (count > std::numeric_limits<int>::max()) {
        throw std::overflow_error("Event count exceeds the transverse sampler's range.");
    }
    return static_cast<int>(count);
}

class Fluidics {
public:
    py::object scatterer_collection;
    py::object flow_cell;

    void seed(const py::object& value) const {
        const auto numpy = py::module_::import("numpy");
        if (py::isinstance<py::bool_>(value) ||
            !(py::isinstance<py::int_>(value) || py::isinstance(value, numpy.attr("integer")))) {
            throw py::type_error("seed must be a non-negative integer.");
        }
        const py::int_ seed_value(value);
        if (seed_value < py::int_(0)) {
            throw py::value_error("seed must be a non-negative integer.");
        }
        flow_cell.attr("seed")(seed_value);
        std::size_t index = 0;
        for (const auto population : scatterer_collection.attr("populations")) {
            population.attr("seed")(seed_value + py::int_(1009 * index));
            ++index;
        }
    }

    py::object generate_event_collection(
        const py::object& run_time, const py::object& sampling_rate, const py::object& random_state
    ) const;
};

py::object Fluidics::generate_event_collection(
    const py::object& run_time, const py::object& sampling_rate, const py::object& random_state
) const {
    if (!random_state.is_none()) {
        const auto generator = py::module_::import("numpy").attr("random").attr("Generator");
        if (py::isinstance(random_state, generator)) {
            seed(random_state.attr("integers")(0, std::numeric_limits<std::uint32_t>::max()));
        } else {
            seed(random_state);
        }
    }
    const auto& cell = flow_cell.cast<const FlowCell&>();
    const py::object sample = flow_cell.attr("sample");
    const py::object area = sample.attr("area");
    const py::object mean_speed = sample.attr("average_flow_speed");
    const py::object volume_flow = mean_speed * area;
    const py::object units = py::module_::import("FlowCyPy.units").attr("ureg");
    const py::object frame_type = py::module_::import("FlowCyPy.sub_frames.events").attr("EventDataFrame");
    const py::object range = py::module_::import("builtins").attr("range");

    py::list blocks;
    for (const auto population : scatterer_collection.attr("populations")) {
        const py::object method = population.attr("sampling_method");
        const bool explicit_model = py::isinstance<ExplicitModel>(method);
        const py::object concentration = population.attr("get_effective_concentration")();
        int count;
        if (explicit_model) {
            count = explicit_event_count(concentration * volume_flow * run_time);
        } else if (py::isinstance<GammaModel>(method)) {
            const auto samples = method.cast<const GammaModel&>().number_of_samples;
            if (samples > std::numeric_limits<int>::max()) {
                throw std::overflow_error("Gamma sample count exceeds the transverse sampler's range.");
            }
            count = static_cast<int>(samples);
        } else {
            throw py::type_error("Unsupported sampling method: " +
                py::str(py::type::of(method).attr("__name__")).cast<std::string>());
        }

        py::dict metadata;
        metadata["Name"] = population.attr("name");
        metadata["PopulationType"] = py::type::of(population).attr("__name__");
        metadata["Concentration"] = population.attr("concentration");
        metadata["SamplingMethod"] = py::type::of(method).attr("__name__");
        metadata["NumberOfEvents"] = count;
        auto block = std::make_shared<PopulationEvents>(
            frame_type(py::arg("index") = range(count)),
            py::reinterpret_borrow<py::object>(population), method,
            metadata["Name"].cast<std::string>(), metadata["PopulationType"].cast<std::string>(), metadata
        );
        blocks.append(py::cast(block));
        if (explicit_model && count == 0) {
            continue;
        }

        // Each population's own binding defines its optical properties and their units.
        const auto properties = population.attr("sample")(py::arg("number_of_samples") = count).cast<py::dict>();
        for (const auto& item : properties) {
            block->set_quantity_column(py::cast<std::string>(item.first),
                                       py::reinterpret_borrow<py::object>(item.second));
        }

        for (auto label : population.attr("labels")) {
            block->set_quantity_column(label.attr("column_name").cast<std::string>(),
                                       label.attr("_sample")(py::arg("size") = count, py::arg("properties") = properties));
        }

        auto [x, y, speeds] = cell.sample_transverse_profile(count);
        block->set_quantity_column("x", vector_move_from_numpy(x, x.size()) * units.attr("meter"));
        block->set_quantity_column("y", vector_move_from_numpy(y, y.size()) * units.attr("meter"));
        const py::object velocities = vector_move_from_numpy(speeds, speeds.size()) * units.attr("meter/second");
        block->set_quantity_column("Velocity", velocities);
        if (explicit_model) {
            auto times = cell.sample_arrival_times(count, run_time.attr("m_as")("second").cast<double>());
            block->set_quantity_column("Time", vector_move_from_numpy(times, times.size()) * units.attr("second"));
        } else {
            const py::object mean_velocity = velocities.attr("mean")();
            const py::object volume = mean_velocity / sampling_rate * area;
            metadata["VelocityMean"] = mean_velocity;
            metadata["InterrogationVolumePerTimeBin"] = volume;
            metadata["ExpectedNumberOfParticles"] = (concentration * volume).attr("m_as")("particle");
        }
    }
    const auto collection_type = py::module_::import("FlowCyPy.event_collection").attr("EventCollection");
    return collection_type(py::arg("events_list") = blocks);
}

}  // namespace

PYBIND11_MODULE(system, module) {
    module.doc() = "Fluidic event generation for flow cytometry acquisitions.";
    py::class_<Fluidics>(module, "Fluidics", R"doc(
        Generate population events for a configured flow cell.

        Parameters
        ----------
        scatterer_collection : ScattererCollection
            Particle populations to simulate.
        flow_cell : FlowCell
            Flow cell through which the particles are transported.
    )doc")
        .def(py::init<py::object, py::object>(), py::arg("scatterer_collection"), py::arg("flow_cell"))
        .def("__repr__", [](const Fluidics& system) {
            return py::str("Fluidics(scatterer_collection={!r}, flow_cell={!r})")
                .format(system.scatterer_collection, system.flow_cell);
        })
        .def_readwrite("scatterer_collection", &Fluidics::scatterer_collection)
        .def_readwrite("flow_cell", &Fluidics::flow_cell)
        .def("seed", &Fluidics::seed, py::arg("value"),
             "Seed the flow cell and all population samplers with a non-negative integer.")
        .def("generate_event_collection", &Fluidics::generate_event_collection,
             py::arg("run_time"), py::arg("sampling_rate"), py::arg("random_state") = py::none(),
             R"doc(
                 Generate an event collection for all configured populations.

                 Parameters
                 ----------
                 run_time : time quantity
                     Acquisition duration for explicit arrivals.
                 sampling_rate : frequency quantity
                     Sampling rate for gamma occupancy calculations.
                 random_state : int or numpy.random.Generator, optional
                     Seed or advancing random stream for this acquisition.

                 Returns
                 -------
                 EventCollection
                     Ordered population event blocks with unit-aware dataframes.
             )doc");
}
