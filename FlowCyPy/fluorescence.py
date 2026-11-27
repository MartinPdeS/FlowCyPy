"""Spectrally resolved fluorescence for explicitly sampled particles."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
import numpy as np
from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.opto_electronics.coupling_model import ScatteringModel
from FlowCyPy.opto_electronics.system import _next_noise_seed
from FlowCyPy.units import ureg


@dataclass(frozen=True, kw_only=True)
class Bandpass:
    """Ideal rectangular optical filter with inclusive edges.

    Parameters
    ----------
    center, width : length quantity
        Central wavelength and full passband width.
    """

    center: ureg.Quantity
    width: ureg.Quantity

    def __post_init__(self):
        """Check that both edges are positive physical wavelengths."""
        center = float(self.center.m_as("nm"))
        width = float(self.width.m_as("nm"))
        if not np.isfinite([center, width]).all() or not 0 < width < 2 * center:
            raise ValueError("Bandpass requires finite positive width and wavelengths.")

    def transmits(self, *, wavelength):
        """Return a boolean transmission mask for scalar or array wavelengths."""
        # Evaluate in one unit and allow one rounding step at each inclusive edge.
        center = self.center.m_as("nm")
        half_width = self.width.m_as("nm") / 2
        lower = np.nextafter(center - half_width, -np.inf)
        upper = np.nextafter(center + half_width, np.inf)
        values = wavelength.m_as("nm")
        return (lower <= values) & (values <= upper)


@dataclass(frozen=True, kw_only=True)
class Fluorophore:
    """Fluorophore with a discrete photon-emission spectrum.

    Parameters
    ----------
    name : str
        Dye identifier, unique among labels on a population.
    absorption_cross_section : area quantity or mapping of wavelength to area
        Molecular absorption cross section at the configured laser wavelength.
        With multiple lasers, supply one wavelength-keyed value per line.
    quantum_yield : float
        Mean emitted photons per absorbed photon, between zero and one.
    emission_wavelengths : length quantity, shape (n,)
        Representative wavelength of each emission bin.
    photon_weights : array-like, shape (n,)
        Relative integrated photon counts per bin. Weights are normalized internally.
        For a continuous spectrum, refine the bins near filter edges.
    lifetime : time quantity, optional
        Mean delay from absorption to emission for a single exponential decay.
        Omission or a zero duration gives prompt emission.
    """

    name: str
    absorption_cross_section: ureg.Quantity | Mapping
    quantum_yield: float
    emission_wavelengths: ureg.Quantity
    photon_weights: tuple[float, ...]
    lifetime: ureg.Quantity | None = None

    def __post_init__(self):
        """Validate the spectrum and retain an independent normalized copy."""
        if self.lifetime is not None:
            if not hasattr(self.lifetime, "m_as"):
                raise TypeError("lifetime requires a time quantity.")
            seconds = np.asarray(self.lifetime.m_as("second"))
            if seconds.ndim or not np.isfinite(seconds) or seconds < 0:
                raise ValueError(
                    "lifetime must be a finite, nonnegative scalar duration."
                )
        wavelengths = np.array(
            self.emission_wavelengths.m_as("nm"), dtype=float, copy=True
        )
        weights = np.asarray(self.photon_weights, dtype=float)
        areas = self.absorption_cross_section
        if isinstance(areas, Mapping):
            if not areas:
                raise ValueError("Provide at least one absorption cross section.")
            for wavelength in areas:
                nm = float(wavelength.m_as("nm"))
                if not np.isfinite(nm) or nm <= 0:
                    raise ValueError("Excitation wavelengths must be finite and positive.")
            object.__setattr__(self, "absorption_cross_section", MappingProxyType(dict(areas)))
            areas = areas.values()
        else:
            areas = (areas,)
        for value in areas:
            area = float(value.m_as("meter**2"))
            if not self.name.strip() or not np.isfinite(area) or area < 0:
                raise ValueError("Provide a dye name and finite nonnegative absorption cross sections.")
        if not 0 <= self.quantum_yield <= 1:
            raise ValueError("quantum_yield must be between zero and one.")
        if (
            wavelengths.ndim != 1
            or not wavelengths.size
            or wavelengths.shape != weights.shape
            or not np.isfinite(wavelengths).all()
            or np.any(wavelengths <= 0)
            or not np.isfinite(weights.sum())
            or np.any(weights < 0)
            or weights.sum() <= 0
        ):
            raise ValueError(
                "Provide positive emission wavelengths and matching nonnegative photon weights."
            )
        spectrum = wavelengths * ureg.nm
        spectrum.magnitude.setflags(write=False)
        object.__setattr__(self, "emission_wavelengths", spectrum)
        object.__setattr__(self, "photon_weights", tuple(weights / weights.sum()))


@dataclass(frozen=True, kw_only=True)
class Label:
    """Fluorescent labeling of one population.

    Parameters
    ----------
    fluorophore : Fluorophore
        Optical properties shared by the labeled particles.
    molecules_per_particle : int or BaseDistribution, optional
        Fixed count or dimensionless count distribution, sampled once per event.
        Distribution samples are rounded to the nearest integer.
    molecules_per_area : inverse area quantity, optional
        Mean surface density of bound fluorophores. Counts are Poisson draws
        with mean density times the individual particle’s outer surface area.
    molecules_per_volume : inverse volume quantity, optional
        Mean density throughout the sphere enclosed by the outer diameter.
        Counts are Poisson draws with mean density times particle volume.
        Supply exactly one loading parameter per label.
    """

    fluorophore: Fluorophore
    molecules_per_particle: int | distributions.BaseDistribution | None = None
    molecules_per_area: ureg.Quantity | None = None
    molecules_per_volume: ureg.Quantity | None = None
    _rng: np.random.Generator | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        """Check dye and count configuration before sampling."""
        if not isinstance(self.fluorophore, Fluorophore):
            raise TypeError("fluorophore must be a Fluorophore.")
        loadings = (self.molecules_per_particle, self.molecules_per_area, self.molecules_per_volume)
        if sum(value is not None for value in loadings) != 1:
            raise ValueError("Specify exactly one of molecules_per_particle, molecules_per_area and molecules_per_volume.")
        for name, density, unit in (
            ("molecules_per_area", self.molecules_per_area, "1 / meter**2"),
            ("molecules_per_volume", self.molecules_per_volume, "1 / meter**3"),
        ):
            if density is None:
                continue
            if not hasattr(density, "m_as"):
                raise TypeError(f"{name} requires a quantity convertible to {unit}.")
            magnitude = np.asarray(density.m_as(unit))
            if magnitude.ndim or not np.isfinite(magnitude) or magnitude < 0:
                raise ValueError(f"{name} must be a finite nonnegative scalar.")
            object.__setattr__(self, "_rng", np.random.default_rng())
            return
        count = self.molecules_per_particle
        if not isinstance(count, distributions.BaseDistribution) and (
            not isinstance(count, (int, np.integer))
            or isinstance(count, bool)
            or count < 0
        ):
            raise ValueError(
                "molecules_per_particle must be a nonnegative integer or distribution."
            )

    @property
    def column_name(self):
        """Event column containing this dye's molecule count."""
        return f"Label:{self.fluorophore.name}"

    def _seed(self, *, value):
        """Seed a stochastic molecule count for a repeatable acquisition."""
        if self._rng is not None:
            object.__setattr__(self, "_rng", np.random.default_rng(value))
        elif isinstance(self.molecules_per_particle, distributions.BaseDistribution):
            self.molecules_per_particle.seed(value)

    def _sample(self, *, size, properties=None):
        """Return dimensionless molecule counts for a block of events."""
        if self._rng is not None:
            if properties is None:
                raise RuntimeError("Geometry-dependent labeling requires sampled geometry. Rebuild the FlowCyPy fluidics extension.")
            if "Diameter" in properties:
                diameter = properties["Diameter"]
            else:
                diameter = properties["CoreDiameter"] + 2 * properties["ShellThickness"]
            if np.any(diameter.magnitude < 0):
                raise ValueError("Geometry-dependent labeling requires nonnegative outer diameters.")
            if self.molecules_per_area is not None:
                expected = self.molecules_per_area * np.pi * diameter**2
            else:
                expected = self.molecules_per_volume * (np.pi / 6) * diameter**3
            counts = self._rng.poisson(expected.m_as(""))
        elif isinstance(self.molecules_per_particle, distributions.BaseDistribution):
            counts = self.molecules_per_particle.sample(size).m_as("")
            if not np.isfinite(counts).all() or np.any(counts < 0):
                raise ValueError(
                    "Label count distribution produced invalid molecule counts."
                )
            counts = np.rint(counts)
        else:
            counts = np.full(size, self.molecules_per_particle)
        return counts * ureg.dimensionless


