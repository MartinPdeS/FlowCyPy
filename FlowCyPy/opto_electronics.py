from typing import List

import pandas as pd

from FlowCyPy import source
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.coupling import ScatteringSimulator
from FlowCyPy.detector import Detector
from FlowCyPy.source import GaussianBeam  # noqa: F401
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing


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

    def model_event(
        self, event_dataframe: pd.DataFrame, compute_cross_section: bool = False
    ):
        """
        Adds optoelectronic parameters to the provided DataFrame.

        This method updates the DataFrame in place by adding columns for the detector names and their
        corresponding responsivities. It also adds the amplifier gain and bandwidth.

        Parameters
        ----------
        event_dataframe : pd.DataFrame
            DataFrame to which the optoelectronic parameters will be added.
        """
        self._add_coupling_to_dataframe(
            event_dataframe=event_dataframe, compute_cross_section=compute_cross_section
        )

        self._add_pulse_width_to_dataframe(event_dataframe=event_dataframe)

        return event_dataframe

    def _add_coupling_to_dataframe(
        self, event_dataframe: pd.DataFrame, compute_cross_section: bool = False
    ):
        """
        Computes the detected signal for each scatterer in the provided DataFrame and updates it in place.
        This method iterates over the list of detectors and computes the detected signal for each scatterer
        using the `compute_detected_signal` function.

        Parameters
        ----------
        event_dataframe : pd.DataFrame
            DataFrame containing scatterer properties. It must include a column named 'type' with values
            'Sphere' or 'CoreShell', and additional columns required for each scatterer type.
        compute_cross_section : bool, optional
            If True, the scattering cross section (Csca) is computed and added to the DataFrame under the
            column 'Csca'. Default is False.
        """
        if event_dataframe.empty:
            return

        for detector in self.detectors:
            simulator = ScatteringSimulator(
                source=self.source,
                detector=detector,
                bandwidth=self.amplifier.bandwidth,
                medium_refractive_index=event_dataframe.medium_refractive_index,
            )

            simulator.run(
                event_df=event_dataframe, compute_cross_section=compute_cross_section
            )

    def _add_pulse_width_to_dataframe(self, event_dataframe: pd.DataFrame):
        r"""
        Generates and assigns random Gaussian pulse parameters for each particle event.

        The pulse shape follows the Gaussian beam"s spatial intensity profile:

        .. math::

            I(r) = I_0 \exp\left(-\frac{2r^2}{w_0^2}\right),

        where :math:`w_0` is the beam waist (the :math:`1/e^2` radius of the intensity distribution).
        This profile can be rewritten in standard Gaussian form:

        .. math::

            I(r) = I_0 \exp\left(-\frac{r^2}{2\sigma_x^2}\right),

        which implies the spatial standard deviation:

        .. math::

            \sigma_x = \frac{w_0}{2}.

        When a particle moves at a constant flow speed :math:`v`, the spatial coordinate :math:`r`
        is related to time :math:`t` via :math:`r = v t`. Substituting this into the intensity profile
        gives a temporal Gaussian:

        .. math::

            I(t) = I_0 \exp\left(-\frac{2 (v t)^2}{w_0^2}\right).

        This is equivalent to a Gaussian in time:

        .. math::

            I(t) = I_0 \exp\left(-\frac{t^2}{2\sigma_t^2}\right),

        so that the temporal standard deviation is:

        .. math::

            \sigma_t = \frac{\sigma_x}{v} = \frac{w_0}{2v}.

        The full width at half maximum (FWHM) in time is then:

        .. math::

            \text{FWHM} = 2\sqrt{2 \ln2} \, \sigma_t = \frac{w_0}{v} \sqrt{2 \ln2}.

        **Generated Parameters:**
        - **Centers:** The time at which each pulse occurs (randomly determined).
        - **Widths:** The pulse width (:math:`\sigma_t`) in seconds, computed as :math:`w_0 / (2 v)`.

        **Effects**
        -----------
        Modifies `event_dataframe` in place by adding:
        - A `'Centers'` column with the pulse center times.
        - A `'Widths'` column with the computed pulse widths.
        """
        if event_dataframe.empty:
            return

        assert (
            "Velocity" in event_dataframe.columns
        ), "Event DataFrame must contain 'Velocity' column to compute the pulses width."
        # Calculate the pulse width (standard deviation in time, σₜ) based on the beam waist and flow speed.
        if event_dataframe.empty:
            return

        widths = self.source.get_particle_width(velocity=event_dataframe["Velocity"])

        event_dataframe["Widths"] = widths
