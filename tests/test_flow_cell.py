import pytest
import numpy as np
from unittest.mock import patch

# Import necessary components from FlowCyPy.
from FlowCyPy import units
from FlowCyPy.fluidics import Fluidics, FlowCell, ScattererCollection, population, distribution
import FlowCyPy
FlowCyPy.debug_mode = True  # Enable debug mode for detailed logging


# ----------------- FIXTURES -----------------

@pytest.fixture
def valid_flowcell():
    """
    Create a valid FlowCell instance using typical microfluidic and flow cytometry parameters.
    """
    return FlowCell(
        width=10 * units.micrometer,
        height=10 * units.micrometer,
        sample_volume_flow=0.3 * units.microliter / units.second,
        sheath_volume_flow=3 * units.microliter / units.second,
        mu=1e-3 * units.pascal * units.second,
        N_terms=25,
        n_int=200,
    )

@pytest.fixture
def real_population():
    """
    Create a real Population instance using FlowCyPy's Sphere population with delta distributions.
    """
    return population.Sphere(
        name='Population',
        particle_count=10 * units.particle,
        diameter=distribution.Delta(position=150 * units.nanometer),
        refractive_index=distribution.Delta(position=1.39 * units.RIU)
    )

@pytest.fixture
def real_scatterer_collection(real_population):
    """
    Create a real ScattererCollection containing the real Population instance.
    """
    return ScattererCollection(
        medium_refractive_index=1.33 * units.RIU,
        populations=[real_population]
    )

# --- Test Cases ---

def test_flowcell_creation(valid_flowcell):
    assert valid_flowcell._cpp_dpdx_ref != 0
    assert valid_flowcell._cpp_u_center > 0
    assert valid_flowcell.sample.width > 0
    assert valid_flowcell.sample.height > 0
    assert valid_flowcell.sample.area > 0
    assert valid_flowcell.sample.average_flow_speed > 0

def test_invalid_width_type():
    with pytest.raises(ValueError):
        FlowCell(
            width=10e-6,  # Not a Quantity
            height=10e-6 * units.meter,
            sample_volume_flow=0.3 * units.microliter / units.second,
            sheath_volume_flow=3 * units.microliter / units.second,
            mu=1e-3 * units.pascal * units.second,
        )

def test_invalid_flow_units():
    with pytest.raises(ValueError):
        FlowCell(
            width=10 * units.micrometer,
            height=10 * units.micrometer,
            sample_volume_flow=0.3 * units.meter,  # Wrong unit
            sheath_volume_flow=3 * units.microliter / units.second,
            mu=1e-3 * units.pascal * units.second,
        )

def test_velocity_output(valid_flowcell):
    velocity = valid_flowcell._cpp_get_velocity(y=0.0, z=0.0, dpdx_local=1e-3)

    assert velocity != 0

    assert np.all(np.isfinite(velocity))

def test_compute_channel_flow(valid_flowcell):
    Q = valid_flowcell._cpp_compute_channel_flow(valid_flowcell._cpp_dpdx_ref)
    assert Q > 0

def test_sample_particles(valid_flowcell):
    n_samples = 1000
    x, y, velocity = valid_flowcell.sample_transverse_profile(n_samples)

    assert len(y) == n_samples
    assert len(x) == n_samples
    assert len(velocity) == n_samples
    # Check that velocities are finite.

    assert np.all(np.isfinite(velocity.magnitude))

@patch('matplotlib.pyplot.show')
def test_plot_method(mock_show, valid_flowcell, real_scatterer_collection):
    fluidics = Fluidics(
        scatterer_collection=real_scatterer_collection,
        flow_cell=valid_flowcell
    )

    fluidics.plot(run_time=1 * units.millisecond)


def test_get_sample_volume(valid_flowcell):
    run_time = 10 * units.second
    volume = valid_flowcell.get_sample_volume(run_time)
    volume_microliters = volume.to("microliter")
    assert volume_microliters.magnitude > 0

def test_generate_poisson_events(valid_flowcell, real_population):
    run_time = 10 * units.second
    df = valid_flowcell._generate_event_dataframe(run_time=run_time, populations=[real_population])
    expected_columns = {"Time", "Velocity", "x", "y"}
    assert expected_columns.issubset(set(df.columns))
    if not df.empty:
        assert len(df) > 0

def test_generate_event_dataframe(valid_flowcell, real_population):
    run_time = 10 * units.second
    df_event = valid_flowcell._generate_event_dataframe(populations=[real_population], run_time=run_time)
    # Check that the DataFrame has a MultiIndex with "Population" and "Index"
    assert "Population" in df_event.index.names
    assert "ScattererID" in df_event.index.names
    assert len(df_event) > 0

def test_event_dataframe_units(valid_flowcell, real_scatterer_collection):
    run_time = 10 * units.second
    df_event = valid_flowcell._generate_event_dataframe(populations=real_scatterer_collection.populations, run_time=run_time)
    # Check that each column has pint arrays with units (assume the column has .pint attribute)
    for col in df_event.columns:
        assert hasattr(df_event[col], "pint")


# ------------------ RUN TESTS ------------------

if __name__ == "__main__":
    pytest.main(["-W", "error", "-s", __file__])
