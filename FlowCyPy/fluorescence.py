import numpy as np
from TypedUnit import ureg, Quantity, Length, Area, Dimensionless


class Dye:
    """
    Single line fluorophore model with unity optics throughput.
    All attributes are unit-carrying quantities except quantum_yield which is dimensionless.
    """

    def __init__(
        self,
        name: str,
        absorption_cross_section: Area,
        quantum_yield: Dimensionless,
        excitation_wavelength: Length,
        emission_wavelength: Length,
    ) -> None:
        self.name = name
        self.absorption_cross_section = absorption_cross_section
        self.quantum_yield = float(quantum_yield)
        self.excitation_wavelength = excitation_wavelength
        self.emission_wavelength = emission_wavelength

    @property
    def wavelength_ratio_excitation_over_emission(self) -> Quantity:
        # Returns a dimensionless quantity
        return self.excitation_wavelength / self.emission_wavelength

    def __repr__(self) -> str:
        return (
            f"Dye(name='{self.name}', "
            f"absorption_cross_section={self.absorption_cross_section:~P}, "
            f"quantum_yield={self.quantum_yield:.3f}, "
            f"excitation_wavelength={self.excitation_wavelength:~P}, "
            f"emission_wavelength={self.emission_wavelength:~P})"
        )


class DyeLabelingModel:
    """
    Base class for mapping bead diameter to expected label count.
    All inputs and outputs are unit aware.
    expected_labels_given_diameter must return a dimensionless quantity (counts).
    """

    def expected_labels_given_diameter(self, diameter: Quantity) -> Quantity:
        raise NotImplementedError

    def sample_labels_given_diameter(self, diameter: Quantity) -> Quantity:
        """
        Default stochastic draw around the expectation.
        Returns a dimensionless quantity with units of 'count'.
        """
        expected_count = self.expected_labels_given_diameter(diameter)
        lam_value = expected_count.to(
            ureg.dimensionless
        ).magnitude  # Poisson parameter must be a float
        sampled = np.random.poisson(lam=lam_value)
        return sampled * ureg.dimensionless


class SurfaceDensityLabeling(DyeLabelingModel):
    """
    Labels reside on the surface. Expected count scales with surface area.
    density is counts per square meter.
    """

    def __init__(self, density: Quantity) -> None:
        self.density = density  # counts / m^2

    def expected_labels_given_diameter(self, diameter: Length) -> Quantity:
        # Surface area for a sphere expressed as A = pi * d^2
        surface_area = np.pi * (diameter**2)
        return self.density * surface_area  # dimensionless count quantity


class VolumeDensityLabeling(DyeLabelingModel):
    """
    Labels embedded in the volume. Expected count scales with volume.
    density is counts per cubic meter.
    """

    def __init__(self, density: Quantity) -> None:
        self.density = density  # counts / m^3

    def expected_labels_given_diameter(self, diameter: Length) -> Quantity:
        volume = (np.pi / 6.0) * (diameter**3)  # sphere volume in terms of diameter
        return self.density * volume  # dimensionless count quantity