def _validate_labels(*, labels, sampling_method):
    """Validate labels supplied by the native population constructors."""
    labels = tuple(labels)
    if not isinstance(sampling_method, populations.ExplicitModel):
        raise TypeError("Fluorescent labels require ExplicitModel.")
    if not all(isinstance(label, Label) for label in labels):
        raise TypeError("labels must contain Label objects.")
    if len({label.column_name for label in labels}) != len(labels):
        raise ValueError("Fluorophore names must be unique within a population.")
    return labels


def _couple_channel(*, events, source, detector, compute_cross_section):
    """Write the peak power and fluorescence components of one detector."""
    for block, scatter, emissions, total in _line_powers(
        events=events, source=source, detector=detector, compute_cross_section=compute_cross_section
    ):
        if emissions:
            block.metadata.setdefault("FluorescencePower", {})[detector.name] = (scatter, emissions)
        block.set_quantity_column(detector.name, total)


def _couple_lasers(*, events, beam, detector, compute_cross_section):
    """Combine excitation lines on the same events and retain their photon wavelengths."""
    name = detector.name
    totals = {}
    for index, laser in enumerate(beam.lasers):
        source = beam if index == 0 else type(beam)(
            wavelength=laser.wavelength, optical_power=laser.optical_power,
            waist_y=beam.waist_y, waist_z=beam.waist_z, polarization=beam.polarization,
        )
        nm = float(laser.wavelength.m_as("nm"))
        suffix = f"[{nm:g} nm]"
        for block, scatter, emissions, total in _line_powers(
            events=events, source=source, detector=detector,
            compute_cross_section=compute_cross_section, multiple=True,
        ):
            block.set_quantity_column(name + suffix, total)
            if compute_cross_section:
                block.set_quantity_column("Csca" + suffix, block.get_quantity("Csca"))
            if index == 0:
                totals[block.name] = total.copy()
                block.metadata.setdefault("FluorescencePower", {})[name] = (0 * total, [])
            else:
                totals[block.name] += total
            components = block.metadata["FluorescencePower"][name][1]
            if "scatter" in detector.signals:
                components.append((scatter, {nm: 1.0}, 0.0, index))
            for amplitude, weights, *delay in emissions:
                components.append((amplitude, weights, delay[0] if delay else 0.0, index))
    for block in events:
        if not block.empty:
            block.set_quantity_column(name, totals[block.name])
            if compute_cross_section:
                first_nm = beam.wavelength.m_as("nm")
                block.set_quantity_column("Csca", block.get_quantity(f"Csca[{first_nm:g} nm]"))


