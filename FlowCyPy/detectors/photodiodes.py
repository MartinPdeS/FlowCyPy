"""Reference PIN and avalanche photodiode channels."""

from FlowCyPy.detectors._preset import DetectorPreset
from FlowCyPy.units import ureg

pin = DetectorPreset(
    responsivity=0.5 * ureg.ampere / ureg.watt,
    dark_current=10 * ureg.nanoampere,
)

apd = DetectorPreset(
    responsivity=0.7 * ureg.ampere / ureg.watt,
    dark_current=5 * ureg.nanoampere,
)
