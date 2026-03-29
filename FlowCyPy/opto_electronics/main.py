from typing import List

from TypedUnit import Time, Power
import numpy as np

from . import source, circuits
from .amplifier import Amplifier
from .coupling_model import ScatteringModel
from .detector import Detector
from .digitizer import Digitizer
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing
from FlowCyPy.fluidics.event_collection import EventCollection


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
    source : source.BaseSource
        The light source instance used in the setup.
    amplifier : Amplifier
        The amplifier instance used to amplify the detected signals.
    digitizer : Digitizer
        The digitizer instance used to convert analog signals to digital form.
    analog_processing : List[circuits.BaseCircuit]
        List of analog processing circuits applied to the signals.
    """

    detectors: List[Detector]
    source: source.BaseSource
    amplifier: Amplifier
    digitizer: Digitizer
    analog_processing: List[circuits.BaseCircuit] = tuple()

    def initialize_optical_signal_dict(
        self, run_time: Time, background_power: Power
    ) -> dict:
        """
        Initialize detector optical power traces.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        background_power : Power
            Constant optical background added to every detector channel.

        Returns
        -------
        dict
            Optical power signal dictionary.
        """
        signal_dict = {}
        signal_dict["Time"] = self.digitizer.get_time_series(run_time=run_time)

        number_of_elements = len(signal_dict["Time"])

        for detector in self.detectors:
            signal_dict[detector.name] = np.ones(number_of_elements) * background_power

        return signal_dict

    def convert_optical_power_to_photocurrent(self, power_signal_dict: dict) -> dict:
        """
        Convert detector optical power traces to photocurrent traces.

        Parameters
        ----------
        power_signal_dict : dict
            Optical power signal dictionary.

        Returns
        -------
        dict
            Photocurrent signal dictionary.
        """
        for detector in self.detectors:
            power_signal_dict[detector.name] *= detector.responsivity.to(
                "ampere / watt"
            )

        return power_signal_dict

    def apply_detector_current_noise(self, photocurrent_dict: dict) -> dict:
        """
        Apply detector current noise to photocurrent traces.

        Parameters
        ----------
        signal_dict : dict
            Photocurrent signal dictionary.

        Returns
        -------
        dict
            Updated photocurrent signal dictionary.
        """
        for detector in self.detectors:
            photocurrent_dict[detector.name] = detector.apply_dark_current_noise(
                signal=photocurrent_dict[detector.name],
                bandwidth=self.digitizer.bandwidth,
            )

        return photocurrent_dict

    def apply_source_noise_to_optical_signals(self, power_signal_dict: dict) -> dict:
        """
        Apply source level optical noise processes.

        Parameters
        ----------
        power_signal_dict : dict
            Optical power signals.

        Returns
        -------
        dict
            Updated optical power signals.
        """
        if self.source.include_rin_noise and self.source.rin is not None:
            power_signal_dict = self.source.add_rin_to_signal_dict(
                signal_dict=power_signal_dict,
            )

        if self.source.include_shot_noise:
            for detector in self.detectors:
                power_signal_dict[detector.name] = self.source.add_shot_noise_to_signal(
                    signal=power_signal_dict[detector.name],
                    time=power_signal_dict["Time"],
                )

        return power_signal_dict

    def add_coupling_to_dataframe(
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
            )

            simulator.run(event_collection, compute_cross_section=compute_cross_section)

    def convert_photocurrent_to_voltage(self, photocurrent_dict: dict) -> dict:
        """
        Convert photocurrent traces to analog voltage traces.

        Parameters
        ----------
        photocurrent_dict : dict
            Photocurrent signal dictionary.

        Returns
        -------
        dict
            Analog voltage signal dictionary.
        """
        for detector in self.detectors:
            photocurrent_dict[detector.name] = self.amplifier.amplify(
                signal=photocurrent_dict[detector.name],
                sampling_rate=self.digitizer.sampling_rate,
            )

        return photocurrent_dict

    def convert_optical_power_to_voltage(self, power_signal_dict: dict) -> dict:
        """
        Convert optical power traces to analog voltage traces by applying the full optoelectronic chain.

        Parameters
        ----------
        power_signal_dict : dict
            Optical power signal dictionary.

        Returns
        -------
        dict
            Analog voltage signal dictionary.
        """
        power_signal_dict = self.apply_source_noise_to_optical_signals(
            power_signal_dict=power_signal_dict,
        )

        photocurrent_dict = self.convert_optical_power_to_photocurrent(
            power_signal_dict=power_signal_dict,
        )

        photocurrent_dict = self.apply_detector_current_noise(
            photocurrent_dict=photocurrent_dict
        )

        voltage_dict = self.convert_photocurrent_to_voltage(
            photocurrent_dict=photocurrent_dict,
        )

        return voltage_dict

    def copy_dict(self, dictionnary: dict) -> dict:
        """
        Create a safe working copy of a signal dictionary.

        Parameters
        ----------
        signal_dict : dict
            Signal dictionary containing arrays or Pint quantities.

        Returns
        -------
        dict
            Copied signal dictionary.
        """
        copied_signal_dict = {}

        for key, value in dictionnary.items():
            if hasattr(value, "copy"):
                copied_signal_dict[key] = value.copy()
            else:
                copied_signal_dict[key] = value

        return copied_signal_dict

    def apply_analog_processing(self, analog_dict: dict) -> dict:
        """
        Apply analog post processing circuits to an analog signal dictionary.

        Parameters
        ----------
        analog_dict : dict
            Analog voltage signals.
        signal_processing : SignalProcessing
            Processing configuration.

        Returns
        -------
        dict
            Processed analog signal dictionary.
        """
        processed_analog_dict = self.copy_dict(analog_dict)

        for detector in self.detectors:
            for circuit in self.analog_processing:
                processed_analog_dict[detector.name] = circuit.process(
                    signal=processed_analog_dict[detector.name],
                    sampling_rate=self.digitizer.sampling_rate,
                )

        return processed_analog_dict
