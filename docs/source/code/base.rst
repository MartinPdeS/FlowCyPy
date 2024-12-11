Classes and Methods
===================

This section documents the main classes and methods available in the **FlowCyPy** library, grouped by functionality.

Flow Parameters
---------------
Classes that deal with flow cytometry system parameters.

FlowCell Class
~~~~~~~~~~~~~~

.. autoclass:: FlowCyPy.FlowCell
   :members:
   :show-inheritance:
   :exclude-members: flow_speed, flow_area, run_time
   :undoc-members:

Laser Sources
-------------
Classes representing laser beam sources.

GaussianBeam
~~~~~~~~~~~~

.. autoclass:: FlowCyPy.source.GaussianBeam
   :members:
   :show-inheritance:
   :exclude-members: numerical_aperture, optical_power, polarization, wavelength

AstigmaticGaussianBeam
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: FlowCyPy.source.AstigmaticGaussianBeam
   :members:
   :show-inheritance:
   :exclude-members: numerical_aperture_x, numerical_aperture_y, optical_power, polarization, wavelength

Scatterers
----------
Classes representing particles and populations within the cytometer.

Scatterer
~~~~~~~~~

.. autoclass:: FlowCyPy.Scatterer
   :members:
   :show-inheritance:

Population
~~~~~~~~~~

.. autoclass:: FlowCyPy.population.Population
   :members:
   :show-inheritance:
   :exclude-members: name, refractive_index, size

Detectors
---------
Classes for modeling the signal detection process in flow cytometry.

Detector
~~~~~~~~

.. autoclass:: FlowCyPy.detector.Detector
   :members:
   :show-inheritance:
   :exclude-members: resistance, responsitivity, sampling, sampling_freq, saturation_level, temperature, n_bins, name, noise_level, numerical_aperture, phi_angle, dark_current, gamma_angle

Cytometry Systems
-----------------
Classes related to the overall configuration of a flow cytometry system.

FlowCytometer
~~~~~~~~~~~~~

.. autoclass:: FlowCyPy.cytometer.FlowCytometer
   :members:
   :show-inheritance:

Analysis Tools
--------------
Classes for processing and analyzing data from flow cytometry experiments.

EventCorrelator Class
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: FlowCyPy.event_correlator.EventCorrelator
   :members:
   :show-inheritance:
