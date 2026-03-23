#!/usr/bin/env python
# -*- coding: utf-8 -*-
import FlowCyPy.units as _
from . import circuits
from . import discriminator
from . import peak_locator
from .digitizer import Digitizer
from FlowCyPy.signal_generator import SignalGenerator


class SignalProcessing:
    """
    Container for analog and digital signal processing stages in a simulated flow cytometry pipeline.

    This class orchestrates the application of analog electronic filtering, digitization, triggering,
    and peak detection algorithms. It integrates key building blocks of the signal acquisition chain
    in a modular and extensible way.

    Parameters
    ----------
    analog_processing : list of circuits.SignalProcessor
        List of analog signal processing components (e.g., amplifiers, filters) applied to
        simulated voltage traces before digitization.
    digitizer : Digitizer
        Digitization module that converts analog voltage signals to digital values using
        specified bit depth, voltage range, and sampling parameters.
    discriminator : discriminator.BaseDiscriminator
        Component responsible for extracting signal segments based on threshold-crossing
        or window-based logic applied to the analog signal.
    peak_algorithm : peak_locator.BasePeakLocator
        Peak detection algorithm that locates and characterizes peaks in the digitized signal
        (e.g., based on amplitude, area, or width).
    """

    def __init__(
        self,
        digitizer: Digitizer,
        analog_processing: list[circuits.BaseCircuit] = (),
        discriminator: discriminator.BaseDiscriminator = None,
        peak_algorithm: peak_locator.BasePeakLocator = None,
    ):
        self.analog_processing = analog_processing
        self.digitizer = digitizer
        self.discriminator = discriminator
        self.peak_algorithm = peak_algorithm
