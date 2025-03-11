"""
Flow Cell geometries
====================

"""
from FlowCyPy import units
from FlowCyPy.flow_cell import CircularFlowCell, RectangularFlowCell, SquareFlowCell

# Create example FlowCell instances
volume_flow = 0.3 * units.microliter / units.second
focusing_factor = 0.5

# CircularFlowCell instance
circular_cell = CircularFlowCell(
    volume_flow=volume_flow,
    radius=10 * units.micrometer,
    focusing_factor=focusing_factor
)

# RectangularFlowCell instance with width 20 μm and height 10 μm.
rectangular_cell = RectangularFlowCell(
    volume_flow=volume_flow,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
    focusing_factor=focusing_factor
)

# SquareFlowCell instance
square_cell = SquareFlowCell(
    volume_flow=volume_flow,
    side=3 * units.micrometer,
    focusing_factor=focusing_factor
)

# %%
# Plot velocity profile for CircularFlowCell
circular_cell.plot_3d(n_samples=300)

# %%
# Plot velocity profile for RectangularFlowCell
rectangular_cell.plot_3d(n_samples=300)

# %%
# Plot velocity profile for SquareFlowCell
square_cell.plot_3d(n_samples=300)

