from typing import List
import pandas as pd

from FlowCyPy import source
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.coupling_model import ScatteringModel, FluorescenceModel
from FlowCyPy.detector import Detector
from FlowCyPy.source import GaussianBeam  # noqa: F401
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing
from FlowCyPy.event_collection import EventCollection


@dataclass(config=config_dict)
class OptoElectronics(StrictDataclassMixing):
    """
    Base class for optoelectronic components in flow cytometry simulations.

    This class serves as a base for various optoelectronic components, such as detectors and
    signal generators, providing common functionality and attributes.

    Parameters
    ----------
    detectors : List[Detector], optional
        A list of Detector instances to be included in the optoelectronics setup.
    source : source.BaseBeam
        The light source instance used in the setup.
    amplifier : TransimpedanceAmplifier
        The amplifier instance used to amplify the detected signals.
    """

    detectors: List[Detector]
    source: source.BaseBeam
    amplifier: TransimpedanceAmplifier

    def _add_coupling_to_dataframe(
        self, event_collection: EventCollection, compute_cross_section: bool = False
    ):
        """
        Computes the detected signal for each scatterer in the provided DataFrame and updates it in place.
        This method iterates over the list of detectors and computes the detected signal for each scatterer
        using the `compute_detected_signal` function.

        Parameters
        ----------
        event_collection : EventCollection
            Collection of dataframe containing scatterer properties. It must include a column named 'type' with values
            'Sphere' or 'CoreShell', and additional columns required for each scatterer type.
        compute_cross_section : bool, optional
            If True, the scattering cross section (Csca) is computed and added to the DataFrame under the
            column 'Csca'. Default is False.
        """
        if len(event_collection) == 0:
            return

        for detector in self.detectors:

            simulator = ScatteringModel(
                source=self.source,
                detector=detector,
                bandwidth=self.amplifier.bandwidth,
            )

            simulator.run(event_collection, compute_cross_section=compute_cross_section)
