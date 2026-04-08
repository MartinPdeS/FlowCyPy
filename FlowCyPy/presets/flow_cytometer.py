from TypedUnit import FlowRate, Power, ureg

from FlowCyPy.presets.detector import PMT
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy import fluidics
from FlowCyPy import opto_electronics
from FlowCyPy import digital_processing
from FlowCyPy.run_record import RunRecord
from FlowCyPy.fluidics import SheathFlowRate, SampleFlowRate
from enum import Enum


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
        threshold: str = "4sigma",
        include_shot_noise: bool = True,
        include_rin_noise: bool = True,
    ):
        self.sample_volume_flow = sample_volume_flow
        self.sheath_volume_flow = sheath_volume_flow
        self.optical_power = optical_power
        self.threshold = threshold
        self.include_shot_noise = include_shot_noise
        self.include_rin_noise = include_rin_noise

        self.instance = FlowCytometer(
            fluidics=self.get_fluidics(),
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
        return self.instance.run(
            run_time=run_time,
            opto_electronics=self.get_optoelectronics(),
            digital_processing=self.get_digital_processing(),
        )

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

        scatterer_collection = fluidics.ScattererCollection()

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
        source = opto_electronics.source.Gaussian(
            waist_y=65 * ureg.micrometer,
            waist_z=10 * ureg.micrometer,
            wavelength=488 * ureg.nanometer,
            optical_power=self.optical_power,
            include_shot_noise=self.include_shot_noise,
            include_rin_noise=self.include_rin_noise,
        )

        amplifier = opto_electronics.Amplifier(
            gain=10 * ureg.volt / ureg.ampere,
            bandwidth=2 * ureg.megahertz,
        )

        digitizer = opto_electronics.Digitizer(
            bit_depth=14,
            use_auto_range=True,
            sampling_rate=10 * ureg.megahertz,
        )

        detector_0 = PMT(
            name="forward",
            phi_angle=0 * ureg.degree,
            numerical_aperture=1.2 * ureg.AU,
            dark_current=0 * ureg.picoampere,
        )

        detector_1 = PMT(
            name="side",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.3 * ureg.AU,
            cache_numerical_aperture=0.1 * ureg.AU,
            dark_current=0 * ureg.picoampere,
        )

        analog_processing = [
            opto_electronics.circuits.BaselineRestorationServo(
                time_constant=50 * ureg.microsecond
            ),
            opto_electronics.circuits.BesselLowPass(
                cutoff_frequency=2 * ureg.megahertz, order=4, gain=2
            ),
        ]

        return opto_electronics.OptoElectronics(
            detectors=[detector_0, detector_1],
            source=source,
            digitizer=digitizer,
            analog_processing=analog_processing,
            amplifier=amplifier,
        )

    def get_digital_processing(self) -> digital_processing.DigitalProcessing:
        """
        Returns the signal processing system.

        Returns
        -------
        digital_processing.DigitalProcessing
            Configured signal processing system
        """
        triggering = digital_processing.discriminator.DynamicWindow(
            trigger_channel="forward",
            threshold=self.threshold,
            pre_buffer=20,
            post_buffer=20,
            max_triggers=-1,
        )

        peak_algo = digital_processing.peak_locator.GlobalPeakLocator(
            compute_width=False
        )

        return digital_processing.DigitalProcessing(
            discriminator=triggering,
            peak_algorithm=peak_algo,
        )


class Cytek:
    """
    Defines the Cytek flowcytometer with estimated parameters.

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
        threshold: str = "4sigma",
        include_shot_noise: bool = True,
        include_rin_noise: bool = True,
    ):
        self.sample_volume_flow = sample_volume_flow
        self.sheath_volume_flow = sheath_volume_flow
        self.optical_power = optical_power
        self.threshold = threshold
        self.include_shot_noise = include_shot_noise
        self.include_rin_noise = include_rin_noise

        self.instance = FlowCytometer(
            fluidics=self.get_fluidics(),
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
        return self.instance.run(
            run_time=run_time,
            opto_electronics=self.get_optoelectronics(),
            digital_processing=self.get_digital_processing(),
        )

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

        scatterer_collection = fluidics.ScattererCollection()

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
        source = opto_electronics.source.Gaussian(
            waist_y=65 * ureg.micrometer,
            waist_z=10 * ureg.micrometer,
            wavelength=488 * ureg.nanometer,
            optical_power=self.optical_power,
            bandwidth=10 * ureg.megahertz,
            include_shot_noise=self.include_shot_noise,
            include_rin_noise=self.include_rin_noise,
            rin=-250 * ureg.dB_per_Hz,
        )

        amplifier = opto_electronics.Amplifier(
            gain=1 * ureg.volt / ureg.ampere,
            bandwidth=2 * ureg.megahertz,
        )

        digitizer = opto_electronics.Digitizer(
            sampling_rate=10 * ureg.megahertz,
            bit_depth=22,
            use_auto_range=False,
            output_signed_codes=True,
            channel_range_mode="shared",
        )

        detector_0 = opto_electronics.Detector(
            name="FSC",
            phi_angle=0 * ureg.degree,
            numerical_aperture=1.1,
            bandwidth=10 * ureg.megahertz,
            dark_current=0 * ureg.picoampere,
            current_noise_density=300 * ureg.femtoampere / ureg.sqrt_hertz,
        )

        detector_1 = opto_electronics.Detector(
            name="SSC",
            phi_angle=0 * ureg.degree,
            numerical_aperture=0.1,
            cache_numerical_aperture=0.04,
            bandwidth=10 * ureg.megahertz,
            dark_current=0 * ureg.picoampere,
            current_noise_density=20 * ureg.femtoampere / ureg.sqrt_hertz,
        )

        analog_processing = [
            opto_electronics.circuits.BesselLowPass(
                cutoff_frequency=1 * ureg.megahertz, order=4, gain=2
            ),
            opto_electronics.circuits.BaselineRestorationServo(
                time_constant=20 * ureg.microsecond, initialize_with_first_sample=False
            ),
        ]

        return opto_electronics.OptoElectronics(
            detectors=[detector_0, detector_1],
            source=source,
            digitizer=digitizer,
            analog_processing=analog_processing,
            amplifier=amplifier,
        )

    def get_digital_processing(self) -> digital_processing.DigitalProcessing:
        """
        Returns the signal processing system.

        Returns
        -------
        digital_processing.DigitalProcessing
            Configured signal processing system
        """
        discriminator = digital_processing.discriminator.DynamicWindow(
            trigger_channel="SSC",
            threshold=self.threshold,
            pre_buffer=2,
            post_buffer=2,
            max_triggers=-1,
        )

        peak_algo = digital_processing.peak_locator.GlobalPeakLocator(
            compute_width=False,
            compute_area=True,
            allow_negative_area=True,
            support=digital_processing.peak_locator.FullWindowSupport(),
            polarity="positive",
            height_mode="peak_to_baseline",
            baseline_mode="zero",
        )

        return digital_processing.DigitalProcessing(
            discriminator=discriminator,
            peak_algorithm=peak_algo,
        )
