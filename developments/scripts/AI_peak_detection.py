import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from MPSPlots.styles import mps

from FlowCyPy import units
from FlowCyPy.flow_cell import CircularFlowCell


cell = CircularFlowCell(
    volume_flow= 0.3 * units.microliter / units.second,
    radius=10 * units.micrometer,
    focusing_factor=0.4
)

cell.plot_3d(500)


from FlowCyPy import units
from FlowCyPy.flow_cell import RectangularFlowCell


cell = RectangularFlowCell(
    volume_flow= 0.3 * units.microliter / units.second,
    width=20 * units.micrometer,
    height=10 * units.micrometer,
    focusing_factor=0.7
)

cell.plot_3d(500)