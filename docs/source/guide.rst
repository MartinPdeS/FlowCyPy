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
scatter-only PMTs on a 488 nm instrument. The dye parameters are illustrative.

.. code-block:: python

   import numpy as np
   from FlowCyPy.detectors.photomultipliers import pmt
   from FlowCyPy.fluorescence import Bandpass, Fluorophore, Label
   from FlowCyPy.samples.beads import microbeads
   from FlowCyPy.systems.bd import facs_canto
   from FlowCyPy.units import ureg

   instrument = facs_canto()
   dye = Fluorophore(
       name="green dye",
       absorption_cross_section=2e-20 * ureg.meter**2,
       quantum_yield=0.8,
       lifetime=4 * ureg.nanosecond,
       emission_wavelengths=np.array([510, 520, 530, 550]) * ureg.nm,
       photon_weights=(1, 4, 3, 2),
   )
   beads = microbeads(
       name="labeled beads", diameter=300 * ureg.nm, refractive_index=1.59,
       medium_refractive_index=1.33, concentration=1e9 * ureg.particle / ureg.mL,
       labels=[Label(fluorophore=dye, molecules_per_particle=20_000)],
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
accepts the 520 and 530 nm bins, or 70% of emitted photons before geometric
collection. Supply integrated photon counts per spectral bin and use finer bins
near a passband edge. A detector defaults to scatter only. Select both scatter
and fluorescence for a mixed channel. Its filter applies to elastic scatter at
the laser wavelength as well as to emission.

Use a molecular absorption cross section measured at the acquisition wavelength.
The model assumes weak excitation, isotropic emission, collection in air
with an optional central obscuration, and constant detector responsivity across
the band. Shot noise uses the photon energy of each emission bin. Background
power represents in-channel background at the laser wavelength. Fluorescent
populations use explicit event sampling. A dimensionless FlowCyPy distribution
can supply molecule counts, sampled once per particle and shared across channels.
The event column for this example is named "Label:green dye".

A fluorophore's optional lifetime is the mean delay from absorption to emission.
Omit it or supply zero for prompt emission. For a positive lifetime, FlowCyPy
applies a single exponential decay to each dye after laser intensity noise and
before photon shot noise and detector electronics. The simulation treats the
excitation as constant within each sampling interval and computes the mean
emitted power in that bin. Choose a sampling interval that resolves the
excitation pulse. The existing periodic acquisition boundary carries the decay
tail into the beginning of the trace, conserving energy over a complete window.
Event-frame power columns describe prompt coupling amplitudes. Read the analog
waveforms for the delayed signal.

See :doc:`gallery/tutorials/fluorescence_acquisition` to compare labeled and
unlabeled beads in one acquisition and :doc:`gallery/studies/fluorescence_bandpass`
to calculate spectral spillover.
