.. _opto_electronics:

Opto-electronics
================

The :mod:`FlowCyPy.opto_electronics` package defines the optical and electronic acquisition chain of the simulation.

It describes how particles are illuminated, how scattered light is collected by detectors, how the resulting photocurrent is amplified and filtered, and how analog signals are digitized before digital signal processing.

Together, these components determine the temporal shape, amplitude, bandwidth, and noise properties of the recorded detector traces.

The typical workflow is:

1. define a light source
2. configure one or more detectors
3. specify the analog front-end, including amplification and optional filtering
4. define the digitizer settings
5. combine everything into an :class:`FlowCyPy.opto_electronics.OptoElectronics` object

This configuration is then passed to the cytometer to simulate the acquisition chain from optical excitation to sampled digital signals.

Opto-electronic configuration
-----------------------------

The :class:`FlowCyPy.opto_electronics.OptoElectronics` class groups the source, detectors, amplifier, digitizer, and optional analog processing stages into a single configuration object.

.. autoclass:: FlowCyPy.opto_electronics.OptoElectronics
   :members:
   :show-inheritance:

Light sources
-------------

Source classes define the spatial profile and optical properties of the illuminating beam.

They specify quantities such as wavelength, optical power, beam waist, and relative intensity noise, which together determine the incident optical field seen by particles traversing the interrogation region.

Gaussian source
+++++++++++++++

The Gaussian source models a focused beam with Gaussian transverse intensity profiles.

It is suitable for most tightly focused flow cytometry illumination geometries.

.. autoclass:: FlowCyPy.opto_electronics.source.Gaussian
   :members:
   :show-inheritance:

Flat-top source
+++++++++++++++

The flat-top source models an illumination profile with a more uniform intensity over the beam cross-section.

It is useful when approximating excitation geometries that are intentionally homogenized across the interrogation region.

.. autoclass:: FlowCyPy.opto_electronics.source.FlatTop
   :members:
   :show-inheritance:

Detectors
---------

Detector classes describe how scattered light is collected and converted into electrical current.

A detector typically defines its angular position, numerical aperture, and responsivity.

These parameters determine the optical collection efficiency and the conversion from collected optical power to photocurrent.

.. autoclass:: FlowCyPy.opto_electronics.detector.Detector
   :members:
   :show-inheritance:

Amplification
-------------

Amplifier classes model the analog front-end that converts detector photocurrent into voltage.

In FlowCyPy, this stage is typically represented by a transimpedance amplifier, which applies a current-to-voltage gain, a finite bandwidth, and optional electronic noise contributions.

This stage strongly influences pulse amplitude, temporal smoothing, and baseline noise before digitization.

.. autoclass:: FlowCyPy.opto_electronics.amplifier.Amplifier
   :members:
   :show-inheritance:

Digitization
------------

The digitizer converts analog voltage signals into sampled digital traces.

Its configuration controls the sampling rate, quantization depth, and channel range strategy.

These settings determine the temporal resolution, integer encoding, clipping behavior, and effective dynamic range of the recorded waveforms.

.. autoclass:: FlowCyPy.opto_electronics.digitizer.Digitizer
   :members:
   :show-inheritance:

Analog processing circuits
--------------------------

Analog processing circuits represent signal conditioning stages applied before digitization.

Typical examples include baseline restoration, low-pass filtering, and other bandwidth-limiting or shaping operations that affect the continuous detector signal.

.. automodule:: FlowCyPy.opto_electronics.circuits
   :members:
   :undoc-members:
   :show-inheritance:

Example
-------

The example below shows a typical opto-electronic configuration composed of a Gaussian source, two detectors, a transimpedance amplifier, optional analog filtering, and a digitizer.

.. code-block:: python

   from FlowCyPy.units import ureg
   from FlowCyPy.opto_electronics import (
       Detector,
       Digitizer,
       OptoElectronics,
       Amplifier,
       source,
       circuits,
   )

   analog_processing = [
       circuits.BaselineRestorationServo(time_constant=100 * ureg.microsecond),
       circuits.BesselLowPass(cutoff_frequency=2 * ureg.megahertz, order=4, gain=2),
   ]

   excitation_source = source.Gaussian(
       waist_z=10e-6 * ureg.meter,
       waist_y=60e-6 * ureg.meter,
       wavelength=405 * ureg.nanometer,
       optical_power=200 * ureg.milliwatt,
       rin=-140 * ureg.dB_per_Hz,
       bandwidth=10 * ureg.megahertz,
   )

   detectors = [
       Detector(
           name="side",
           phi_angle=90 * ureg.degree,
           numerical_aperture=1.1,
           responsivity=1 * ureg.ampere / ureg.watt,
       ),
       Detector(
           name="forward",
           phi_angle=0 * ureg.degree,
           numerical_aperture=0.3,
           cache_numerical_aperture=0.1,
           responsivity=1 * ureg.ampere / ureg.watt,
       ),
   ]

   amplifier = Amplifier(
       gain=10 * ureg.volt / ureg.ampere,
       bandwidth=10 * ureg.megahertz,
       voltage_noise_density=0.0 * ureg.nanovolt / ureg.sqrt_hertz,
       current_noise_density=0.0 * ureg.femtoampere / ureg.sqrt_hertz,
   )

   digitizer = Digitizer(
       sampling_rate=60 * ureg.megahertz,
       bit_depth=14,
       use_auto_range=True,
       channel_range_mode="shared",
   )

   opto_electronics = OptoElectronics(
       digitizer=digitizer,
       detectors=detectors,
       source=excitation_source,
       amplifier=amplifier,
       analog_processing=analog_processing,
   )
