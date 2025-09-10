from TypedUnit import FlowRate, Power, Voltage, ureg

from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.instances.detector import PMT
from FlowCyPy.digitizer import Digitizer
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.flow_cytometer import FlowCytometer
from FlowCyPy.fluidics import Fluidics
from FlowCyPy.opto_electronics import OptoElectronics
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.source import GaussianBeam


class FacsCanto:
    def __new__(
        self,
        sample_volume_flow: FlowRate,
        sheath_volume_flow: FlowRate,
        optical_power: Power,
        background_power: Power,
        saturation_level: Voltage = 1 * ureg.volt,
    ):
        """
        Defines the FacsCanto flowcytometer with estimated parameters

        """
        flow_cell = FlowCell(
            sample_volume_flow=sample_volume_flow,
            sheath_volume_flow=sheath_volume_flow,
            width=400 * ureg.micrometer,
            height=400 * ureg.micrometer,
        )

        scatterer_collection = ScattererCollection(
            medium_refractive_index=1.33 * ureg.RIU
        )

        fluidics = Fluidics(
            scatterer_collection=scatterer_collection, flow_cell=flow_cell
        )

        source = GaussianBeam(
            numerical_aperture=0.2 * ureg.AU,
            wavelength=450 * ureg.nanometer,
            optical_power=optical_power,
        )

        digitizer = Digitizer(
            bit_depth="14bit",
            saturation_levels=(0 * ureg.volt, saturation_level),
            sampling_rate=10 * ureg.megahertz,
        )

        amplifier = TransimpedanceAmplifier(
            gain=10 * ureg.volt / ureg.ampere,
            bandwidth=60 * ureg.megahertz,
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

        opto_electronics = OptoElectronics(
            detectors=[detector_0, detector_1],
            digitizer=digitizer,
            source=source,
            amplifier=amplifier,
        )

        flow_cytometer = FlowCytometer(
            opto_electronics=opto_electronics,
            fluidics=fluidics,
            background_power=background_power,
        )

        return flow_cytometer
