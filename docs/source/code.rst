Code Documentation
==================

This document provides the API documentation for the Flow Cytometer simulation code, which models
the flow of particles through a flow cytometer and generates particle arrival times based on a
Poisson process. The classes and functions documented here are automatically generated from the
codebase using Sphinx `autoclass` directives.

Classes and Methods
===================

Below are the primary classes and methods used in the flow cytometer simulation.

FlowCell Class
--------------

.. autoclass:: FlowCyPy.FlowCell
   :members:
   :show-inheritance:

ScattererDistribution Class
---------------------------

.. autoclass:: FlowCyPy.ScattererDistribution
   :members:
   :show-inheritance:

FlowCytometer Class
-------------------

.. autoclass:: FlowCyPy.FlowCytometer
   :members:
   :show-inheritance:

Distribution Classes
====================

The **Distribution** classes define how particle sizes are generated in the simulation. These classes allow for flexible modeling of particle sizes, whether they follow a normal distribution, a uniform range, or a fixed size. Below are the available distribution classes.

NormalDistribution Class
------------------------

The `NormalDistribution` generates particle sizes that follow a normal (Gaussian) distribution.

.. autoclass:: FlowCyPy.distribution.NormalDistribution
   :members:
   :show-inheritance:

LogNormalDistribution Class
---------------------------

The `LogNormalDistribution` generates particle sizes that follow a log-normal distribution, where the logarithm of the sizes follows a normal distribution.

.. autoclass:: FlowCyPy.distribution.LogNormalDistribution
   :members:
   :show-inheritance:

DeltaDistribution Class
-----------------------

The `DeltaDistribution` generates a fixed particle size, modeling a delta-like distribution where all particles have the same size.

.. autoclass:: FlowCyPy.distribution.DeltaDistribution
   :members:
   :show-inheritance:

UniformDistribution Class
-------------------------

The `UniformDistribution` generates particle sizes that are evenly distributed between a lower and upper bound.

.. autoclass:: FlowCyPy.distribution.UniformDistribution
   :members:
   :show-inheritance:

WeibullDistribution Class
-------------------------

The `WeibullDistribution` generates particle sizes following a Weibull distribution, which is flexible for modeling skewed particle size distributions.

.. autoclass:: FlowCyPy.distribution.WeibullDistribution
   :members:
   :show-inheritance:
