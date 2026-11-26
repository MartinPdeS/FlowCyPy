"""Instrument factories, organized by manufacturer.

Import a named factory from its manufacturer module and call it to create a
FlowCytometer. Each call constructs an independent sample and acquisition chain.
"""
from ._assembly import ScatterChannel, ScatterSystem

__all__ = ["ScatterChannel", "ScatterSystem"]
