.. _amplifier:

Amplifier
=========

This module defines the analog signal amplification components used in flow cytometry simulations.
Amplifiers convert weak photo-currents (from photodetectors) into measurable voltages prior to digitization.

In FlowCyPy, the primary amplification model is the transimpedance amplifier (TIA), which applies
a configurable gain and bandwidth to the input signal. It also supports optional voltage and current
noise sources to simulate realistic analog front-end behavior.

Available Amplifier
-------------------

.. autoclass:: FlowCyPy.amplifier.TransimpedanceAmplifier
   :members:
   :undoc-members:
   :show-inheritance:

   A transimpedance amplifier (TIA) model that transforms photocurrent into voltage signals using
   a configurable gain, bandwidth, and optional noise sources. The TIA is applied to each detector
   channel and is responsible for setting the signal's final amplitude and frequency content before
   digitization.

Usage Example
-------------

.. code-block:: python

   from FlowCyPy.amplifier import TransimpedanceAmplifier
   import FlowCyPy.units as units

   amplifier = TransimpedanceAmplifier(
       gain=10 * units.volt / units.ampere,
       bandwidth=10 * units.megahertz,
       voltage_noise_density=0.1 * units.nanovolt / units.sqrt_hertz,
       current_noise_density=0.2 * units.femtoampere / units.sqrt_hertz
   )

   opto_electronics = OptoElectronics(
       detectors=[...],
       source=...,
       amplifier=amplifier
   )
