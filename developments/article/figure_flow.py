from FlowCyPy import units
from FlowCyPy.flow_cell import FlowCell
import matplotlib.pyplot as plt
from MPSPlots.styles import mps


with plt.style.context(mps):
    figure, axes = plt.subplots(1, 3, figsize=(16, 5))

vol_speed =  units.microliter / units.second

sheathes = [0.1 * vol_speed, 0.2 * vol_speed, 0.4 * vol_speed]

for ax, sheath in zip(axes, sheathes):
    sample_volume_flow = 0.05 * units.microliter / units.second
    flow_cell = FlowCell(
        sample_volume_flow=sample_volume_flow,        # Flow speed: 10 microliter per second
        sheath_volume_flow=sheath,        # Flow speed: 10 microliter per second
        width=10 * units.micrometer,        # Flow area: 10 x 10 micrometers
        height=10 * units.micrometer,        # Flow area: 10 x 10 micrometers
    )



    flow_cell.plot(n_samples=300, ax=ax, show=False)

    ratio = (sheath / sample_volume_flow).magnitude

    ax.set_title('$Q_{sheath} \; /  \; Q_{sample}:$ ' + str(ratio))

plt.show()