def _line_powers(*, events, source, detector, compute_cross_section, multiple=False):
    """Yield scatter, spectrally resolved fluorescence, and total power per population."""
    accepts_scatter = "scatter" in detector.signals and (
        detector.optical_filter is None
        or detector.optical_filter.transmits(wavelength=source.wavelength)
    )
    if accepts_scatter or compute_cross_section:
        ScatteringModel(source=source, detector=detector).run(
            events, compute_cross_section=compute_cross_section
        )

    for block in events:
        if block.empty:
            continue
        scatter = (
            block.get_quantity(detector.name)
            if accepts_scatter
            else np.zeros(len(block)) * ureg.watt
        )
        total = scatter.copy()
        emissions = []
        labels = block.population.labels if "fluorescence" in detector.signals else ()
        if labels:
            if not isinstance(block.sampling_method, populations.ExplicitModel):
                raise TypeError("Fluorescent labels require ExplicitModel.")
            irradiance = source.get_irradiance_signal(
                x=block.get_quantity("x"),
                y=block.get_quantity("y"),
                z=np.zeros(len(block)) * ureg.meter,
            ).m_as("W/m**2")
            inner, outer = (
                detector.cache_numerical_aperture,
                detector.numerical_aperture,
            )
            if not 0 <= inner <= outer <= 1:
                raise ValueError(
                    "Isotropic fluorescence collection in air requires 0 <= cache NA <= NA <= 1."
                )
            fraction = (np.sqrt(1 - inner**2) - np.sqrt(1 - outer**2)) / 2
        for label in labels:
            dye = label.fluorophore
            cross_section = dye.absorption_cross_section
            if isinstance(cross_section, Mapping):
                nm = source.wavelength.m_as("nm")
                matches = [value for line, value in cross_section.items()
                           if np.isclose(line.m_as("nm"), nm, rtol=1e-12, atol=0)]
                if len(matches) != 1:
                    raise ValueError(f"{dye.name} requires one absorption cross section at {nm:g} nm.")
                cross_section = matches[0]
            elif multiple:
                raise ValueError(f"Supply wavelength-specific absorption cross sections for {dye.name}.")
            dye_amplitude = (
                irradiance
                * cross_section.m_as("m**2")
                * block.get_quantity(label.column_name).magnitude
                * dye.quantum_yield
                * fraction
                * ureg.watt
            )
            spectral_weights = {}
            for wavelength, weight in zip(
                dye.emission_wavelengths, dye.photon_weights, strict=True
            ):
                if weight == 0 or (
                    detector.optical_filter
                    and not detector.optical_filter.transmits(wavelength=wavelength)
                ):
                    continue
                # Quantum yield counts photons. Convert their energy at emission.
                wavelength_nm = float(wavelength.m_as("nm"))
                power_weight = weight * source.wavelength.m_as("nm") / wavelength_nm
                spectral_weights[wavelength_nm] = (
                    spectral_weights.get(wavelength_nm, 0.0) + power_weight
                )
            if spectral_weights:
                total += dye_amplitude * sum(spectral_weights.values())
                lifetime = (
                    0.0 if dye.lifetime is None else float(dye.lifetime.m_as("second"))
                )
                component = (dye_amplitude, spectral_weights)
                emissions.append((*component, lifetime) if lifetime else component)
        yield block, scatter, emissions, total


