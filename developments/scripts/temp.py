import numpy as np
import matplotlib.pyplot as plt

from FlowCyPy import units
from FlowCyPy.flow_cell import CircularFlowCell, RectangularFlowCell, SquareFlowCell
from FlowCyPy.population import BasePopulation

# Create example FlowCell instances
volume_flow = 0.3 * units.microliter / units.second

# CircularFlowCell instance
circular_cell = CircularFlowCell(
    volume_flow=volume_flow,
    radius=10 * units.micrometer
)

# RectangularFlowCell instance with width 20 μm and height 10 μm.
rectangular_cell = RectangularFlowCell(
    volume_flow=volume_flow,
    width=20 * units.micrometer,
    height=10 * units.micrometer
)

# SquareFlowCell instance
square_cell = SquareFlowCell(
    volume_flow=volume_flow,
    side=3 * units.micrometer
)

# Create a figure with subplots for velocity profiles
fig, axs = plt.subplots(1, 3, figsize=(18, 5))

# Plot velocity profile for CircularFlowCell
r, velocities_circ = circular_cell.get_velocity_profile(num_points=100)
axs[0].plot(r, velocities_circ, color='blue')
axs[0].set_title('Circular Flow Cell Velocity Profile')
axs[0].set_xlabel(f'Radial Position [{r.units}]')
axs[0].set_ylabel(f'Velocity [{velocities_circ.units}]')
axs[0].grid(True)

# Plot velocity profile for RectangularFlowCell
X_rect, Y_rect, velocities_rect = rectangular_cell.get_velocity_profile(num_points=50)
c1 = axs[1].contourf(X_rect, Y_rect, velocities_rect, cmap='viridis')
axs[1].set_title('Rectangular Flow Cell Velocity Profile')
axs[1].set_xlabel('x (m)')
axs[1].set_ylabel('y (m)')
fig.colorbar(c1, ax=axs[1])

# Plot velocity profile for SquareFlowCell
X_sq, Y_sq, velocities_sq = square_cell.get_velocity_profile(num_points=50)
c2 = axs[2].contourf(X_sq, Y_sq, velocities_sq, cmap='plasma')
axs[2].set_title('Square Flow Cell Velocity Profile')
axs[2].set_xlabel('x (m)')
axs[2].set_ylabel('y (m)')
fig.colorbar(c2, ax=axs[2])

plt.tight_layout()
plt.show()


# Generate events for the CircularFlowCell, which includes sampling velocity.
velocities_sampled_circ = circular_cell.sample_velocity(500)

# Generate events for the RectangularFlowCell.
velocities_sampled_rect = rectangular_cell.sample_velocity(500)

# Generate events for the SquareFlowCell.
velocities_sampled_sq = square_cell.sample_velocity(500)

# Create a figure with subplots for histograms of sampled velocities.
fig2, axs2 = plt.subplots(1, 3, figsize=(18, 5))

axs2[0].hist(velocities_sampled_circ, edgecolor='black', color='skyblue')
axs2[0].set_title('Sampled Velocities (Circular)')
axs2[0].set_xlabel('Velocity (m/s)')
axs2[0].set_ylabel('Frequency')
axs2[0].grid(True)

axs2[1].hist(velocities_sampled_rect, edgecolor='black', color='lightgreen')
axs2[1].set_title('Sampled Velocities (Rectangular)')
axs2[1].set_xlabel('Velocity (m/s)')
axs2[1].set_ylabel('Frequency')
axs2[1].grid(True)

axs2[2].hist(velocities_sampled_sq, edgecolor='black', color='salmon')
axs2[2].set_title('Sampled Velocities (Square)')
axs2[2].set_xlabel('Velocity (m/s)')
axs2[2].set_ylabel('Frequency')
axs2[2].grid(True)

plt.tight_layout()
plt.show()
