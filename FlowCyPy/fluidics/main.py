from TypedUnit import Time, Frequency, Concentration
import numpy as np

from .scatterer_collection import ScattererCollection
from .event_collection import EventCollection, PopulationEvents
from .flow_cell import FlowCell
from .populations import BasePopulation, ExplicitModel, GammaModel
from FlowCyPy.sub_frames.events import EventDataFrame


class Fluidics:
    def __init__(
        self,
        scatterer_collection: ScattererCollection,
        flow_cell: FlowCell,
    ):
        """
        Initialize the fluidics system.

        Parameters
        ----------
        scatterer_collection : ScattererCollection
            Collection of populations to simulate.
        flow_cell : FlowCell
            Flow cell through which particles are transported.
        """
        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell

    def generate_event_collection(
        self,
        run_time: Time,
        sampling_rate: Frequency,
    ) -> EventCollection:
        """
        Generate the event collection for all configured populations.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.
        sampling_rate : Frequency
            Sampling rate used for gamma model occupancy calculations.

        Returns
        -------
        EventCollection
            Population resolved event blocks.
        """
        event_collection = EventCollection()

        for population in self.scatterer_collection.populations:
            effective_concentration = population.get_effective_concentration()

            event_block = self._generate_population_event_block(
                population=population,
                effective_concentration=effective_concentration,
                run_time=run_time,
                sampling_rate=sampling_rate,
            )

            event_collection.append(event_block)

        return event_collection

    def _generate_population_event_block(
        self,
        population: BasePopulation,
        effective_concentration: Concentration,
        run_time: Time,
        sampling_rate: Frequency,
    ) -> PopulationEvents:
        """
        Generate the event block for one population.
        """
        if isinstance(population.sampling_method, ExplicitModel):
            return self._generate_explicit_event_block(
                population=population,
                effective_concentration=effective_concentration,
                run_time=run_time,
            )

        if isinstance(population.sampling_method, GammaModel):
            return self._generate_gamma_event_block(
                population=population,
                effective_concentration=effective_concentration,
                sampling_rate=sampling_rate,
            )

        raise TypeError(
            f"Unsupported sampling method: {population.sampling_method.__class__.__name__}"
        )

    def _generate_explicit_event_block(
        self,
        population: BasePopulation,
        effective_concentration: Concentration,
        run_time: Time,
    ) -> PopulationEvents:
        """
        Generate explicit event data for one population.
        """
        number_of_events = self._compute_number_of_explicit_events(
            effective_concentration=effective_concentration,
            run_time=run_time,
        )

        event_block = self._create_population_event_block(
            population=population,
            number_of_events=number_of_events,
        )

        event_block.metadata["NumberOfEvents"] = number_of_events

        if number_of_events <= 0:
            return event_block

        self._add_sampled_population_properties(
            event_block=event_block,
            population=population,
        )

        self._add_sampled_flow_properties(
            event_block=event_block,
            number_of_events=number_of_events,
        )

        self._add_explicit_arrival_times(
            event_block=event_block,
            number_of_events=number_of_events,
            run_time=run_time,
        )

        return event_block

    def _generate_gamma_event_block(
        self,
        population: BasePopulation,
        effective_concentration: Concentration,
        sampling_rate: Frequency,
    ) -> PopulationEvents:
        """
        Generate gamma model support data for one population.
        """
        number_of_events = population.sampling_method.number_of_samples

        event_block = self._create_population_event_block(
            population=population,
            number_of_events=number_of_events,
        )

        self._add_sampled_population_properties(
            event_block=event_block,
            population=population,
        )

        self._add_sampled_flow_properties(
            event_block=event_block,
            number_of_events=number_of_events,
        )

        mean_velocity = event_block.get_quantity("Velocity").mean()

        interrogation_volume_per_time_bin = (
            mean_velocity / sampling_rate * self.flow_cell.sample.area
        )

        expected_number_of_particles = (
            (effective_concentration * interrogation_volume_per_time_bin)
            .to("particle")
            .magnitude
        )

        event_block.metadata["VelocityMean"] = mean_velocity
        event_block.metadata["InterrogationVolumePerTimeBin"] = (
            interrogation_volume_per_time_bin
        )
        event_block.metadata["ExpectedNumberOfParticles"] = expected_number_of_particles
        event_block.metadata["NumberOfEvents"] = number_of_events

        return event_block

    def _compute_number_of_explicit_events(
        self,
        effective_concentration: Concentration,
        run_time: Time,
    ) -> int:
        """
        Compute the number of explicit events expected during the acquisition.
        """
        flow_volume_per_second = (
            self.flow_cell.sample.average_flow_speed * self.flow_cell.sample.area
        )

        particle_flux = effective_concentration * flow_volume_per_second

        return int(np.rint((particle_flux * run_time).to("particle").magnitude))

    def _create_population_event_block(
        self,
        population: BasePopulation,
        number_of_events: int,
    ) -> PopulationEvents:
        """
        Create an empty structured event block for one population.
        """
        dataframe = EventDataFrame(index=range(max(number_of_events, 0)))

        return PopulationEvents(
            dataframe=dataframe,
            population=population,
            sampling_method=population.sampling_method,
            name=population.name,
            scatterer_type=population.__class__.__name__,
            metadata={
                "Name": population.name,
                "PopulationType": population.__class__.__name__,
                "ParticleCount": population.concentration,
                "SamplingMethod": population.sampling_method.__class__.__name__,
            },
        )

    def _add_sampled_population_properties(
        self,
        event_block: PopulationEvents,
        population: BasePopulation,
    ) -> None:
        """
        Sample population specific properties and append them to the event table.
        """
        properties = population.sample(number_of_samples=len(event_block))

        for column_name, values in properties.items():
            event_block.set_quantity_column(column_name=column_name, value=values)

    def _add_sampled_flow_properties(
        self,
        event_block: PopulationEvents,
        number_of_events: int,
    ) -> None:
        """
        Sample transverse positions and velocities and append them to the event table.
        """
        x_position, y_position, velocities = self.flow_cell.sample_transverse_profile(
            number_of_events
        )

        event_block.set_quantity_column(column_name="x", value=x_position)
        event_block.set_quantity_column(column_name="y", value=y_position)
        event_block.set_quantity_column(column_name="Velocity", value=velocities)

    def _add_explicit_arrival_times(
        self,
        event_block: PopulationEvents,
        number_of_events: int,
        run_time: Time,
    ) -> None:
        """
        Sample explicit arrival times and append them to the event table.
        """
        arrival_time = self.flow_cell.sample_arrival_times(
            n_events=number_of_events,
            run_time=run_time,
        )

        event_block.set_quantity_column(column_name="Time", value=arrival_time)
