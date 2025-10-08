from TypedUnit import FlowRate, Power, ureg

from FlowCyPy.instances.detector import PMT
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy import fluidics, triggering_system, triggering_system
from FlowCyPy import opto_electronics
from FlowCyPy import signal_processing
from FlowCyPy.run_record import RunRecord

from enum import Enum


class SheathFlowRate(Enum):
    DEFAULT = 18 * ureg.milliliter / ureg.minute
    LOW = 20 * ureg.milliliter / ureg.minute
    MEDIUM = 30 * ureg.milliliter / ureg.minute
    HIGH = 40 * ureg.milliliter / ureg.minute


class SampleFlowRate(Enum):
    LOW = 10 * ureg.microliter / ureg.minute
    MEDIUM = 60 * ureg.microliter / ureg.minute
    HIGH = 120 * ureg.microliter / ureg.minute


class FacsCanto:
    """
    Defines the FacsCanto flowcytometer with estimated parameters.

    Parameters
    ----------
    sample_volume_flow : SampleFlowRate | FlowRate
        Sample flow rate setting
    sheath_volume_flow : SheathFlowRate | FlowRate
        Sheath flow rate setting
    optical_power : Power
        Laser optical power
    background_power : Power
        Background optical power
    """

    def __init__(
        self,
        sample_volume_flow: SampleFlowRate | FlowRate,
        sheath_volume_flow: SheathFlowRate | FlowRate,
        optical_power: Power,
        background_power: Power,
    ):
        self.sample_volume_flow = sample_volume_flow
        self.sheath_volume_flow = sheath_volume_flow
        self.optical_power = optical_power

        self.instance = FlowCytometer(
            opto_electronics=self.get_optoelectronics(),
            fluidics=self.get_fluidics(),
            signal_processing=self.get_signal_processing(),
            background_power=background_power,
        )

    def add_population(self, *populations) -> None:
        """
        Adds particle populations to the fluidics system.

        Parameters
        ----------
        *populations : population.ParticlePopulation
            One or more particle populations to add
        """
        self.instance.fluidics.scatterer_collection.add_population(*populations)

    def dilute_sample(self, factor: float) -> None:
        """
        Dilutes the sample by a specified factor.

        Parameters
        ----------
        factor : float
            Dilution factor
        """
        self.instance.fluidics.scatterer_collection.dilute(factor)

    def run(self, run_time: ureg.Quantity) -> RunRecord:
        """
        Runs the flow cytometer simulation for a specified duration.

        Parameters
        ----------
        run_time : ureg.Quantity
            Duration of the simulation run

        Returns
        -------
        RunRecord
            Results of the simulation run
        """
        return self.instance.run(run_time=run_time)

    def get_fluidics(self) -> fluidics.Fluidics:
        """
        Creates the fluidics system for the FacsCanto.

        Returns
        -------
        fluidics.Fluidics
            Configured fluidics system
        """
        sample_volume_flow = (
            self.sample_volume_flow.value
            if isinstance(self.sample_volume_flow, Enum)
            else self.sample_volume_flow
        )
        sheath_volume_flow = (
            self.sheath_volume_flow.value
            if isinstance(self.sheath_volume_flow, Enum)
            else self.sheath_volume_flow
        )

        flow_cell = fluidics.FlowCell(
            sample_volume_flow=sample_volume_flow,
            sheath_volume_flow=sheath_volume_flow,
            width=177 * ureg.micrometer,
            height=433 * ureg.micrometer,
        )

        scatterer_collection = fluidics.ScattererCollection(
            medium_refractive_index=1.33 * ureg.RIU
        )

        return fluidics.Fluidics(
            scatterer_collection=scatterer_collection, flow_cell=flow_cell
        )

    def get_optoelectronics(self) -> opto_electronics.OptoElectronics:
        """
        Returns the optoelectronics system.

        Returns
        -------
        opto_electronics.OptoElectronics
            Configured optoelectronics system
        """
        source = opto_electronics.source.AstigmaticGaussianBeam(
            waist_y=65 * ureg.micrometer,
            waist_z=10 * ureg.micrometer,
            wavelength=488 * ureg.nanometer,
            optical_power=self.optical_power,
        )

        amplifier = opto_electronics.TransimpedanceAmplifier(
            gain=10 * ureg.volt / ureg.ampere,
            bandwidth=10 * ureg.megahertz,
        )

        detector_0 = PMT(
            name="forward",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.7 * ureg.AU,
        )

        detector_1 = PMT(
            name="side",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.3 * ureg.AU,
            cache_numerical_aperture=0.1 * ureg.AU,
        )

        return opto_electronics.OptoElectronics(
            detectors=[detector_0, detector_1],
            source=source,
            amplifier=amplifier,
        )

    def get_signal_processing(self) -> signal_processing.SignalProcessing:
        """
        Returns the signal processing system.

        Returns
        -------
        signal_processing.SignalProcessing
            Configured signal processing system
        """
        digitizer = signal_processing.Digitizer(
            bit_depth="14bit",
            saturation_levels="auto",
            sampling_rate=10 * ureg.megahertz,
        )

        analog_processing = [
            signal_processing.circuits.BaselineRestorator(
                window_size=10 * ureg.microsecond
            ),
            signal_processing.circuits.BesselLowPass(
                cutoff=2 * ureg.megahertz, order=4, gain=2
            ),
        ]

        triggering = triggering_system.DynamicWindow(
            trigger_detector_name="forward",
            threshold="4sigma",
            pre_buffer=20,
            post_buffer=20,
            max_triggers=-1,
        )

        peak_algo = signal_processing.peak_locator.GlobalPeakLocator(
            compute_width=False
        )

        return signal_processing.SignalProcessing(
            digitizer=digitizer,
            analog_processing=analog_processing,
            triggering_system=triggering,
            peak_algorithm=peak_algo,
        )