def _decay_bin_averages(*, excitation, interval_seconds, lifetime_seconds):
    """Return mean emitted power per bin on the periodic acquisition window.

    Parameters
    ----------
    excitation : power quantity, shape (n,)
        Prompt power held constant within each uniform acquisition bin.
    interval_seconds, lifetime_seconds : float
        Bin width and positive exponential lifetime in seconds.

    Returns
    -------
    power quantity, shape (n,)
        Exact bin averages for this piecewise-constant excitation.
    """
    values = np.asarray(excitation.magnitude, dtype=float)
    if values.size < 2:
        return excitation
    ratio = interval_seconds / lifetime_seconds
    if not np.isfinite(ratio):
        return excitation
    if ratio == 0:
        return np.full_like(values, values.mean()) * excitation.units
    retention = np.exp(-ratio)
    excitation_fraction = -np.expm1(-ratio)
    previous_weight = excitation_fraction / ratio
    # Avoid cancellation in the first bin of a slow decay.
    current_weight = (
        ratio * (0.5 - ratio / 6 + ratio**2 / 24)
        if ratio < 1e-4
        else 1 - previous_weight
    )

    # Start in periodic steady state, including light from previous windows.
    # The weights run backward from the bin immediately before time zero.
    history = retention ** np.arange(values.size, dtype=float)
    state = np.average(values[::-1], weights=history)
    emitted = np.empty_like(values)
    for index, power in enumerate(values):
        emitted[index] = previous_weight * state + current_weight * power
        state = retention * state + excitation_fraction * power
    return emitted * excitation.units


def _apply_spectral_noise(*, source, detectors, power, emission, generator, bandwidth=None):
    """Apply each laser's RIN before lifetime response and photon shot noise.

    Spectral keys contain the detector, photon wavelength in nm and optionally
    lifetime in seconds and excitation laser index. In a multi-line beam the
    unassigned background has no excitation laser.
    """
    multi = source._has_multiple_lasers
    components = [(detector.name, None, 0.0, None if multi else 0) for detector in detectors]
    traces = [power[component[0]] for component in components]
    for key, trace in emission.items():
        name, wavelength, *details = key
        lifetime = details[0] if details else 0.0
        if len(details) > 2 or not np.isfinite(lifetime) or lifetime < 0:
            raise ValueError("Invalid spectral key or fluorescence lifetime.")
        laser_index = details[1] if len(details) == 2 else (None if multi else 0)
        components.append((name, wavelength, lifetime, laser_index))
        traces.append(trace)

    if source.include_rin_noise:
        for index, laser in enumerate(source.lasers):
            if laser.rin is None:
                continue
            positions = [i for i, component in enumerate(components) if component[3] == index]
            if not positions:
                continue
            noise_source = source
            if source._explicit_lasers:
                noise_bandwidth = source.bandwidth
                if not np.isfinite(noise_bandwidth.m_as("Hz")):
                    noise_bandwidth = bandwidth
                noise_source = type(source)(
                    wavelength=laser.wavelength, optical_power=laser.optical_power,
                    waist_y=source.waist_y, waist_z=source.waist_z,
                    rin=laser.rin, bandwidth=noise_bandwidth,
                )
            inputs = {str(i): traces[i] for i in positions}
            noisy = noise_source.add_rin_to_signal_dict(
                {"Time": power["Time"], **inputs}, seed=_next_noise_seed(generator=generator)
            )
            for i in positions:
                traces[i] = noisy[str(i)]
    combined = {"Time": power["Time"]}
    for (name, wavelength, lifetime, _), trace in zip(components, traces, strict=True):
        if lifetime and trace.size > 1:
            interval = (power["Time"][1] - power["Time"][0]).m_as("second")
            trace = _decay_bin_averages(
                excitation=trace, interval_seconds=interval, lifetime_seconds=lifetime
            )
        measured = trace
        if source.include_shot_noise:
            measured = source.add_shot_noise_to_signal(
                trace,
                power["Time"],
                seed=_next_noise_seed(generator=generator),
                wavelength=None if wavelength is None else wavelength * ureg.nm,
            )
        combined[name] = combined.get(name, 0 * ureg.watt) + measured
    return combined
