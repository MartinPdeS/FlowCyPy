import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from MPSPlots.styles import mps

from FlowCyPy import units
from FlowCyPy.flow_cell import CircularFlowCell

# Define parameters for the CircularFlowCell
volume_flow = 0.3 * units.microliter / units.second
radius = 10 * units.micrometer

# Define different hydrodynamic focusing factors to study
focusing_factors = [0.3, 0.5, 0.7]

# Dictionaries to store velocity profiles and sampled velocities
profile_data = {}
sampled_data = {}

n_profile_points = 100
n_samples = 1500

# Loop over focusing factors to generate data
for f in focusing_factors:
    cell = CircularFlowCell(volume_flow=volume_flow, radius=radius, focusing_factor=f)
    r, vel = cell.get_velocity_profile(num_points=n_profile_points)
    # Convert velocity to m/s for plotting
    profile_data[f] = (r, vel.to('meter/second').magnitude)
    sampled = cell.sample_velocity(n_samples=n_samples)
    sampled_data[f] = sampled.to('meter/second').magnitude


with plt.style.context(mps):
    fig = plt.figure(figsize=(14, 5))

    grid = GridSpec(1, 4, width_ratios=[2, 1, 1, 1], height_ratios=[1])

    ax1 = fig.add_subplot(grid[0])
    ax2 = fig.add_subplot(grid[1])
    ax3 = fig.add_subplot(grid[2], sharey=ax2, sharex=ax2)
    ax4 = fig.add_subplot(grid[3], sharey=ax2, sharex=ax2)

    axes = [ax1, ax2, ax3, ax4]

    # Plot overlaid velocity profiles on the first subplot
    axes[0].plot(r, vel, lw=2, label=f'Focusing Factor = {f}')

    axes[0].set_xlabel('Radial Position (m)')
    axes[0].set_ylabel('Velocity (m/s)')
    axes[0].set_title('Velocity Profiles')
    axes[0].legend()
    axes[0].grid(True)

    # Plot overlaid histograms using Seaborn on the second subplot
    colors = sns.color_palette("husl", len(focusing_factors))
    for ax, (i, f) in zip(axes[1:], enumerate(focusing_factors)):
        sns.histplot(sampled_data[f], fill=True, multiple="stack", kde=False, color=colors[i], ax=ax, alpha=0.3)

        ax.set_xlim([0.6, None])
        ax.set_ylabel('')
        ax.set_xlabel('Sampled Velocity (m/s)')
        ax.set_title(f'Focusing Factor = {f}')
        # ax.legend()

    axes[1].set_ylabel('Count')
    plt.tight_layout()
    plt.savefig("velocity_profiles_and_histograms.png", dpi=300)
    plt.show()
