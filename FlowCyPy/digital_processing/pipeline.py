#!/usr/bin/env python
# -*- coding: utf-8 -*-
import FlowCyPy.units as _
from . import discriminator
from . import peak_locator


class DigitalProcessing:
    """
    Container for analog and digital signal processing stages in a simulated flow cytometry pipeline.

    This class orchestrates the application of analog electronic filtering, digitization, triggering,
    and peak detection algorithms. It integrates key building blocks of the signal acquisition chain
    in a modular and extensible way.

    Parameters
    ----------
    discriminator : discriminator.BaseDiscriminator
        Component responsible for extracting signal segments based on threshold-crossing
        or window-based logic applied to the analog signal.
    peak_algorithm : peak_locator.BasePeakLocator
        Peak detection algorithm that locates and characterizes peaks in the digitized signal
        (e.g., based on amplitude, area, or width).
    """

    def __init__(
        self,
        discriminator: discriminator.BaseDiscriminator = None,
        peak_algorithm: peak_locator.BasePeakLocator = None,
    ):
        self.discriminator = discriminator
        self.peak_algorithm = peak_algorithm
