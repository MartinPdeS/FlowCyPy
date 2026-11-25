# Initialize the shared unit registry before loading native processing modules.
import FlowCyPy.units as _  # noqa: F401
from . import discriminator, peak_locator
from .peak_locator import BasePeakLocator

__all__ = ["DigitalProcessing", "discriminator", "peak_locator"]


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
    peak_locator : BasePeakLocator, optional
        Peak detection algorithm that locates and characterizes peaks in the digitized signal
        (e.g., based on amplitude, area, or width).
    peak_algorithm : BasePeakLocator, optional
        Compatibility alias for peak_locator.
    """

    def __init__(
        self,
        discriminator: discriminator.BaseDiscriminator = None,
        peak_algorithm: BasePeakLocator | None = None,
        *,
        peak_locator: BasePeakLocator | None = None,
    ):
        self.discriminator = discriminator
        if peak_algorithm is not None and peak_locator is not None:
            raise TypeError("Specify only one of peak_locator and peak_algorithm.")
        self.peak_locator = peak_locator if peak_locator is not None else peak_algorithm

    @property
    def peak_algorithm(self) -> BasePeakLocator | None:
        """Return the configured peak locator under its original name."""
        return self.peak_locator

    @peak_algorithm.setter
    def peak_algorithm(self, value: BasePeakLocator | None) -> None:
        self.peak_locator = value
