import pytest
import numpy as np
from FlowCyPy import units
from FlowCyPy.flow_cell import CircularFlowCell, RectangularFlowCell, SquareFlowCell, IdealFlowCell


@pytest.fixture
def circular_cell():
    """Fixture to create a CircularFlowCell instance."""
    return CircularFlowCell(
        volume_flow=0.3 * units.microliter / units.second,
        radius=10 * units.micrometer
    )


@pytest.fixture
def rectangular_cell():
    """Fixture to create a RectangularFlowCell instance."""
    return RectangularFlowCell(
        volume_flow=0.3 * units.microliter / units.second,
        width=20 * units.micrometer,
        height=10 * units.micrometer
    )


@pytest.fixture
def square_cell():
    """Fixture to create a SquareFlowCell instance."""
    return SquareFlowCell(
        volume_flow=0.3 * units.microliter / units.second,
        side=15 * units.micrometer
    )


@pytest.fixture
def ideal_cell():
    """Fixture to create an IdealFlowCell instance."""
    return IdealFlowCell(
        flow_speed=0.5 * units.meter / units.second,
        flow_area=100 * units.micrometer**2
    )


# ------------------ TESTING CIRCULAR FLOW CELL ------------------

def test_circular_flowcell_velocity_profile(circular_cell):
    """Test the velocity profile calculation in a circular flow cell."""
    r, velocities = circular_cell.get_velocity_profile(num_points=100)

    assert len(r) == 100
    assert len(velocities) == 100
    assert np.all(velocities <= 2 * circular_cell.flow_speed)
    assert velocities[0].to('metre/second').magnitude == pytest.approx(2 * circular_cell.flow_speed.to('metre/second').magnitude, rel=1e-3)  # Center velocity max
    assert velocities[-1] == pytest.approx(0.0, rel=1e-3)  # Edge velocity 0


def test_circular_flowcell_sampling(circular_cell):
    """Test velocity sampling in a circular flow cell."""
    sampled_velocities = circular_cell.sample_velocity(n_samples=100)

    assert len(sampled_velocities) == 100
    assert np.all(sampled_velocities <= 2 * circular_cell.flow_speed)
    assert np.all(sampled_velocities >= 0)


# ------------------ TESTING RECTANGULAR FLOW CELL ------------------

def test_rectangular_flowcell_velocity_profile(rectangular_cell):
    """Test the velocity profile calculation in a rectangular flow cell."""
    X, Y, velocities = rectangular_cell.get_velocity_profile(num_points=50)

    assert X.shape == velocities.shape
    assert Y.shape == velocities.shape
    assert np.all(velocities <= 1.5 * rectangular_cell.flow_speed)
    assert np.all(velocities >= 0)


def test_rectangular_flowcell_sampling(rectangular_cell):
    """Test velocity sampling in a rectangular flow cell."""
    sampled_velocities = rectangular_cell.sample_velocity(n_samples=100)

    assert len(sampled_velocities) == 100
    assert np.all(sampled_velocities <= 1.5 * rectangular_cell.flow_speed)
    assert np.all(sampled_velocities >= 0)


# ------------------ TESTING SQUARE FLOW CELL ------------------

def test_square_flowcell_velocity_profile(square_cell):
    """Test the velocity profile calculation in a square flow cell."""
    X, Y, velocities = square_cell.get_velocity_profile(num_points=50)

    assert X.shape == velocities.shape
    assert Y.shape == velocities.shape
    assert np.all(velocities <= 1.5 * square_cell.flow_speed)
    assert np.all(velocities >= 0)


def test_square_flowcell_sampling(square_cell):
    """Test velocity sampling in a square flow cell."""
    sampled_velocities = square_cell.sample_velocity(n_samples=100)

    assert len(sampled_velocities) == 100
    assert np.all(sampled_velocities <= 1.5 * square_cell.flow_speed)
    assert np.all(sampled_velocities >= 0)


# ------------------ TESTING IDEAL FLOW CELL ------------------

def test_ideal_flowcell_velocity_profile(ideal_cell):
    """Test the velocity profile of an ideal flow cell."""
    velocities = ideal_cell.get_velocity_profile(num_points=100)

    assert len(velocities) == 100
    assert np.all(velocities == ideal_cell.flow_speed.magnitude)


def test_ideal_flowcell_sampling(ideal_cell):
    """Test velocity sampling in an ideal flow cell."""
    sampled_velocities = ideal_cell.sample_velocity(n_samples=100)

    assert len(sampled_velocities) == 100
    assert np.all(sampled_velocities.to('meter/second').magnitude == ideal_cell.flow_speed.to('meter/second').magnitude)


# ------------------ RUN TESTS ------------------

if __name__ == "__main__":
    pytest.main(["-W error", __file__])

