from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class FractionSelection:
    """
    Simple fraction selection model for sample cleanup steps such as SEC.

    This model intentionally note does not implement chromatographic physics.
    It represents the net effect of selecting a fraction by:

        1. Optionally scaling population concentration by a multiplicative factor
        2. Enforcing a hard minimum diameter cutoff during sampling

    This is sufficient to emulate a common practical use case:
    reducing small particle backgrounds while keeping the rest of the flow
    cytometry pipeline unchanged.

    Parameters
    ----------
    minimum_diameter
        Any sampled diameter smaller than this value is rejected.

        Provide a pint Quantity with units of length, for example:
            70 * ureg.nanometer

    concentration_multiplier
        Optional multiplier applied to population.particle_count in place.

        Example:
            0.4 for EV recovery
            0.05 for lipoprotein depletion

    oversample_factor
        Candidate oversampling factor used by rejection sampling.

    maximum_rounds
        Maximum rejection sampling rounds before raising an error.

    random_seed
        Optional seed for reproducible filtering.
    """

    minimum_diameter: float
    concentration_multiplier: Optional[float] = None
    oversample_factor: int = 4
    maximum_rounds: int = 50
    random_seed: Optional[int] = None

    def apply_in_place(self, population_object):
        """
        Apply the fraction selection to a population in place.

        This function expects:
            - population_object.particle_count: pint Quantity
            - population_object.diameter.generate(n): returns pint Quantity of diameters

        After applying, calls to population_object.diameter.generate(n)
        will never return values smaller than minimum_diameter.
        """
        if self.concentration_multiplier is not None:
            population_object.particle_count = population_object.particle_count * float(
                self.concentration_multiplier
            )

        population_object.diameter = _MinimumDiameterFilteredDistribution(
            base_distribution=population_object.diameter,
            minimum_diameter=self.minimum_diameter,
            oversample_factor=self.oversample_factor,
            maximum_rounds=self.maximum_rounds,
            random_seed=self.random_seed,
        )
        return population_object


class _MinimumDiameterFilteredDistribution:
    """
    Internal distribution wrapper that enforces a hard minimum diameter cutoff.
    """

    def __init__(
        self,
        base_distribution,
        minimum_diameter,
        oversample_factor: int,
        maximum_rounds: int,
        random_seed: int | None,
    ):
        self.base_distribution = base_distribution
        self.minimum_diameter = minimum_diameter
        self.oversample_factor = int(oversample_factor)
        self.maximum_rounds = int(maximum_rounds)
        self.random_generator = np.random.default_rng(random_seed)

    def generate(self, number_of_samples: int):
        number_of_samples = int(number_of_samples)
        if number_of_samples <= 0:
            raise ValueError("number_of_samples must be positive")

        accepted = []
        remaining = number_of_samples

        for _ in range(self.maximum_rounds):
            number_to_draw = max(1, remaining * self.oversample_factor)
            candidates = self.base_distribution.generate(number_to_draw)

            keep = candidates >= self.minimum_diameter
            kept = candidates[keep]

            if kept.size > 0:
                accepted.append(kept)
                remaining -= kept.size

            if remaining <= 0:
                break

        if remaining > 0:
            raise RuntimeError(
                "Too few samples above minimum_diameter. "
                "Lower the cutoff or increase oversample_factor or maximum_rounds."
            )

        return np.concatenate(accepted)[:number_of_samples]
