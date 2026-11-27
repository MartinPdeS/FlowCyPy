#include <pybind11/pybind11.h>

namespace py = pybind11;
using namespace pybind11::literals;

namespace {

py::object next_noise_seed(const py::object& generator) {
    if (generator.is_none()) {
        return py::none();
    }
    const auto uint64 = py::module_::import("numpy").attr("uint64");
    return py::int_(generator.attr("integers")(0, py::int_(1) << py::int_(64), "dtype"_a = uint64));
}

struct OptoElectronics {
    py::object detectors, source, amplifier, digitizer, analog_processing;

    py::dict initialize_optical_signal_dict(py::object run_time, py::object background_power) const {
        py::dict signals;
        auto time = digitizer.attr("get_time_series")("run_time"_a = run_time);
        signals["Time"] = time;
        const auto ones = py::module_::import("numpy").attr("ones");
        for (auto detector : detectors) {
            signals[detector.attr("name")] = ones(py::len(time)) * background_power;
        }
        return signals;
    }

    py::dict convert_optical_power_to_photocurrent(py::dict signals) const {
        for (auto detector : detectors) {
            auto name = detector.attr("name");
            py::object signal = signals[name];
            signal *= detector.attr("responsivity").attr("to")("ampere / watt");
            signals[name] = signal;
        }
        return signals;
    }

    py::dict apply_detector_current_noise(py::dict signals, const py::object& generator) const {
        for (auto detector : detectors) {
            auto name = detector.attr("name");
            signals[name] = detector.attr("apply_dark_current_noise")(
                "signal"_a = signals[name], "bandwidth"_a = digitizer.attr("bandwidth"),
                "seed"_a = next_noise_seed(generator));
        }
        return signals;
    }

    py::dict apply_spectral_noise(py::dict signals, const py::dict& emission, const py::object& generator) const {
        auto bandwidth = digitizer.attr("bandwidth").cast<py::object>();
        if (bandwidth.is_none()) bandwidth = digitizer.attr("sampling_rate").cast<py::object>() / py::float_(2.0);
        return py::module_::import("FlowCyPy.fluorescence").attr("_apply_spectral_noise")(
            "source"_a = source, "detectors"_a = detectors, "power"_a = signals,
            "emission"_a = emission, "generator"_a = generator, "bandwidth"_a = bandwidth).cast<py::dict>();
    }

    py::dict apply_source_noise_to_optical_signals(py::dict signals, const py::object& generator) const {
        if (source.attr("_explicit_lasers").cast<bool>()) {
            return apply_spectral_noise(signals, py::dict(), generator);
        }
        if (source.attr("include_rin_noise").cast<bool>() && !source.attr("rin").is_none()) {
            signals = source.attr("add_rin_to_signal_dict")(
                "signal_dict"_a = signals, "seed"_a = next_noise_seed(generator));
        }
        if (source.attr("include_shot_noise").cast<bool>()) {
            for (auto detector : detectors) {
                auto name = detector.attr("name");
                signals[name] = source.attr("add_shot_noise_to_signal")(
                    "signal"_a = signals[name], "time"_a = signals["Time"],
                    "seed"_a = next_noise_seed(generator));
            }
        }
        return signals;
    }

    void add_coupling_to_dataframe(py::object events, bool compute_cross_section) const {
        if (py::len(events) == 0) {
            return;
        }
        for (auto block : events) {
            block.attr("metadata").attr("pop")("FluorescencePower", py::none());
        }
        auto model = py::module_::import("FlowCyPy.opto_electronics.coupling_model").attr("ScatteringModel");
        for (auto detector : detectors) {
            if (source.attr("_has_multiple_lasers").cast<bool>()) {
                py::module_::import("FlowCyPy.fluorescence").attr("_couple_lasers")(
                    "events"_a = events, "beam"_a = source, "detector"_a = detector,
                    "compute_cross_section"_a = compute_cross_section);
            } else if (detector.attr("optical_filter").is_none() &&
                py::len(detector.attr("signals")) == 1 &&
                detector.attr("signals")[py::int_(0)].cast<std::string>() == "scatter") {
                model("source"_a = source, "detector"_a = detector).attr("run")(
                    events, "compute_cross_section"_a = compute_cross_section);
            } else {
                py::module_::import("FlowCyPy.fluorescence").attr("_couple_channel")(
                    "events"_a = events, "source"_a = source, "detector"_a = detector,
                    "compute_cross_section"_a = compute_cross_section);
            }
        }
    }

    py::dict convert_photocurrent_to_voltage(py::dict signals, const py::object& generator) const {
        for (auto detector : detectors) {
            auto name = detector.attr("name");
            signals[name] = amplifier.attr("amplify")(
                "signal"_a = signals[name], "sampling_rate"_a = digitizer.attr("sampling_rate"),
                "seed"_a = next_noise_seed(generator));
        }
        return signals;
    }

