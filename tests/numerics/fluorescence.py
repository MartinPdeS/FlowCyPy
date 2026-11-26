"""Hard optical filters and fluorescence in an explicit-particle acquisition."""

import numpy as np
import pytest
from FlowCyPy.detectors.photomultipliers import pmt
from FlowCyPy.dyes import alexa_fluor_488, alexa_fluor_594, alexa_fluor_647, atto_647n, fitc
from FlowCyPy.fluidics import distributions, populations
from FlowCyPy.fluorescence import Bandpass, Fluorophore, Label, _decay_bin_averages
from FlowCyPy.opto_electronics import Amplifier
from FlowCyPy.systems.bd import facs_canto
from FlowCyPy.units import ureg


def test_bandpass_edges():
    band = Bandpass(center=0.530 * ureg.micrometer, width=30 * ureg.nm)
    wavelengths = np.array([488, 514.99, 515, 530, 545, 545.01]) * ureg.nm
    np.testing.assert_array_equal(
        band.transmits(wavelength=wavelengths), [0, 0, 1, 1, 1, 0]
    )


def _instrument(*, shot_noise, count, lifetime=None):
    """Construct a two-bin dye with one blue and one red emission channel."""
    workflow = facs_canto(
        include_shot_noise=shot_noise,
        include_rin_noise=False,
        background_power=0 * ureg.watt,
    )
    optics = workflow.opto_electronics
    dye = Fluorophore(
        name="test",
        absorption_cross_section=2e-20 * ureg.meter**2,
        quantum_yield=0.75,
        lifetime=lifetime,
        emission_wavelengths=np.array([520, 600]) * ureg.nm,
        photon_weights=(1, 3),
    )
    labels = [Label(fluorophore=dye, molecules_per_particle=count)]
    population = populations.SpherePopulation(
        name="beads",
        concentration=1e9 * ureg.particle / ureg.milliliter,
        diameter=300 * ureg.nm,
        refractive_index=1.5,
        medium_refractive_index=1.33,
        labels=labels,
    )
    workflow.fluidics.scatterer_collection.add_population(population)
    optics.detectors = [
        pmt(
            name=name,
            phi_angle=90 * ureg.degree,
            numerical_aperture=0.8,
            dark_current=0 * ureg.ampere,
            signals=("fluorescence",),
            optical_filter=Bandpass(center=center * ureg.nm, width=10 * ureg.nm),
        )
        for name, center in [("green", 520), ("red", 600), ("dark", 700)]
    ]
    return workflow


@pytest.mark.parametrize("shot_noise", [False, True])
def test_fluorescence_acquisition(*, shot_noise):
    workflow = _instrument(
        shot_noise=shot_noise,
        count=distributions.Uniform(
            lower_bound=5000 * ureg.dimensionless,
            upper_bound=10000 * ureg.dimensionless,
        ),
    )
    record = workflow.acquire(run_time=0.5 * ureg.millisecond, random_state=17)
    block = record.event_collection[0]
    counts = block.get_quantity("Label:test").magnitude
    assert len(counts) > 1 and np.ptp(counts) > 0
    source = workflow.opto_electronics.source
    # Independent Gaussian irradiance and solid-angle reference for NA=0.8 in air.
    irradiance = 2 * source.optical_power / (np.pi * source.waist_y * source.waist_z)
    irradiance = irradiance * np.exp(
        -2 * (block.get_quantity("y") / source.waist_y).to("").magnitude ** 2
    )
    expected = (
        irradiance * (2e-20 * ureg.meter**2) * counts * 0.75 * 0.2 * 0.25 * 488 / 520
    )
    np.testing.assert_allclose(
        block.get_quantity("green").m_as("W"), expected.m_as("W"), atol=0
    )
    np.testing.assert_allclose(
        block.get_quantity("red").m_as("W"), expected.m_as("W") * 3 * 520 / 600, atol=0
    )
    assert np.all(block.get_quantity("dark").magnitude == 0)
    analog = record.signal.analog
    assert np.max(analog["red"].m_as("V")) > 0
    if not shot_noise:
        np.testing.assert_allclose(
            analog["red"].m_as("V"),
            analog["green"].m_as("V") * 3 * 520 / 600,
            atol=1e-18,
        )
    repeat = workflow.acquire(run_time=0.5 * ureg.millisecond, random_state=17)
    np.testing.assert_array_equal(
        analog["red"].m_as("V"), repeat.signal.analog["red"].m_as("V")
    )


