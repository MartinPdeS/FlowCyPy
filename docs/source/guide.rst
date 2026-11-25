Choose a workflow
=================

Build and inspect the simulation in stages: fluidics generates particle
arrivals; optical collection creates detector signals; electronics and digital
processing determine the measured events. Validate each stage before comparing
a complete acquisition with an experiment.

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: Complete tutorials
      :link: /gallery/tutorials/index
      :link-type: doc

      Connect fluidics, optics, electronics and processing.

   .. grid-item-card:: Parameter studies
      :link: /gallery/studies/index
      :link-type: doc

      Explore the effects of model and instrument settings.

   .. grid-item-card:: Validation examples
      :link: /gallery/validation/index
      :link-type: doc

      Check the expected behaviour of individual components.

   .. grid-item-card:: Understand the model
      :link: theory
      :link-type: doc

      Review the assumptions behind simulated signals.

.. toctree::
   :hidden:

   theory

Start with a named instrument
-----------------------------

Import a factory from its lowercase manufacturer module. Each call returns
a fresh Workflow. Edit its components, add your sample and run the acquisition.

.. code-block:: python

   from FlowCyPy.fluidics.populations import SpherePopulation
   from FlowCyPy.systems.bd import facs_canto_ii
   from FlowCyPy.units import ureg

   system = facs_canto_ii(optical_power=30 * ureg.milliwatt)
   system.opto_electronics.digitizer.bit_depth = 16
   beads = SpherePopulation(
       name="beads", diameter=200 * ureg.nanometer, refractive_index=1.59,
       medium_refractive_index=1.33, concentration=1e8 * ureg.particle / ureg.milliliter,
   )
   system.fluidics.scatterer_collection.add_population(beads)
   record = system.run(run_time=1 * ureg.millisecond, random_state=42)

The original FlowCyPy configurations are available as ``bd.facs_canto`` and
``cytek.reference``. The latter uses the signed ADC voltage ranges from the
Cytek bead comparison example.

The RosettaX-derived configurations use the wavelength, channel names, collection
angles, apertures and detector sampling in ``RosettaX/assets/instrument_catalog.toml``.
They simulate scatter channels. The common flow cell, beam waists, detector
electrical response, amplifier and 14-bit digitizer are FlowCyPy reference
settings. Replace them with measured components for instrument-specific predictions.

Browse the agilent, bd, beckman_coulter, cytek, miltenyi, nanofcm, sony,
stratedigm and thermo_fisher modules. When scatter channels use different lasers,
a wavelength suffix selects a single-laser acquisition, for example ``sony.id7000_405``.
Apogee geometries require angular weighting and a rectangular blocker that the
detector model does not implement.

For your own instrument, pass the fluidics, opto_electronics and digital_processing
components to ``Workflow.from_components``. To use the shared reference electronics,
define a ``ScatterSystem`` with a wavelength and a tuple of ``ScatterChannel`` objects.
Import both from ``FlowCyPy.systems``. The first channel is the default trigger.

Follow :doc:`gallery/tutorials/sony_id7000` to select a laser and change its
sampling rate. See :doc:`gallery/studies/compare_scatter_systems` to compare
side-scatter traces from two systems using the same bead sample.
