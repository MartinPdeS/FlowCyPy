import numpy as np


def coupling_model(diameter, refractive_index, medium_refractive_index):
    """
    Basic scattering model amplitude ∝ d^6 * contrast_factor.

    Replace this with your Mie-based detector-coupled model when desired.
    """
    d_m = diameter.to("meter").magnitude
    n = refractive_index.to("RIU").magnitude

    relative = n / medium_refractive_index
    contrast = ((relative**2 - 1) / (relative**2 + 2)) ** 2

    return d_m**6 * contrast


class GammaModel:
    def __init__(self, mc_samples):
        self.mc_samples = mc_samples

    def process_population(self):
        """
        For each population, compute:
            - expected particles per time bin
            - amplitude distribution moments
            - whether gamma shortcut or explicit sampling will be used
        """
        expected = (
            (self.population.particle_count * self.interrogation_volume_per_time_bin)
            .to("particle")
            .magnitude
        )

        diameter_sample = self.population.diameter.generate(self.mc_samples)
        refractive_index_sample = self.population.refractive_index.generate(
            self.mc_samples
        )
        medium_refractive_index_sample = (
            np.ones_like(refractive_index_sample) * self.medium_refractive_index
        )

        amps = coupling_model(
            diameter=diameter_sample,
            refractive_index=refractive_index_sample,
            medium_refractive_index=medium_refractive_index_sample,
        )
        mean_amp = float(np.mean(amps))
        mean_sq = float(np.mean(amps**2))

        self.stats = {
            "expected_per_bin": expected,
            "mean_amp": mean_amp,
            "mean_sq_amp": mean_sq,
            "diameter_samples": diameter_sample,
            "refractive_index_samples": refractive_index_sample,
            "amplitude_samples": amps,
        }

    def sample(self):
        """
        Gamma approximation for dense population:
        Match mean and variance of compound Poisson sum.
        """
        expected = self.stats["expected_per_bin"]
        mean = self.stats["mean_amp"]
        mean_sq = self.stats["mean_sq_amp"]

        mean_sum = expected * mean
        var_sum = expected * mean_sq

        if var_sum <= 0 or mean_sum <= 0:
            return 0.0

        shape = mean_sum**2 / var_sum
        scale = var_sum / mean_sum

        return np.random.gamma(shape=shape, scale=scale)


class ExplicitModel:
    """
    Explicit compound Poisson model for a particle population.

    For each time bin:

        1. Draw the number of particles in the bin from a Poisson
           distribution whose mean is

               expected_number_of_particles_per_time_bin
                   = particle_count * interrogation_volume_per_time_bin

        2. For each of these particles, sample its diameter and
           refractive index from the provided distributions.

        3. Compute its amplitude with `coupling_model` and sum all
           amplitudes in the bin.

    This preserves the discrete, particle-resolved nature of the signal
    and is well suited for rare populations such as EVs.
    """

    def __init__(self):
        """
        Parameters
        ----------
        interrogation_volume_per_time_bin :
            Pint Quantity, effective volume sampled in one time bin.

        refractive_index :
            Distribution object with .generate(n) → pint array of RI.

        diameters :
            Distribution object with .generate(n) → pint array of sizes.

        particle_count :
            Pint Quantity concentration (for example particle / milliliter).

        medium_refractive_index :
            Scalar refractive index of the medium. Passed to
            `coupling_model` as an array for convenience.
        """
        pass

    def sample(self):
        """
        Explicit compound Poisson sampling for this population in a
        single time bin.

        Steps:
            1. Draw the number of particles from Poisson(expected_per_bin).
            2. If zero, return 0.0.
            3. Otherwise, sample diameters and refractive indices for
               each particle, compute amplitudes, and sum.

        Returns
        -------
        float
            Total amplitude contributed by this population in one time
            bin.
        """
        expected = self.stats["expected_per_bin"]

        number_of_particles = np.random.poisson(expected)
        if number_of_particles <= 0:
            return 0.0

        diameter_sample = self.population.diameter.generate(number_of_particles)
        refractive_index_sample = self.population.refractive_index.generate(
            number_of_particles
        )
        medium_refractive_index_sample = (
            np.ones_like(refractive_index_sample) * self.medium_refractive_index
        )

        amplitudes = coupling_model(
            diameter=diameter_sample,
            refractive_index=refractive_index_sample,
            medium_refractive_index=medium_refractive_index_sample,
        )

        return float(amplitudes.sum())