def test_mixed_channel_and_scatter_default():
    workflow = _instrument(shot_noise=False, count=10000)
    optics = workflow.opto_electronics
    geometry = {"phi_angle": 90 * ureg.degree, "numerical_aperture": 0.8}
    optics.detectors = [
        pmt(name="scatter", **geometry),
        pmt(name="fluor", signals=("fluorescence",), **geometry),
        pmt(name="mixed", signals=("scatter", "fluorescence"), **geometry),
        pmt(
            name="blocked",
            optical_filter=Bandpass(center=520 * ureg.nm, width=20 * ureg.nm),
            **geometry,
        ),
    ]
    settings = {"run_time": 0.5 * ureg.millisecond, "random_state": 17}
    block = workflow.acquire(**settings).event_collection[0]
    reference = _instrument(shot_noise=False, count=0)
    reference.opto_electronics.detectors = optics.detectors
    blank = reference.acquire(**settings).event_collection[0]
    np.testing.assert_array_equal(
        block.get_quantity("scatter").m_as("W"), blank.get_quantity("scatter").m_as("W")
    )
    np.testing.assert_allclose(
        block.get_quantity("mixed").m_as("W"),
        (block.get_quantity("scatter") + block.get_quantity("fluor")).m_as("W"),
        atol=0,
    )
    assert np.all(block.get_quantity("blocked").magnitude == 0)
    assert np.all(blank.get_quantity("fluor").magnitude == 0)


def test_emission_shot_noise_uses_emitted_photon_energy():
    workflow = _instrument(shot_noise=True, count=10000)
    optics = workflow.opto_electronics
    time = np.arange(12000) * ureg.microsecond
    wavelength = 650 * ureg.nm
    photon_power = (
        optics.source.photon_energy
        * (optics.source.wavelength / wavelength)
        / (time[1] - time[0])
    )
    power = {
        detector.name: np.zeros(time.size) * ureg.watt for detector in optics.detectors
    }
    power["Time"] = time
    # Unit gain and an unrestricted amplifier bandwidth expose single photons in volts.
    optics.amplifier = Amplifier(gain=1 * ureg.volt / ureg.ampere)
    voltages = optics.convert_optical_power_to_voltage(
        power,
        random_generator=np.random.default_rng(31),
        emission={("red", 650): np.full(time.size, 0.5) * photon_power},
    )
    detector = optics.detectors[1]
    counts = (
        voltages["red"] / (photon_power * detector.responsivity * optics.amplifier.gain)
    ).m_as("")
    np.testing.assert_allclose(counts, counts.round(), atol=1e-12)
    assert counts.mean() == pytest.approx(0.5, abs=0.04)


@pytest.mark.parametrize("bins_per_lifetime", [0.25, 1, 8, 64])
def test_bin_integrated_decay(*, bins_per_lifetime):
    """A square excitation for four lifetimes has an analytic rise and tail."""
    duration = 4 * bins_per_lifetime
    edges = np.arange(int(64 * bins_per_lifetime) + 1) / bins_per_lifetime
    excitation = (np.arange(edges.size - 1) < duration) * ureg.nanowatt

    # Integral of the response to a unit step, in units of power times lifetime.
    def step_integral(time):
        elapsed = np.maximum(time, 0)
        return elapsed + np.expm1(-elapsed)

    expected = (
        np.diff(step_integral(edges) - step_integral(edges - 4)) * bins_per_lifetime
    )
    measured = _decay_bin_averages(
        excitation=excitation,
        interval_seconds=4e-9 / bins_per_lifetime,
        lifetime_seconds=4e-9,
    )
    np.testing.assert_allclose(measured.m_as("nW"), expected, atol=1e-12)
    assert measured.sum().m_as("nW") == pytest.approx(duration)


def test_lifetime_wraps_across_acquisition_boundary():
    """A repeatedly illuminated final bin produces a tail in the next period."""
    excitation = np.array([0, 0, 0, 1]) * ureg.watt
    measured = _decay_bin_averages(
        excitation=excitation, interval_seconds=1e-9, lifetime_seconds=4e-9
    )
    expected_initial_state = -np.expm1(-0.25) / -np.expm1(-1)
    expected_first_bin = expected_initial_state * -np.expm1(-0.25) / 0.25
    assert measured[0].m_as("W") == pytest.approx(expected_first_bin)
    assert measured.sum().m_as("W") == pytest.approx(1)
    assert np.all(measured.magnitude >= 0)


