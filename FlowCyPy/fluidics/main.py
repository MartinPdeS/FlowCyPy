from TypedUnit import Time, Frequency, Concentration
import pandas as pd
import numpy as np

from .scatterer_collection import ScattererCollection
from .event_collection import EventCollection, PopulationEvents
from .flow_cell import FlowCell
from .populations import BasePopulation, ExplicitModel, GammaModel


class Fluidics:
    def __init__(self, scatterer_collection: ScattererCollection, flow_cell: FlowCell):
        """
        Initializes the Fluidics system with a scatterer collection and a flow cell.

        Parameters
        ----------
        scatterer_collection : ScattererCollection, optional
            The collection of particles or scatterers to be processed in the flow cytometer.
        flow_cell : FlowCell, optional
            The flow cell through which the particles will pass.
        """
        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell

    def generate_event_collection(
        self,
        run_time: Time,
        sampling_rate: Frequency,
    ) -> EventCollection:
        """
        Generate the full event collection for all configured populations.

        Parameters
        ----------
        run_time : Time
            Acquisition duration.

        Returns
        -------
        EventCollection
            Structured population event blocks with coupling already evaluated.
        """
        event_collection = EventCollection()

        for population in self.scatterer_collection.populations:
            effective_concentration = population.get_effective_concentration()

            if isinstance(population.sampling_method, ExplicitModel):
                events = self._generate_explicit_event(
                    population=population,
                    effective_concentration=effective_concentration,
                    run_time=run_time,
                )

            elif isinstance(population.sampling_method, GammaModel):
                events = self._generate_gamma_event(
                    population=population,
                    effective_concentration=effective_concentration,
                    sampling_rate=sampling_rate,
                )

            else:
                raise TypeError(
                    f"Unsupported sampling method: {population.sampling_method.__class__.__name__}"
                )

            event_collection.append(events)

        # opto_electronics._add_coupling_to_dataframe(
        #     event_collection=event_collection,
        #     compute_cross_section=False,
        # )

        return event_collection

    def _generate_explicit_event(
        self,
        population: BasePopulation,
        effective_concentration,
        run_time: Time,
    ) -> PopulationEvents:
        """
        Generate explicit event data for one population.

        Parameters
        ----------
        population : populations.BasePopulation
            Population to simulate.
        effective_concentration : pint.Quantity
            Effective concentration after any selection or dilution.
        run_time : Time
            Acquisition duration.

        Returns
        -------
        PopulationEvents
            Structured explicit event block.
        """
        flow_volume_per_second = (
            self.flow_cell.sample.average_flow_speed * self.flow_cell.sample.area
        )
        particle_flux = effective_concentration * flow_volume_per_second

        number_of_events = int(
            np.rint((particle_flux * run_time).to("particle").magnitude)
        )

        dataframe = pd.DataFrame(index=range(max(number_of_events, 0)))
        events = self._build_population_events(
            dataframe=dataframe, population=population
        )

        if number_of_events <= 0:
            events.metadata["NumberOfEvents"] = 0
            return events

        self.add_population_property_to_events(
            events=events,
            population=population,
        )

        arrival_time = self.flow_cell.sample_arrival_times(
            n_events=number_of_events,
            run_time=run_time,
        )

        x_position, y_position, velocities = self.flow_cell.sample_transverse_profile(
            number_of_events
        )

        events.set_quantity_column(column_name="Time", value=arrival_time)
        events.set_quantity_column(column_name="x", value=x_position)
        events.set_quantity_column(column_name="y", value=y_position)
        events.set_quantity_column(column_name="Velocity", value=velocities)

        events.metadata["NumberOfEvents"] = number_of_events

        return events

    def _generate_gamma_event(
        self,
        population: BasePopulation,
        effective_concentration: Concentration,
        sampling_rate: Frequency,
    ) -> PopulationEvents:
        """
        Generate support data for one gamma model population.

        Parameters
        ----------
        population : populations.BasePopulation
            Population to simulate.
        effective_concentration : pint.Quantity
            Effective concentration after any selection or dilution.
        opto_electronics : OptoElectronics
            Opto electronic configuration used to compute occupancy related
            metadata.

        Returns
        -------
        PopulationEvents
            Structured gamma model event block.
        """
        number_of_events = population.sampling_method.number_of_samples

        dataframe = pd.DataFrame(index=range(number_of_events))
        events = self._build_population_events(
            dataframe=dataframe, population=population
        )

        x_position, y_position, velocities = self.flow_cell.sample_transverse_profile(
            number_of_events
        )

        events.set_quantity_column(column_name="x", value=x_position)
        events.set_quantity_column(column_name="y", value=y_position)
        events.set_quantity_column(column_name="Velocity", value=velocities)

        self.add_population_property_to_events(
            events=events,
            population=population,
        )

        mean_velocity = events.get_quantity("Velocity").mean()

        interrogation_volume_per_time_bin = (
            mean_velocity / sampling_rate * self.flow_cell.sample.area
        )

        expected_number_of_particles = (
            (effective_concentration * interrogation_volume_per_time_bin)
            .to("particle")
            .magnitude
        )

        events.metadata["VelocityMean"] = mean_velocity
        events.metadata["InterrogationVolumePerTimeBin"] = (
            interrogation_volume_per_time_bin
        )
        events.metadata["ExpectedNumberOfParticles"] = expected_number_of_particles
        events.metadata["NumberOfEvents"] = number_of_events

        return events

    def _build_population_events(
        self,
        dataframe: pd.DataFrame,
        population: BasePopulation,
    ) -> PopulationEvents:
        """
        Build a structured event container for one population.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Event table for one population.
        population : BasePopulation
            Population that generated the events.

        Returns
        -------
        PopulationEvents
            Structured event block.
        """
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

    def add_population_property_to_events(
        self,
        events: PopulationEvents,
        population: BasePopulation,
    ) -> None:
        """
        Sample population specific properties and append them to the event table.

        Parameters
        ----------
        events : PopulationEvents
            Event block updated in place.
        population : BasePopulation
            Population providing the sampled properties.
        """
        properties = population.sample(number_of_samples=len(events.dataframe))

        for key, value in properties.items():
            events.set_quantity_column(column_name=key, value=value)

    def _generate_explicit_event(
        self,
        population: BasePopulation,
        effective_concentration,
        run_time: Time,
    ) -> PopulationEvents:
        """
        Generate explicit event data for one population.

        Parameters
        ----------
        population : BasePopulation
            Population to simulate.
        effective_concentration : pint.Quantity
            Effective concentration after any selection or dilution.
        run_time : Time
            Acquisition duration.

        Returns
        -------
        PopulationEvents
            Structured explicit event block.
        """
        flow_volume_per_second = (
            self.flow_cell.sample.average_flow_speed * self.flow_cell.sample.area
        )
        particle_flux = effective_concentration * flow_volume_per_second

        number_of_events = int(
            np.rint((particle_flux * run_time).to("particle").magnitude)
        )

        dataframe = pd.DataFrame(index=range(max(number_of_events, 0)))
        events = self._build_population_events(
            dataframe=dataframe, population=population
        )

        if number_of_events <= 0:
            events.metadata["NumberOfEvents"] = 0
            return events

        self.add_population_property_to_events(
            events=events,
            population=population,
        )

        arrival_time = self.flow_cell.sample_arrival_times(
            n_events=number_of_events,
            run_time=run_time,
        )

        x_position, y_position, velocities = self.flow_cell.sample_transverse_profile(
            number_of_events
        )

        events.set_quantity_column(column_name="Time", value=arrival_time)
        events.set_quantity_column(column_name="x", value=x_position)
        events.set_quantity_column(column_name="y", value=y_position)
        events.set_quantity_column(column_name="Velocity", value=velocities)

        events.metadata["NumberOfEvents"] = number_of_events

        return events
