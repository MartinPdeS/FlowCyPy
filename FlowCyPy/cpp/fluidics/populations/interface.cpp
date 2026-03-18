#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <pint/pint.h>
#include <utils/numpy.h>
#include "populations.h"

namespace py = pybind11;


std::shared_ptr<BaseDistribution> as_distribution(py::object obj, const char* delta_unit_expr) {
    py::object ureg = get_shared_ureg();

    if (py::hasattr(obj, "units")) {
        const double value = obj.attr("to_base_units")().attr("magnitude").cast<double>();

        return std::make_shared<Delta>(value);
    }

    return obj.cast<std::shared_ptr<BaseDistribution>>();
};


PYBIND11_MODULE(populations, module) {
    py::object ureg = get_shared_ureg();

    module.doc() = R"pdoc(
        FlowCyPy population module.

        This extension defines population level objects used to parameterize flow cytometry
        simulations. A population couples:

            - A concentration (particle / liter)
            - Distributions for physical properties (e.g., diameter, refractive index)
            - A sampling strategy describing how detector signals are generated

        All quantities returned to Python are Pint Quantity objects using the shared unit registry.
    )pdoc"
    ;

    py::class_<BaseSamplingMethod, std::shared_ptr<BaseSamplingMethod>>(module, "BaseSamplingMethod")
        .doc() = R"pdoc(
            Base class for sampling strategies.

            A sampling strategy specifies how a population is realized during simulation,
            for example whether particle properties are sampled explicitly per event or
            approximated by a phenomenological distribution.

            This class is an interface and is not intended to be instantiated directly.
        )pdoc";

    py::class_<ExplicitModel, std::shared_ptr<ExplicitModel>, BaseSamplingMethod>(module, "ExplicitModel")
        .def(py::init<>())
        .doc() = R"pdoc(
            Explicit particle based sampling strategy.

            This strategy indicates that particles should be handled explicitly rather than
            through an aggregate statistical approximation. It is intended for regimes where
            discrete particle arrivals and event to event variability matter.

            Typical use cases include rare populations (e.g., extracellular vesicles) or
            analyses that require event level interpretability.
        )pdoc";

    py::class_<GammaModel, std::shared_ptr<GammaModel>, BaseSamplingMethod>(module, "GammaModel")
        .def(
            py::init<size_t>(),
            py::arg("number_of_samples")
        )
        .def_readwrite(
            "number_of_samples",
            &GammaModel::number_of_samples,
            R"pdoc(
                Number of random variates produced per sampling call.

                This controls the number of samples drawn from the underlying Gamma distribution
                per simulated time bin. Increasing this can improve approximation accuracy at the
                cost of increased runtime.
            )pdoc"
        )
        .doc() = R"pdoc(
            Gamma distribution sampling strategy.

            This strategy approximates population to detector coupling using a single Gamma
            distribution fitted from the population property distributions and the coupling model.

            Conceptually, for each simulated time bin:

                1. A signal amplitude is drawn from a Gamma distribution.
                2. The Gamma parameters are derived from the population diameter distribution,
                refractive index distribution, and the optical coupling model.

            This is a phenomenological approximation. It does not simulate discrete particle
            arrivals and therefore trades physical interpretability for speed.

            Appropriate for abundant populations (e.g., cells) at high event rates.
            Not recommended for rare populations where discreteness and per particle variability
            shape the observed signal statistics.

            Parameters
            ----------
            number_of_samples : int
                Number of random variates produced per sampling call.
        )pdoc";

    py::class_<BasePopulation, std::shared_ptr<BasePopulation>>(module, "BasePopulation")
        .def_readwrite(
            "name",
            &BasePopulation::name
        )
        .def_readwrite(
            "sampling_method",
            &BasePopulation::sampling_method
        )
        .def(
            "dilute",
            &BasePopulation::dilute,
            py::arg("dilution_factor"),
            R"pdoc(
                Dilute the population by updating its concentration.

                This divides the population concentration by the provided dilution factor.

                Parameters
                ----------
                dilution_factor : float
                    Factor by which concentration is reduced. Must be positive.
            )pdoc"
        )
        .def_property(
            "concentration",
            [ureg](const BasePopulation &population) {
                py::object concentration_with_units = py::float_(population.concentration) * ureg.attr("particle / liter");
                return concentration_with_units;
            },
            [](BasePopulation &population, py::object concentration) {
                double concentration_value = concentration.attr("to")("particle / liter").attr("magnitude").cast<double>();
                population.concentration = concentration_value;
            },
            R"pdoc(
                Population concentration.

                Returns
                -------
                pint.Quantity
                    Concentration expressed in particle / liter.
            )pdoc"
        )
        .def(
            "get_effective_concentration",
            [ureg](const BasePopulation &population) {
                double effective_concentration = population.get_effective_concentration();
                py::object effective_concentration_with_units = py::float_(effective_concentration) * ureg.attr("particle / liter");
                return effective_concentration_with_units;
            },
            R"pdoc(
                Return the effective concentration used for simulation.

                This allows derived populations to implement concentration corrections
                (e.g., gating, viability fractions, or other effective yield models) while
                preserving the stored nominal concentration.

                Returns
                -------
                pint.Quantity
                    Effective concentration expressed in particle / liter.
                )pdoc"
                        )
                        .doc() = R"pdoc(
                Base class for particle populations.

                A population is defined by:

                    - A name
                    - A nominal concentration (particle / liter)
                    - A sampling strategy (BaseSamplingMethod)

                Concrete populations extend this base class with distributions describing
                particle physical properties, and typically provide methods to sample those
                properties in a vectorized manner.

                Notes
                -----
                The stored concentration is unitless in C++ and interpreted as particle / liter
                at the Python boundary.
            )pdoc";

    py::class_<SpherePopulation, std::shared_ptr<SpherePopulation>, BasePopulation>(module, "SpherePopulation")
        .def(
            py::init(
                [ureg](
                    const std::string &name,
                    py::object &concentration,
                    py::object &medium_refractive_index_obj,
                    py::object &refractive_index_obj,
                    py::object &diameter_obj,
                    std::shared_ptr<BaseSamplingMethod> sampling_method
                ) {
                    std::shared_ptr<BaseDistribution> medium_refractive_index =
                        as_distribution(medium_refractive_index_obj, "RIU");

                    std::shared_ptr<BaseDistribution> refractive_index =
                        as_distribution(refractive_index_obj, "RIU");

                    std::shared_ptr<BaseDistribution> diameter =
                        as_distribution(diameter_obj, "meter");

                    return std::make_shared<SpherePopulation>(
                        name,
                        concentration.attr("to")("particle / liter").attr("magnitude").cast<double>(),
                        std::move(medium_refractive_index),
                        std::move(refractive_index),
                        std::move(diameter),
                        std::move(sampling_method)
                    );
                }
            ),
            py::arg("name"),
            py::arg("concentration"),
            py::arg("medium_refractive_index"),
            py::arg("refractive_index"),
            py::arg("diameter"),
            py::arg("sampling_method") = std::make_shared<ExplicitModel>(),
            R"pdoc(
                Spherical particle population.

                This population represents homogeneous spheres characterized by:

                    - Medium refractive index distribution
                    - Particle refractive index distribution
                    - Particle diameter distribution

                Parameters
                ----------
                name : str
                    Human readable population name.
                concentration : pint.Quantity
                    Particle concentration. Must be convertible to particle / liter.
                medium_refractive_index : BaseDistribution
                    Distribution for the surrounding medium refractive index (RIU).
                refractive_index : BaseDistribution
                    Distribution for the particle refractive index (RIU).
                diameter : BaseDistribution
                    Distribution for particle diameter (length).
                sampling_method : BaseSamplingMethod
                    Strategy controlling how the population contributes to simulated signals.
            )pdoc"
        )
        .def(
            "sample",
            [ureg](const SpherePopulation &population, const size_t number_of_samples) {
                py::dict samples_with_units;

                std::vector<size_t> shape = {number_of_samples};

                samples_with_units["MediumRefractiveIndex"] =
                    vector_move_from_numpy(population.medium_refractive_index->sample(number_of_samples), shape) * ureg.attr("RIU");

                samples_with_units["RefractiveIndex"] =
                    vector_move_from_numpy(population.refractive_index->sample(number_of_samples), shape) * ureg.attr("RIU");

                samples_with_units["Diameter"] =
                    vector_move_from_numpy(population.diameter->sample(number_of_samples), shape) * ureg.attr("meter");

                return samples_with_units;
            },
            py::arg("number_of_samples"),
            R"pdoc(
                Sample particle properties from the population distributions.

                Parameters
                ----------
                number_of_samples : int
                    Number of particles to sample.

                Returns
                -------
                dict[str, pint.Quantity]
                    Dictionary containing sampled arrays with units:

                    - "MediumRefractiveIndex" : RIU
                    - "RefractiveIndex" : RIU
                    - "Diameter" : meter
                )pdoc"
                        )
                        .doc() = R"pdoc(
                Spherical population with distribution based physical parameters.

                See Also
                --------
                CoreShellPopulation : population with separate core and shell properties.
            )pdoc";

    py::class_<CoreShellPopulation, std::shared_ptr<CoreShellPopulation>, BasePopulation>(module, "CoreShellPopulation")
        .def(
            py::init<>(
                [](
                    const std::string &name,
                    const py::object &concentration,
                    const std::shared_ptr<BaseDistribution> &medium_refractive_index,
                    const std::shared_ptr<BaseDistribution> &core_refractive_index,
                    const std::shared_ptr<BaseDistribution> &shell_refractive_index,
                    const std::shared_ptr<BaseDistribution> &core_diameter,
                    const std::shared_ptr<BaseDistribution> &shell_thickness,
                    const std::shared_ptr<BaseSamplingMethod> &sampling_method
                ) {
                    return std::make_shared<CoreShellPopulation>(
                        name,
                        concentration.attr("to")("particle / liter").attr("magnitude").cast<double>(),
                        std::move(medium_refractive_index),
                        std::move(core_refractive_index),
                        std::move(shell_refractive_index),
                        std::move(core_diameter),
                        std::move(shell_thickness),
                        std::move(sampling_method)
                    );
                }
            ),
            py::arg("name"),
            py::arg("concentration"),
            py::arg("medium_refractive_index"),
            py::arg("core_refractive_index"),
            py::arg("shell_refractive_index"),
            py::arg("core_diameter"),
            py::arg("shell_thickness"),
            py::arg("sampling_method") = std::make_shared<ExplicitModel>(),
            R"pdoc(
                Core shell spherical particle population.

                This population represents spheres composed of a core and a shell, characterized by:

                    - Medium refractive index distribution
                    - Core refractive index distribution
                    - Shell refractive index distribution
                    - Core diameter distribution
                    - Shell thickness distribution

                Parameters
                ----------
                name : str
                    Human readable population name.
                concentration : pint.Quantity
                    Particle concentration. Must be convertible to particle / liter.
                medium_refractive_index : BaseDistribution
                    Distribution for surrounding medium refractive index (RIU).
                core_refractive_index : BaseDistribution
                    Distribution for the core refractive index (RIU).
                shell_refractive_index : BaseDistribution
                    Distribution for the shell refractive index (RIU).
                core_diameter : BaseDistribution
                    Distribution for core diameter (length).
                shell_thickness : BaseDistribution
                    Distribution for shell thickness (length).
                sampling_method : BaseSamplingMethod
                    Strategy controlling how the population contributes to simulated signals.
            )pdoc"
        )
        .def(
            "sample",
            [ureg](const CoreShellPopulation &population, const size_t number_of_samples) {
                py::dict samples_with_units;

                std::vector<size_t> shape = {number_of_samples};

                samples_with_units["MediumRefractiveIndex"] =
                    vector_move_from_numpy(population.medium_refractive_index->sample(number_of_samples), shape) * ureg.attr("RIU");

                samples_with_units["CoreRefractiveIndex"] =
                    vector_move_from_numpy(population.core_refractive_index->sample(number_of_samples), shape) * ureg.attr("RIU");

                samples_with_units["ShellRefractiveIndex"] =
                    vector_move_from_numpy(population.shell_refractive_index->sample(number_of_samples), shape) * ureg.attr("RIU");

                samples_with_units["CoreDiameter"] =
                    vector_move_from_numpy(population.core_diameter->sample(number_of_samples), shape) * ureg.attr("meter");

                samples_with_units["ShellThickness"] =
                    vector_move_from_numpy(population.shell_thickness->sample(number_of_samples), shape) * ureg.attr("meter");

                return samples_with_units;
            },
            py::arg("number_of_samples"),
            R"pdoc(
                Sample particle properties from the population distributions.

                Parameters
                ----------
                number_of_samples : int
                    Number of particles to sample.

                Returns
                -------
                dict[str, pint.Quantity]
                    Dictionary containing sampled arrays with units:

                    - "MediumRefractiveIndex" : RIU
                    - "CoreRefractiveIndex" : RIU
                    - "ShellRefractiveIndex" : RIU
                    - "CoreDiameter" : meter
                    - "ShellThickness" : meter
                )pdoc"
                        )
                        .doc() = R"pdoc(
                Core shell population with distribution based physical parameters.

                The shell thickness is sampled independently from the core diameter. If you need
                a constrained relationship (e.g., total diameter fixed), implement a dedicated
                distribution or a custom population class that enforces the constraint.
            )pdoc";
}
