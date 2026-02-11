class GammaModel:
    """
    Gamma model emulate coupling of a particle population to the detector with a single Gamma distribution.

    For each time bin:
        1. Draw the signal amplitude from a Gamma distribution whose shape and scale parameters are
           fitted to the population's diameter and refractive index distributions and the coupling model.

        2. This is a phenomenological model that captures the overall signal distribution without explicitly modeling individual particles. It is well suited for abundant populations such as cells. However, it may not be appropriate for rare populations such as EVs, where the discrete nature of particle arrivals and their individual properties can significantly impact the signal distribution.

    This is a phenomenological model that captures the overall signal distribution without explicitly modeling individual particles. It is well suited for abundant populations such as cells. However, it may not

    """

    def __init__(self, mc_samples: int = 10_000):
        """
        Initialize the GammaModel with the specified number of Monte Carlo samples.

        Parameters
        ----------
        mc_samples : int
            The number of Monte Carlo samples to use for fitting the Gamma distribution.
        """
        self.mc_samples = mc_samples


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
