from TypedUnit import Length

from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing


@dataclass(config=config_dict)
class FluorescenceLabel(StrictDataclassMixing):
    """
    Describe a fluorescent label attached to a given particle population.

    This is an intrinsic property of the biology, not the instrument.
    The instrument (laser, filters, detector) will read out this label
    and convert it into an analog signal.

    Parameters
    ----------
    name
        A short human-readable name, e.g. "FITC", "PE", "AF647", "CD63-FITC".
        Used for channel naming in output tables and plots.

    excitation_pref
        Wavelength where this label is efficiently excited.
        This is not the actual laser necessarily, it's the ideal excitation line.
        Pint quantity, e.g. 488 * ureg.nanometer.

    emission_peak
        Center wavelength of the emission spectrum (peak of emission).
        Pint quantity, e.g. 520 * ureg.nanometer.

    emission_FWHM
        Approximate full-width at half-maximum of the emission spectrum.
        Pint quantity, e.g. 30 * ureg.nanometer.
        This will matter for bandpass overlap with the detector channel.

    quantum_yield
        Fraction of absorbed photons that become emitted photons, [0,1].
        Dimensionless float.

    copies_per_particle
        How many fluorophores per particle.
        This is the big biological lever. It can be:
        - A scalar (all particles same copy number)
        - A Distribution-like object that can sample per-particle variation
          (log-normal etc.). Units: "counts per particle", dimensionless.

        Interpreted as number of active fluorophores bound per particle.

    brightness_scale
        Optional calibration-like scalar that lumps together:
        absorption cross section at excitation_pref,
        detection solid angle,
        and overall optical train transmission * detector gain
        (excluding per-channel variations handled elsewhere).
        Think of this as converting "copies_per_particle" to "photons/s on sensor".
        Default is 1.0, so you can leave actual scaling to the instrument model.

        Dimensionless float. You can tune this to match experimental MESF.

    bleaching_lifetime
        Optional characteristic bleaching timescale under illumination,
        e.g. 5 * ureg.millisecond.
        You can ignore it now, but it gives you a hook to implement
        bleaching-dependent signal loss for slow scans or repeated passes.

    Notes
    -----
    - The instrument code downstream should combine:
        copies_per_particle
        . quantum_yield
        . brightness_scale
        . laser power overlap
        . detector efficiency / filter transmission
      to turn this into an analog pulse height.

    - We keep spectral info (excitation_pref / emission_peak / emission_FWHM)
      because it will let us map a label to the right FluorChannel(s).
    """

    name: str

    excitation_pref: Length  # Pint Quantity expected: wavelength
    emission_peak: Length  # Pint Quantity expected: wavelength
    emission_FWHM: Length  # Pint Quantity expected: wavelength

    quantum_yield: float

    # copies_per_particle: Union[float, DistributionProtocol]
    # brightness_scale: float = 1.0
