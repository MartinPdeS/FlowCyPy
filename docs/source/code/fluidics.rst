.. _fluidics:

Fluidics
========

The :mod:`FlowCyPy.fluidics` package defines the physical input of a simulation.

It describes the geometry of the flow cell, the organization of particle populations, and the statistical distributions used to generate particle properties such as size and refractive index.

Together, these objects define what enters the optical interrogation region and how particles are spatially and temporally distributed before signal generation.

The typical workflow is:

1. define a :class:`FlowCyPy.fluidics.flow_cell.FlowCell`
2. build one or more particle populations
3. collect them in a :class:`FlowCyPy.fluidics.scatterer_collection.ScattererCollection`
4. combine the collection with the flow cell to create a fluidic configuration

This structure is used throughout FlowCyPy to generate realistic particle arrival statistics and physically consistent event streams.

Flow cell
---------

The flow cell defines the channel geometry and the hydrodynamic conditions used in the simulation.

It converts the specified sample and sheath flow rates into a focused sample region and provides the velocity field used to model particle transport.

.. autoclass:: FlowCyPy.fluidics.flow_cell.FlowCell
   :members:
   :show-inheritance:

Scatterer collection
--------------------

The scatterer collection is the container that stores all particle populations present in the simulated sample.

It provides a convenient interface for combining multiple populations, applying dilution, and passing the resulting sample definition to the fluidics engine.

.. autoclass:: FlowCyPy.fluidics.scatterer_collection.ScattererCollection
   :members:
   :show-inheritance:

Population models
-----------------

Population classes describe the physical properties of the particles present in the sample.

A population typically specifies its concentration, refractive index model, diameter distribution, and the sampling strategy used to instantiate individual particles during simulation.

Sphere population
+++++++++++++++++

Use this class for homogeneous spherical particles.

.. autoclass:: FlowCyPy.fluidics.populations.SpherePopulation
   :members:
   :show-inheritance:

Core-shell population
+++++++++++++++++++++

Use this class for layered particles composed of a core and a shell with distinct optical properties.

.. autoclass:: FlowCyPy.fluidics.populations.CoreShellPopulation
   :members:
   :show-inheritance:

Distribution models
-------------------

Distribution classes define how scalar particle properties are sampled.

They are commonly used for particle diameter, refractive index, or medium refractive index.

These models make it possible to represent monodisperse, weakly polydisperse, or broadly distributed populations within a consistent API.

Normal
++++++

The normal distribution generates values distributed around a mean with symmetric dispersion.

It is appropriate when fluctuations are approximately Gaussian and negative values are either physically excluded by bounds or unlikely within the chosen parameter range.

.. image:: ./../../images/distributions/Normal.png
   :width: 600
   :align: center

.. autoclass:: FlowCyPy.fluidics.distributions.Normal
   :members:
   :show-inheritance:

Log-normal
++++++++++

The log-normal distribution generates strictly positive values whose logarithm follows a normal distribution.

It is commonly used for particle sizes and other positive quantities with right-skewed variation.

.. image:: ./../../images/distributions/LogNormal.png
   :width: 600
   :align: center

.. autoclass:: FlowCyPy.fluidics.distributions.LogNormal
   :members:
   :show-inheritance:

Rosin-Rammler
+++++++++++++

The Rosin-Rammler distribution is widely used to model particle size distributions in dispersed materials.

It is particularly useful when the population contains many small particles and progressively fewer large particles.

.. image:: ./../../images/distributions/RosinRammler.png
   :width: 600
   :align: center

.. autoclass:: FlowCyPy.fluidics.distributions.RosinRammler
   :members:
   :show-inheritance:

Delta
+++++

The delta distribution represents a fixed value with no dispersion.

It is useful for monodisperse reference populations or for parameters that should remain constant across all simulated particles.

.. image:: ./../../images/distributions/Delta.png
   :width: 600
   :align: center

.. autoclass:: FlowCyPy.fluidics.distributions.Delta
   :members:
   :show-inheritance:

Uniform
+++++++

The uniform distribution samples values evenly between a lower and an upper bound.

It is appropriate when all values within an interval are considered equally likely.

.. image:: ./../../images/distributions/Uniform.png
   :width: 600
   :align: center

.. autoclass:: FlowCyPy.fluidics.distributions.Uniform
   :members:
   :show-inheritance:
