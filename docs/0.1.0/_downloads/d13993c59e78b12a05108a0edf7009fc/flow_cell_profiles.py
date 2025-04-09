"""
Flow Cell geometries
====================

"""
from FlowCyPy import units
from FlowCyPy.flow_cell import FlowCell

# Create example FlowCell instances
volume_flow = 0.3 * units.microliter / units.second
focusing_factor = 0.5

flow_cell = FlowCell(
    sample_volume_flow=0.02 * units.microliter / units.second,        # Flow speed: 10 microliter per second
    sheath_volume_flow=0.1 * units.microliter / units.second,        # Flow speed: 10 microliter per second
    width=20 * units.micrometer,        # Flow area: 10 x 10 micrometers
    height=10 * units.micrometer,        # Flow area: 10 x 10 micrometers
)

# %%
# Plot velocity profile for SquareFlowCell
flow_cell.plot(n_samples=300)

