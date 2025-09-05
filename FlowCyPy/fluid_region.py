from matplotlib.patches import Rectangle
from TypedUnit import Area, FlowRate, Length, ureg

from FlowCyPy.binary.interface_flow_cell import FLUIDREGION


class FluidRegion:
    def __init__(self, instance: FLUIDREGION):
        self.instance = instance

    @property
    def width(self) -> Length:
        return self.instance._cpp_width * ureg.meter

    @property
    def height(self) -> Length:
        return self.instance._cpp_height * ureg.meter

    @property
    def area(self) -> Area:
        return self.width * self.height

    @property
    def volume_flow(self) -> FlowRate:
        return self.instance._cpp_volume_flow * (ureg.meter**3 / ureg.second)

    @property
    def average_flow_speed(self) -> FlowRate:
        return self.instance._cpp_average_flow_speed * (ureg.meter / ureg.second)

    @property
    def max_flow_speed(self) -> FlowRate:
        return self.instance._cpp_max_flow_speed * (ureg.meter / ureg.second)

    def _add_to_plot(self, ax, length_units, color, label=None):
        rect = Rectangle(
            (
                -self.width.to(length_units).magnitude / 2,
                -self.height.to(length_units).magnitude / 2,
            ),
            self.width.to(length_units).magnitude,
            self.height.to(length_units).magnitude,
            fill=True,
            edgecolor="black",
            facecolor=color,
            alpha=0.8,
            linewidth=1,
            zorder=-1,
            label=label,
        )
        ax.add_patch(rect)
