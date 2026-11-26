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
a fresh FlowCytometer. Edit its components, add your sample and run the acquisition.

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
components to ``FlowCytometer``. To use the shared reference electronics,
define a ``ScatterSystem`` with a wavelength and a tuple of ``ScatterChannel`` objects.
The first channel is the default trigger. Follow :doc:`gallery/tutorials/build_a_reusable_scatter_system`
to define the geometry or :doc:`gallery/tutorials/assemble_a_flow_cytometer`
to choose the flow cell, optics and electronics individually.

Follow :doc:`gallery/tutorials/select_a_laser_on_sony_id7000` to select a laser and change its
sampling rate. See :doc:`gallery/studies/compare_scatter_systems` to compare
side-scatter traces from two systems using the same bead sample.

Choose a population preset
--------------------------

Select an instrument by manufacturer and a population by sample family.

.. code-block:: python

   from FlowCyPy.samples.vesicles import exosome
   from FlowCyPy.systems.bd import facs_canto
   from FlowCyPy.units import ureg

   instrument = facs_canto()
   vesicles = exosome(name="EV sample", concentration=1e8 * ureg.particle / ureg.milliliter)
   instrument.fluidics.scatterer_collection.add_population(vesicles)

The vesicles module also includes microvesicles and apoptotic bodies. Use
FlowCyPy.samples.lipoproteins for HDL, LDL and VLDL, FlowCyPy.samples.cells
for platelets and cellular debris, and FlowCyPy.samples.beads for monodisperse
beads. Each call builds a fresh population. The biological presets retain
the project's reference diameter and refractive-index distributions.

Choose a detector preset
------------------------

Use ``pmt`` from ``FlowCyPy.detectors.photomultipliers`` for a photomultiplier
tube, or ``pin`` and ``apd`` from ``FlowCyPy.detectors.photodiodes`` for PIN and
avalanche photodiodes. Each factory creates a fresh channel with its reference
responsivity and dark current. Supply the collection geometry and override
electrical settings for a particular detector.

Add fluorescence to an acquisition
----------------------------------

Label a sphere or core-shell population and select the optical contributions
on each detector. This example adds a fluorescence PMT alongside the existing
scatter-only PMTs on a 488 nm instrument. For this example, approximate
FITC absorption at 488 nm by its peak value at 494 nm.

.. code-block:: python

   from FlowCyPy.detectors.photomultipliers import pmt
   from FlowCyPy.dyes import fitc
   from FlowCyPy.fluorescence import Bandpass, Label
   from FlowCyPy.samples.beads import microbeads
   from FlowCyPy.systems.bd import facs_canto
   from FlowCyPy.units import ureg

   instrument = facs_canto()
   beads = microbeads(
       name="labeled beads", diameter=300 * ureg.nm, refractive_index=1.59,
       medium_refractive_index=1.33, concentration=1e9 * ureg.particle / ureg.mL,
       labels=[Label(fluorophore=fitc(), molecules_per_particle=20_000)],
   )
   instrument.fluidics.scatterer_collection.add_population(beads)
   green = pmt(
       name="green", phi_angle=90 * ureg.degree, numerical_aperture=0.8,
       signals=("fluorescence",),
       optical_filter=Bandpass(center=530 * ureg.nm, width=30 * ureg.nm),
   )
   optics = instrument.opto_electronics
   optics.detectors = [*optics.detectors, green]
   record = instrument.acquire(run_time=1 * ureg.millisecond, random_state=42)
   voltage = record.signal.analog["green"]

The bandpass transmits all light from 515 through 545 nm inclusive. Here it
accepts the preset’s single 518 nm emission bin. To model partial transmission,
use a spectrum with multiple bins. Supply integrated photon counts per spectral bin and use finer bins
near a passband edge. A detector defaults to scatter only. Select both scatter
and fluorescence for a mixed channel. Its filter applies to elastic scatter at
the laser wavelength as well as to emission.

Use the event collection to inspect molecule counts and prompt optical powers.
Use the analog record for pulse timing and measured voltage. The
:doc:`fluorescence_model` explains the units, scope and approximations.

* :doc:`gallery/tutorials/detect_labeled_beads` follows labeled and unlabeled
  beads through optical detection, triggering and peak extraction.
* :doc:`gallery/tutorials/define_custom_dye_spectra` predicts two channel power
  ratios and checks them against simulated single-color controls.
* :doc:`gallery/studies/measure_fluorescence_gate_loss` measures the fraction
  of a short pulse captured in a nanosecond gate.