    py::dict convert_optical_power_to_voltage(py::dict signals, const py::object& generator,
                                             const py::dict& emission) const {
        py::sequence streams = generator.is_none()
            ? py::make_tuple(py::none(), py::none(), py::none()).cast<py::sequence>()
            : generator.attr("spawn")(3).cast<py::sequence>();
        if (emission.empty()) {
            signals = apply_source_noise_to_optical_signals(signals, streams[0]);
        } else {
            signals = apply_spectral_noise(signals, emission, streams[0]);
        }
        signals = convert_optical_power_to_photocurrent(signals);
        signals = apply_detector_current_noise(signals, streams[1]);
        return convert_photocurrent_to_voltage(signals, streams[2]);
    }

    py::dict copy_dict(py::dict signals) const {
        py::dict copied;
        for (const auto& [name, value] : signals) {
            copied[name] = py::hasattr(value, "copy") ? value.attr("copy")() : py::reinterpret_borrow<py::object>(value);
        }
        return copied;
    }

    py::dict apply_analog_processing(py::dict signals) const {
        auto processed = copy_dict(signals);
        for (auto detector : detectors) {
            auto name = detector.attr("name");
            for (auto circuit : analog_processing) {
                processed[name] = circuit.attr("process")(
                    "signal"_a = processed[name], "sampling_rate"_a = digitizer.attr("sampling_rate"));
            }
        }
        return processed;
    }
};

py::object checked_component(py::object component, const py::object& type) {
    if (!py::isinstance(component, type)) {
        throw py::type_error("Expected an instance of " + py::str(type.attr("__name__")).cast<std::string>());
    }
    return component;
}

py::list checked_components(py::iterable components, const py::object& type) {
    py::list items;
    for (auto item : components) {
        items.append(checked_component(py::reinterpret_borrow<py::object>(item), type));
    }
    return items;
}

} // namespace