def test_fluorophore_lifetime_in_acquisition():
    """Use a resolvable dye lifetime with instantaneous detector electronics."""
    traces = []
    for lifetime in (None, 0 * ureg.ns, 1 * ureg.microsecond):
        workflow = _instrument(shot_noise=False, count=10000, lifetime=lifetime)
        workflow.opto_electronics.amplifier = Amplifier(
            gain=1 * ureg.volt / ureg.ampere
        )
        record = workflow.acquire(run_time=50 * ureg.microsecond, random_state=17)
        traces.append(record.signal.analog["green"].m_as("V"))
    prompt, zero, delayed = traces
    np.testing.assert_array_equal(zero, prompt)
    assert delayed.max() < prompt.max()
    np.testing.assert_allclose(delayed.sum(), prompt.sum(), rtol=1e-12, atol=0)
    # At 10 MHz, integrate the continuous exponential over 100 ns windows.
    expected = _decay_bin_averages(
        excitation=prompt * ureg.watt, interval_seconds=1e-7, lifetime_seconds=1e-6
    )
    np.testing.assert_allclose(delayed, expected.magnitude, rtol=1e-11, atol=1e-27)


@pytest.mark.parametrize(
    "invalid", [-1 * ureg.ns, np.nan * ureg.ns, np.inf * ureg.ns, [1, 2] * ureg.ns, 4.0]
)
def test_invalid_lifetime(invalid):
    with pytest.raises((TypeError, ValueError), match="lifetime"):
        _instrument(shot_noise=False, count=1, lifetime=invalid)


def test_overlapping_spectra_with_different_lifetimes():
    """Two dyes emitting at the same wavelength decay independently before summation."""
    optics = _instrument(shot_noise=False, count=1).opto_electronics
    optics.amplifier = Amplifier(gain=1 * ureg.volt / ureg.ampere)
    time = np.arange(128) * ureg.ns
    pulse = np.zeros(time.size) * ureg.nanowatt
    pulse[0] = 1 * ureg.nanowatt
    power = {detector.name: pulse.copy() for detector in optics.detectors}
    power["Time"] = time
    voltages = optics.convert_optical_power_to_voltage(
        power, emission={("green", 520, 2e-9): pulse, ("green", 520, 4e-9): 2 * pulse}
    )
    conversion = optics.detectors[0].responsivity * optics.amplifier.gain
    expected = pulse.copy()
    for lifetime_ns, amplitude in [(2, 1), (4, 2)]:
        # After a single 1 ns square pulse the remaining light decays exponentially.
        remaining = lifetime_ns * -np.expm1(-1 / lifetime_ns)
        expected[0] += amplitude * (1 - remaining) * ureg.nanowatt
        expected[1:] += (
            amplitude
            * remaining
            * np.exp(-np.arange(127) / lifetime_ns)
            * -np.expm1(-1 / lifetime_ns)
            * ureg.nanowatt
        )
    np.testing.assert_allclose(
        (voltages["green"] / conversion).m_as("nW"), expected.magnitude, atol=1e-13
    )
    np.testing.assert_allclose(
        (voltages["dark"] / conversion).m_as("nW"), pulse.magnitude, atol=1e-13
    )


@pytest.mark.parametrize(
    "preset, lifetime_ns, quantum_yield, emission_nm, peak_area_m2",
    [
        (fitc, 4.1, 0.92, 518, 2.6765e-20),
        (atto_647n, 3.5, 0.65, 664, 5.7353e-20),
        (alexa_fluor_488, 4.1, 0.92, 519, 2.7912e-20),
        (alexa_fluor_594, 3.9, 0.66, 617, 3.5178e-20),
        (alexa_fluor_647, 1.0, 0.33, 668, 1.0324e-19),
    ],
)
def test_dye_preset(preset, lifetime_ns, quantum_yield, emission_nm, peak_area_m2):
    """Check the tabulated properties and Beer–Lambert conversion at half absorption."""
    dye = preset(relative_absorption=0.5)
    assert dye.absorption_cross_section.m_as("m²") == pytest.approx(0.5 * peak_area_m2, rel=1e-4, abs=0)
    assert dye.lifetime.m_as("ns") == lifetime_ns
    assert dye.quantum_yield == quantum_yield
    np.testing.assert_array_equal(dye.emission_wavelengths.m_as("nm"), [emission_nm])
    assert dye.photon_weights == (1.0,)


def test_preset_rejects_absorption_above_peak():
    with pytest.raises(ValueError, match="relative_absorption"):
        alexa_fluor_488(relative_absorption=1.1)
