|logo|

FlowCyPy
========

**Simulate a flow-cytometry experiment from particle populations to measured
signals.**

|python| |pypi| |docs| |ci| |license|

FlowCyPy is a Python toolkit for building physically motivated flow-cytometer
simulations. Define particles and fluidics, illuminate them with a configurable
source, model detector and electronics, then inspect analog and digital
acquisition as one reproducible workflow.

Why FlowCyPy?
-------------

* **Particle-aware fluidics** — model flow cells, sample and sheath flow, and
  configurable particle populations.
* **Optical scattering** — calculate detector signals from particle size,
  refractive index, wavelength and collection geometry.
* **Instrument realism** — add detectors, amplifiers, analog circuits,
  digitization, shot noise and laser noise.
* **Event-level results** — trigger, locate peaks, classify events and plot
  measurements with pandas-friendly result frames.
* **Units by default** — express physical parameters with explicit units.

Installation
------------

.. code-block:: console

   $ python -m pip install FlowCyPy

FlowCyPy requires Python 3.11 or newer. Pre-built wheels are available for
Linux x86_64 and macOS arm64. To install from source with development tools:

.. code-block:: console

   $ git clone https://github.com/MartinPdeS/FlowCyPy.git
   $ cd FlowCyPy
   $ python -m pip install -e ".[testing,documentation]"

Quick start
-----------

The example below builds a small two-channel simulation. Each stage is
independent, so you can replace a population model, detector, circuit or
processing algorithm without rewriting the rest of the experiment.

.. code-block:: python

   from FlowCyPy import FlowCytometer
   from FlowCyPy.units import ureg
   from FlowCyPy.fluidics import (
       FlowCell, Fluidics, SampleFlowRate, ScattererCollection,
       SheathFlowRate, distributions, populations,
   )
   from FlowCyPy.opto_electronics import (
       Amplifier, Detector, Digitizer, OptoElectronics, circuits, source,
   )
   from FlowCyPy.digital_processing import (
       DigitalProcessing, discriminator, peak_locator,
   )

   # 1. Fluidics and particles
   flow_cell = FlowCell(
       sample_volume_flow=SampleFlowRate.MEDIUM.value,
       sheath_volume_flow=SheathFlowRate.MEDIUM.value,
       width=400 * ureg.micrometer,
       height=150 * ureg.micrometer,
   )
   population = populations.SpherePopulation(
       name="beads",
       medium_refractive_index=distributions.Delta(1.33),
       concentration=1e10 * ureg.particle / ureg.milliliter,
       diameter=distributions.RosinRammler(
           scale=200 * ureg.nanometer, shape=10,
       ),
       refractive_index=distributions.Normal(
           mean=1.44, standard_deviation=0.002, low_cutoff=1.33,
       ),
       sampling_method=populations.GammaModel(number_of_samples=2_000),
   )
   fluidics = Fluidics(
       scatterer_collection=ScattererCollection(populations=[population]),
       flow_cell=flow_cell,
   )

   # 2. Optics, detectors and acquisition electronics
   optics = OptoElectronics(
       source=source.Gaussian(
           waist_z=10 * ureg.micrometer,
           waist_y=60 * ureg.micrometer,
           wavelength=405 * ureg.nanometer,
           optical_power=200 * ureg.milliwatt,
       ),
       detectors=[
           Detector(name="forward", phi_angle=0 * ureg.degree,
                    numerical_aperture=0.3,
                    responsivity=1 * ureg.ampere / ureg.watt),
           Detector(name="side", phi_angle=90 * ureg.degree,
                    numerical_aperture=1.1,
                    responsivity=1 * ureg.ampere / ureg.watt),
       ],
       amplifier=Amplifier(
           gain=10 * ureg.volt / ureg.ampere,
           bandwidth=10 * ureg.megahertz,
       ),
       digitizer=Digitizer(
           sampling_rate=60 * ureg.megahertz,
           bit_depth=14,
           use_auto_range=True,
       ),
       analog_processing=[
           circuits.BesselLowPass(
               cutoff_frequency=2 * ureg.megahertz, order=4, gain=2,
           ),
       ],
   )

   # 3. Triggering and peak extraction
   processing = DigitalProcessing(
       discriminator=discriminator.FixedWindow(
           trigger_channel="side", threshold="4sigma",
           pre_buffer=40, post_buffer=40, max_triggers=-1,
       ),
       peak_algorithm=peak_locator.GlobalPeakLocator(),
   )

   # 4. Run and inspect the acquisition
   cytometer = FlowCytometer(
       fluidics=fluidics,
       background_power=0.001 * ureg.milliwatt,
   )
   record = cytometer.run(
       opto_electronics=optics,
       digital_processing=processing,
       run_time=1 * ureg.millisecond,
   )
   record.event_collection.plot(x="Diameter")
   record.plot_analog()
   record.plot_digital()

For a guided version with more realistic instrument settings, see the
`complete workflow tutorial <https://martinpdes.github.io/FlowCyPy/gallery/tutorials/workflow_1.html>`_.

How the model fits together
---------------------------

.. image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/architecture.png
   :alt: FlowCyPy simulation architecture
   :align: center

The simulation follows the measurement chain:

``fluidics → scattering → detectors → analog electronics → digitizer → digital processing``

This separation makes it straightforward to compare populations, instrument
configurations and signal-processing choices independently.

Documentation and examples
---------------------------

* `Documentation <https://martinpdes.github.io/FlowCyPy/>`_ — getting started,
  model assumptions and API reference.
* `Examples <https://martinpdes.github.io/FlowCyPy/gallery/index.html>`_ —
  tutorials, validation notebooks and parameter studies.
* `Source code <https://github.com/MartinPdeS/FlowCyPy>`_ — issues,
  discussions and contributions.

Development
-----------

.. code-block:: console

   $ python -m pip install -e ".[testing]"
   $ python -m pytest

Build the documentation locally with ``cd docs && make html``. Contributions,
bug reports and ideas are welcome through GitHub Issues and pull requests.

License
-------

FlowCyPy is released under the MIT License. See `LICENSE <https://github.com/MartinPdeS/FlowCyPy/blob/master/LICENSE>`_.

.. |logo| image:: https://github.com/MartinPdeS/FlowCyPy/raw/master/docs/images/logo.png
   :alt: FlowCyPy
   :width: 280px
.. |python| image:: https://img.shields.io/pypi/pyversions/FlowCyPy.svg
   :alt: Python versions
   :target: https://pypi.org/project/FlowCyPy/
.. |pypi| image:: https://img.shields.io/pypi/v/FlowCyPy.svg
   :alt: PyPI
   :target: https://pypi.org/project/FlowCyPy/
.. |docs| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_documentation.yml/badge.svg
   :alt: Documentation status
   :target: https://martinpdes.github.io/FlowCyPy/
.. |ci| image:: https://github.com/martinpdes/flowcypy/actions/workflows/deploy_coverage.yml/badge.svg
   :alt: Test status
.. |license| image:: https://img.shields.io/github/license/MartinPdeS/FlowCyPy.svg
   :alt: MIT License
   :target: https://github.com/MartinPdeS/FlowCyPy/blob/master/LICENSE
