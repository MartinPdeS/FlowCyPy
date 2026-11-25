#include "populations.h"


double SpherePopulation::get_effective_concentration() const {
    double probability_diameter = diameter->proportion_within_cutoffs();
    double probability_refractive_index = refractive_index->proportion_within_cutoffs();
    return concentration * probability_diameter * probability_refractive_index;
}

double CoreShellPopulation::get_effective_concentration() const {
    double probability_core_diameter = core_diameter->proportion_within_cutoffs();
    double probability_shell_thickness = shell_thickness->proportion_within_cutoffs();
    double probability_core_refractive_index = core_refractive_index->proportion_within_cutoffs();
    double probability_shell_refractive_index = shell_refractive_index->proportion_within_cutoffs();
    return concentration * probability_core_diameter * probability_shell_thickness * probability_core_refractive_index * probability_shell_refractive_index;
}
