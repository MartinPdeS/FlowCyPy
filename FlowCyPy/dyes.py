"""Reference fluorophores with measurement sources in the fluorescence model guide."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import log
from FlowCyPy.fluorescence import Fluorophore
from FlowCyPy.units import ureg


@dataclass(frozen=True, kw_only=True)
class DyePreset:
    """Reference properties for a dye with single-exponential emission.

    Parameters
    ----------
    name : str
        Fluorophore name used in event records.
    absorption_maximum, emission_maximum : length quantity
        Approximate wavelengths of peak absorption and emission.
    peak_extinction_coefficient : float
        Decadic molar extinction coefficient at peak absorption in L mol⁻¹ cm⁻¹.
    quantum_yield : float
        Mean emitted photons per absorbed photon.
    lifetime : time quantity
        Mean delay between absorption and emission.
    """

    name: str
    absorption_maximum: ureg.Quantity
    emission_maximum: ureg.Quantity
    peak_extinction_coefficient: float
    quantum_yield: float
    lifetime: ureg.Quantity

    def __call__(self, *, relative_absorption: float | Mapping = 1.0) -> Fluorophore:
        """Build a dye for the configured lasers with one emission bin at the maximum.

        Parameters
        ----------
        relative_absorption : float or mapping of wavelength to float, optional
            Absorbance at the laser wavelength divided by peak absorbance.
            The default uses the peak cross section. For multiple lasers,
            provide a wavelength-keyed fraction for each excitation line.

        Returns
        -------
        Fluorophore
            Dye ready for a Label. Use measured photon weights for spillover studies.
        """
        fractions = relative_absorption.values() if isinstance(relative_absorption, Mapping) else (relative_absorption,)
        if not all(0 <= fraction <= 1 for fraction in fractions):
            raise ValueError("relative_absorption must be between zero and one.")
        # Beer–Lambert conversion from L/(mol cm) to m² per molecule.
        peak = self.peak_extinction_coefficient * 0.1 * log(10) / 6.02214076e23 * ureg.meter**2
        if isinstance(relative_absorption, Mapping):
            cross_section = {line: fraction * peak for line, fraction in relative_absorption.items()}
        else:
            cross_section = relative_absorption * peak
        return Fluorophore(
            name=self.name,
            absorption_cross_section=cross_section,
            quantum_yield=self.quantum_yield,
            lifetime=self.lifetime,
            emission_wavelengths=[self.emission_maximum.m_as("nm")] * ureg.nm,
            photon_weights=(1.0,),
        )


alexa_fluor_488 = DyePreset(
    name="Alexa Fluor 488",
    absorption_maximum=495 * ureg.nm,
    emission_maximum=519 * ureg.nm,
    peak_extinction_coefficient=73_000,
    quantum_yield=0.92,
    lifetime=4.1 * ureg.ns,
)

alexa_fluor_594 = DyePreset(
    name="Alexa Fluor 594",
    absorption_maximum=590 * ureg.nm,
    emission_maximum=617 * ureg.nm,
    peak_extinction_coefficient=92_000,
    quantum_yield=0.66,
    lifetime=3.9 * ureg.ns,
)

alexa_fluor_647 = DyePreset(
    name="Alexa Fluor 647",
    absorption_maximum=650 * ureg.nm,
    emission_maximum=668 * ureg.nm,
    peak_extinction_coefficient=270_000,
    quantum_yield=0.33,
    lifetime=1.0 * ureg.ns,
)

fitc = DyePreset(
    name="FITC",
    absorption_maximum=494 * ureg.nm,
    emission_maximum=518 * ureg.nm,
    peak_extinction_coefficient=70_000,
    quantum_yield=0.92,
    lifetime=4.1 * ureg.ns,
)

atto_647n = DyePreset(
    name="ATTO 647N",
    absorption_maximum=646 * ureg.nm,
    emission_maximum=664 * ureg.nm,
    peak_extinction_coefficient=150_000,
    quantum_yield=0.65,
    lifetime=3.5 * ureg.ns,
)
