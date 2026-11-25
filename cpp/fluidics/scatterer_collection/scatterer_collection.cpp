#include "scatterer_collection.h"

#include <cmath>
#include <stdexcept>

std::vector<double> ScattererCollection::get_population_ratios() const {
    double total_concentration = 0.0;
    for (const auto& population : populations) {
        total_concentration += population->concentration;
    }

    if (total_concentration == 0.0) {
        throw std::invalid_argument(
            "Cannot compute population ratios with zero total particle count."
        );
    }

    std::vector<double> ratios;
    ratios.reserve(populations.size());
    for (const auto& population : populations) {
        ratios.push_back(population->concentration / total_concentration);
    }
    return ratios;
}

ScattererCollection& ScattererCollection::add_population(
    const std::vector<std::shared_ptr<BasePopulation>>& population
) {
    populations.insert(populations.end(), population.begin(), population.end());
    return *this;
}

std::vector<double> ScattererCollection::concentrations() const {
    std::vector<double> values;
    values.reserve(populations.size());
    for (const auto& population : populations) {
        values.push_back(population->concentration);
    }
    return values;
}

void ScattererCollection::set_concentrations(double value) {
    for (auto& population : populations) {
        population->concentration = value;
    }
}

void ScattererCollection::set_concentrations(
    const std::vector<double>& values
) {
    if (values.size() != populations.size()) {
        throw std::invalid_argument(
            "The length of the values list must match the number of populations."
        );
    }

    for (std::size_t index = 0; index < populations.size(); ++index) {
        populations[index]->concentration = values[index];
    }
}

void ScattererCollection::dilute(double factor) {
    if (!std::isfinite(factor) || factor <= 0.0) {
        throw std::invalid_argument(
            "Dilution factor must be finite and greater than zero."
        );
    }

    for (auto& population : populations) {
        population->dilute(factor);
    }
}
