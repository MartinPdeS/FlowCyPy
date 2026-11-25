import numpy as np
import pytest

from FlowCyPy.fluidics import (
    FlowCell,
    Fluidics,
    ScattererCollection,
    distributions,
    populations,
)
from FlowCyPy.units import ureg


def make_fluidics(sampling_method):
    population = populations.SpherePopulation(
        name="population",
        concentration=1e10 * ureg.particle / ureg.milliliter,
        diameter=distributions.Delta(150 * ureg.nanometer),
        refractive_index=distributions.Delta(1.39 * ureg.RIU),
        medium_refractive_index=1.33 * ureg.RIU,
        sampling_method=sampling_method,
    )
    collection = ScattererCollection(populations=[population])
    flow_cell = FlowCell(
        width=10 * ureg.micrometer,
        height=6 * ureg.micrometer,
        sample_volume_flow=1 * ureg.microliter / ureg.second,
        sheath_volume_flow=6 * ureg.microliter / ureg.second,
        event_scheme="uniform-random",
        transverse_sampling_scheme="uniform-random",
    )
    return Fluidics(scatterer_collection=collection, flow_cell=flow_cell)


def event_values(fluidics, random_state):
    collection = fluidics.generate_event_collection(
        run_time=0.2 * ureg.millisecond,
        sampling_rate=5 * ureg.megahertz,
        random_state=random_state,
    )
    events = collection[0]
    return {
        column: events.get_quantity(column).to_base_units().magnitude.copy()
        for column in ("Diameter", "RefractiveIndex", "x", "y", "Velocity", "Time")
    }


@pytest.mark.parametrize("value, error", [(True, TypeError), (0.5, TypeError), (-1, ValueError)])
def test_fluidics_rejects_invalid_seed(value, error):
    """Reject invalid seed values before reseeding either sampler."""
    fluidics = make_fluidics(populations.ExplicitModel())
    with pytest.raises(error, match="non-negative integer"):
        fluidics.seed(value=value)


def test_fluidics_random_state_reproduces_event_collection():
    fluidics = make_fluidics(populations.ExplicitModel())

    first = event_values(fluidics, random_state=1234)
    second = event_values(fluidics, random_state=1234)

    for column in first:
        assert np.array_equal(first[column], second[column]), column


def test_fluidics_random_state_changes_stochastic_events():
    fluidics = make_fluidics(populations.ExplicitModel())

    first = event_values(fluidics, random_state=1234)
    second = event_values(fluidics, random_state=5678)

    assert not np.array_equal(first["x"], second["x"])
    assert not np.array_equal(first["Time"], second["Time"])


@pytest.mark.parametrize(
    "sampling_method",
    [populations.ExplicitModel(), populations.GammaModel(number_of_samples=250)],
)
def test_numpy_generator_replays_and_advances(sampling_method):
    """Independent generators with the same seed replay successive transverse samples."""
    fluidics = make_fluidics(sampling_method)
    generator = np.random.default_rng(1234)
    replay = np.random.default_rng(1234)
    previous_positions = None
    for _ in range(2):
        positions = []
        for stream in (generator, replay):
            collection = fluidics.generate_event_collection(
                run_time=0.2 * ureg.millisecond,
                sampling_rate=5 * ureg.megahertz,
                random_state=stream,
            )
            assert len(collection) == 1
            positions.append(collection[0].get_quantity("x").m_as("meter").copy())

        assert positions[0].size > 0
        np.testing.assert_array_equal(positions[0], positions[1])
        if previous_positions is not None:
            assert not np.array_equal(positions[0], previous_positions)
        previous_positions = positions[0]


def test_empty_explicit_population_keeps_its_event_block():
    """A zero-particle acquisition retains population identity and count metadata."""
    fluidics = make_fluidics(populations.ExplicitModel())
    population = fluidics.scatterer_collection.populations[0]
    population.concentration = 0 * ureg.particle / ureg.liter

    collection = fluidics.generate_event_collection(
        run_time=1 * ureg.millisecond, sampling_rate=1 * ureg.megahertz,
    )

    assert len(collection) == 1
    block = collection[0]
    assert block.population is population
    assert block.empty
    assert block.metadata["NumberOfEvents"] == 0
    assert block.dataframe.scatterer_type == "SpherePopulation"


def test_gamma_count_exceeding_sampler_capacity_is_rejected():
    """Reject counts that would overflow the native sampler before allocating arrays."""
    fluidics = make_fluidics(populations.GammaModel(number_of_samples=2**31))
    with pytest.raises(OverflowError, match="transverse sampler"):
        fluidics.generate_event_collection(
            run_time=1 * ureg.millisecond, sampling_rate=1 * ureg.megahertz,
        )


def test_gamma_and_explicit_models_preserve_particle_statistics():
    explicit = make_fluidics(populations.ExplicitModel())
    gamma = make_fluidics(populations.GammaModel(number_of_samples=250))

    explicit_events = explicit.generate_event_collection(
        run_time=0.2 * ureg.millisecond,
        sampling_rate=5 * ureg.megahertz,
        random_state=42,
    )[0]
    gamma_events = gamma.generate_event_collection(
        run_time=0.2 * ureg.millisecond,
        sampling_rate=5 * ureg.megahertz,
        random_state=42,
    )[0]

    assert len(explicit_events) > 0
    assert len(gamma_events) == 250
    explicit_mean_diameter = (
        explicit_events.get_quantity("Diameter").mean().to("meter").magnitude
    )
    gamma_mean_diameter = (
        gamma_events.get_quantity("Diameter").mean().to("meter").magnitude
    )
    assert explicit_mean_diameter == pytest.approx(gamma_mean_diameter)
    explicit_mean_velocity = (
        explicit_events.get_quantity("Velocity")
        .mean()
        .to("meter / second")
        .magnitude
    )
    gamma_mean_velocity = (
        gamma_events.get_quantity("Velocity")
        .mean()
        .to("meter / second")
        .magnitude
    )
    assert explicit_mean_velocity == pytest.approx(
        gamma_mean_velocity,
        rel=0.05,
    )
    assert gamma_events.metadata["ExpectedNumberOfParticles"] > 0
