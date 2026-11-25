#pragma once

#include <memory>
#include <vector>

#include <fluidics/populations/populations.h>

/**
 * @brief Container for the particle populations present in a sample.
 *
 * The collection owns shared references to the population objects supplied by
 * Python.  It provides the small set of operations that apply to all
 * populations, while the populations themselves retain their physical
 * distributions and sampling models.
 */
class ScattererCollection {
public:
    std::vector<std::shared_ptr<BasePopulation>> populations;

    ScattererCollection() = default;

    explicit ScattererCollection(
        std::vector<std::shared_ptr<BasePopulation>> populations
    ) : populations(std::move(populations)) {}

    /** Return each population's fraction of the total concentration. */
    std::vector<double> get_population_ratios() const;

    /** Append one or more populations and return this collection. */
    ScattererCollection& add_population(
        const std::vector<std::shared_ptr<BasePopulation>>& population
    );

    /** Return the nominal concentrations of all populations. */
    std::vector<double> concentrations() const;

    /** Set all concentrations to the same value. */
    void set_concentrations(double value);

    /** Set each concentration independently. */
    void set_concentrations(const std::vector<double>& values);

    /** Divide every concentration by a finite, positive factor. */
    void dilute(double factor);
};
