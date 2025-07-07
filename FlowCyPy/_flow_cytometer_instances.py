

from FlowCyPy import units
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.cytometer import FlowCytometer
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.fluidics import Fluidics
from FlowCyPy.source import GaussianBeam
from FlowCyPy.digitizer import Digitizer
from FlowCyPy.amplifier import TransimpedanceAmplifier
from FlowCyPy.detector import PMT
from FlowCyPy.opto_electronics import OptoElectronics


class FacsCanto():
    def __new__(self,
        sample_volume_flow: units.Quantity,
        sheath_volume_flow: units.Quantity,
        optical_power: units.Quantity,
        background_power: units.Quantity,
        saturation_level: units.Quantity = 1 * units.volt):
        """
        Defines the FacsCanto flowcytometer with estimated parameters

        """
        flow_cell = FlowCell(
            sample_volume_flow=sample_volume_flow,
            sheath_volume_flow=sheath_volume_flow,
            width=400 * units.micrometer,
            height=400 * units.micrometer,
        )

        scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

        fluidics = Fluidics(
            scatterer_collection=scatterer_collection,
            flow_cell=flow_cell
        )

        source = GaussianBeam(
            numerical_aperture=0.2 * units.AU,
            wavelength=450 * units.nanometer,
            optical_power=optical_power
        )

        digitizer = Digitizer(
            bit_depth='14bit',
            saturation_levels=(0 * units.volt, saturation_level),
            sampling_rate=10 * units.megahertz,
        )

        amplifier = TransimpedanceAmplifier(
            gain=10 * units.volt / units.ampere,
            bandwidth=60 * units.megahertz,
        )

        detector_0 = PMT(
            name='forward',
            phi_angle=0 * units.degree,
            numerical_aperture=0.7 * units.AU,
        )

        detector_1 = PMT(
            name='side',
            phi_angle=0 * units.degree,
            numerical_aperture=0.3 * units.AU,
            cache_numerical_aperture=0.1 * units.AU,
        )

        opto_electronics = OptoElectronics(
            detectors=[detector_0, detector_1],
            digitizer=digitizer,
            source=source,
            amplifier=amplifier
        )

        flow_cytometer = FlowCytometer(
            opto_electronics=opto_electronics,
            fluidics=fluidics,
            background_power=background_power
        )

        return flow_cytometer
