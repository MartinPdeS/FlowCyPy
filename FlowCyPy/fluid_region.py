from FlowCyPy.units import Quantity
from FlowCyPy import units

from matplotlib.patches import Rectangle
from FlowCyPy.binary.interface_flow_cell import FLUIDREGION

class FluidRegion():
    def __init__(self, instance: FLUIDREGION):
        self.instance = instance

    @property
    def width(self) -> Quantity:
        return self.instance._cpp_width * units.meter

    @property
    def height(self) -> Quantity:
        return self.instance._cpp_height * units.meter

    @property
    def area(self) -> Quantity:
        return self.width * self.height

    @property
    def volume_flow(self) -> Quantity:
        return self.instance._cpp_volume_flow * (units.meter**3 / units.second)

    @property
    def average_flow_speed(self) -> Quantity:
        return self.instance._cpp_average_flow_speed * (units.meter / units.second)

    @property
    def max_flow_speed(self) -> Quantity:
        return self.instance._cpp_max_flow_speed * (units.meter / units.second)

    def _add_to_plot(self, ax, length_units, color, label=None):
        rect = Rectangle(
            (-self.width.to(length_units).magnitude / 2, -self.height.to(length_units).magnitude / 2),
            self.width.to(length_units).magnitude,
            self.height.to(length_units).magnitude,
            fill=True,
            edgecolor='black',
            facecolor=color,
            alpha=0.8,
            linewidth=1,
            zorder=-1,
            label=label
        )
        ax.add_patch(rect)