PYBIND11_MODULE(system, module) {
    module.doc() = "Optoelectronic acquisition and analog signal processing.";
    py::module_::import("FlowCyPy.units");
    auto source = py::module_::import("FlowCyPy.opto_electronics.source");
    auto circuits = py::module_::import("FlowCyPy.opto_electronics.circuits");
    auto detector = py::module_::import("FlowCyPy.opto_electronics.detector").attr("Detector");
    auto amplifier = py::module_::import("FlowCyPy.opto_electronics.amplifier").attr("Amplifier");
    auto digitizer = py::module_::import("FlowCyPy.opto_electronics.digitizer").attr("Digitizer");
    module.attr("source") = source;
    module.attr("circuits") = circuits;
    module.attr("Detector") = detector;
    module.attr("Amplifier") = amplifier;
    module.attr("Digitizer") = digitizer;

    module.def("_next_noise_seed", &next_noise_seed, py::kw_only(), "generator"_a);
    py::class_<OptoElectronics> optics(module, "OptoElectronics", py::dynamic_attr(),
        R"doc(
            Convert detector optical power traces into voltage traces for an acquisition.

            Parameters
            ----------
            detectors : iterable of Detector
                Detection channels. Each detector name identifies a signal column.
            source : BaseSource
                Illumination model supplying optical power and source noise.
            amplifier : Amplifier
                Transimpedance stage converting photocurrent into voltage.
            digitizer : Digitizer
                Sets the acquisition time grid and sampling bandwidth.
            analog_processing : iterable of BaseCircuit, optional
                Circuits applied to each voltage channel in the supplied order.
        )doc");
    const auto construct = [detector, source, amplifier, digitizer](
        py::iterable detectors, py::object beam, py::object amp, py::object adc) {
        return OptoElectronics{checked_components(detectors, detector),
            checked_component(beam, source.attr("BaseSource")), checked_component(amp, amplifier),
            checked_component(adc, digitizer), py::tuple()};
    };
    optics.def(py::init(construct), "detectors"_a, "source"_a, "amplifier"_a, "digitizer"_a)
        .def(py::init([construct, circuits](py::iterable detectors, py::object beam,
                py::object amp, py::object adc, py::iterable processing) {
            auto result = construct(detectors, beam, amp, adc);
            result.analog_processing = checked_components(processing, circuits.attr("BaseCircuit"));
            return result;
        }), "detectors"_a, "source"_a, "amplifier"_a, "digitizer"_a, "analog_processing"_a)
        .def("__repr__", [](const OptoElectronics& system) {
            py::list names;
            for (auto detector : system.detectors) {
                names.append(detector.attr("name"));
            }
            return py::str("OptoElectronics(detectors={!r}, source={}, amplifier={}, digitizer={}, circuits={})")
                .format(names, py::type::of(system.source).attr("__name__"),
                        py::type::of(system.amplifier).attr("__name__"),
                        py::type::of(system.digitizer).attr("__name__"), py::len(system.analog_processing));
        })
        .def_readwrite("detectors", &OptoElectronics::detectors)
        .def_readwrite("source", &OptoElectronics::source)
        .def_readwrite("amplifier", &OptoElectronics::amplifier)
        .def_readwrite("digitizer", &OptoElectronics::digitizer)
        .def_readwrite("analog_processing", &OptoElectronics::analog_processing)
        .def("initialize_optical_signal_dict", &OptoElectronics::initialize_optical_signal_dict,
             "run_time"_a, "background_power"_a, R"doc(Initialize detector optical power traces.

Parameters
----------
run_time : Time
    Acquisition duration.
background_power : Power
    Constant optical background added to every detector channel.

Returns
-------
dict
    Optical power signal dictionary.)doc")
        .def("convert_optical_power_to_photocurrent", &OptoElectronics::convert_optical_power_to_photocurrent,
             "power_signal_dict"_a, R"doc(Convert detector optical power traces to photocurrent traces.

Parameters
----------
power_signal_dict : dict
    Optical power signal dictionary.

Returns
-------
dict
    Photocurrent signal dictionary.)doc")
        .def("apply_detector_current_noise", &OptoElectronics::apply_detector_current_noise,
             "photocurrent_dict"_a, py::kw_only(), "random_generator"_a = py::none(), R"doc(Apply detector current noise to photocurrent traces.

Parameters
----------
photocurrent_dict : dict
    Photocurrent signal dictionary.

random_generator : numpy.random.Generator, optional
    Generator supplying independent seeds for native noise realizations.

Returns
-------
dict
    Updated photocurrent signal dictionary.)doc")
        .def("apply_source_noise_to_optical_signals", &OptoElectronics::apply_source_noise_to_optical_signals,
             "power_signal_dict"_a, py::kw_only(), "random_generator"_a = py::none(), R"doc(Apply source level optical noise processes.

Parameters
----------
power_signal_dict : dict
    Optical power signals.

random_generator : numpy.random.Generator, optional
    Generator supplying independent seeds for native noise realizations.

Returns
-------
dict
    Updated optical power signals.)doc")
        .def("add_coupling_to_dataframe", &OptoElectronics::add_coupling_to_dataframe,
             "event_collection"_a, "compute_cross_section"_a = false, R"doc(Computes the detected signal for each scatterer in the provided DataFrame and updates it in place.
This method iterates over the list of detectors and computes the detected signal for each scatterer
using the `compute_detected_signal` function.

Parameters
----------
event_collection : EventCollection
    Collection of population event blocks containing scatterer properties.
    Sphere populations use ``SpherePopulation`` fields and core-shell
    populations use ``CoreShellPopulation`` fields.
compute_cross_section : bool, optional
    If True, the scattering cross section (Csca) is computed and added to the DataFrame under the
    column 'Csca'. Default is False.)doc")
        .def("convert_photocurrent_to_voltage", &OptoElectronics::convert_photocurrent_to_voltage,
             "photocurrent_dict"_a, py::kw_only(), "random_generator"_a = py::none(), R"doc(Convert photocurrent traces to analog voltage traces.

Parameters
----------
photocurrent_dict : dict
    Photocurrent signal dictionary.

random_generator : numpy.random.Generator, optional
    Generator supplying independent seeds for native noise realizations.

Returns
-------
dict
    Analog voltage signal dictionary.)doc")
        .def("convert_optical_power_to_voltage", &OptoElectronics::convert_optical_power_to_voltage,
             "power_signal_dict"_a, py::kw_only(), "random_generator"_a = py::none(), "emission"_a = py::dict(), R"doc(Convert optical power traces to analog voltage traces by applying the full optoelectronic chain.

Parameters
----------
power_signal_dict : dict
    Optical power signal dictionary.

random_generator : numpy.random.Generator, optional
    Generator supplying independent seeds for native noise realizations.

emission : dict, optional
    Additional optical power traces keyed by (detector name, wavelength in nm).
    An optional third key element gives the exponential lifetime in seconds.
    Emission is averaged over each acquisition bin before wavelength-dependent shot noise.

Returns
-------
dict
    Analog voltage signal dictionary.)doc")
        .def("copy_dict", &OptoElectronics::copy_dict,
             "dictionnary"_a, R"doc(Create a safe working copy of a signal dictionary.

Parameters
----------
dictionnary : dict
    Signal dictionary containing arrays or Pint quantities.

Returns
-------
dict
    Shallow copy in which values exposing ``copy()`` are duplicated.)doc")
        .def("apply_analog_processing", &OptoElectronics::apply_analog_processing,
             "analog_dict"_a, R"doc(Apply analog post processing circuits to an analog signal dictionary.

Parameters
----------
analog_dict : dict
    Analog voltage signals.

Returns
-------
dict
    Processed analog signal dictionary.)doc");
}
