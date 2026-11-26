"""Reference photomultiplier tube channels."""

from FlowCyPy.detectors._preset import DetectorPreset
from FlowCyPy.units import ureg

pmt = DetectorPreset(
    responsivity=0.2 * ureg.ampere / ureg.watt,
    dark_current=1 * ureg.nanoampere,
)
