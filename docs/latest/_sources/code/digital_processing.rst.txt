.. _digital_processing:

Digital processing
==================

The :mod:`FlowCyPy.digital_processing` package defines the digital analysis stage applied to sampled detector traces.

It is responsible for isolating candidate events from continuous signals and extracting numerical features from each detected segment.

In a typical workflow, the digitized waveforms are first segmented by a discriminator and then summarized by a peak locator.

The typical workflow is:

1. define a discriminator to extract relevant signal segments
2. define a peak locator to compute event features within each segment
3. combine both into a :class:`FlowCyPy.digital_processing.DigitalProcessing` object

This configuration is then passed to the cytometer processing pipeline to transform raw sampled traces into event level measurements.

Digital processing configuration
--------------------------------

The :class:`FlowCyPy.digital_processing.DigitalProcessing` class groups the discriminator and peak extraction algorithm into a single processing configuration.

.. autoclass:: FlowCyPy.digital_processing.DigitalProcessing
   :members:
   :show-inheritance:

Discriminators
--------------

Discriminators are responsible for selecting relevant signal segments from continuous detector traces.

They define the criteria used to initiate and terminate event windows, typically through threshold crossings, buffered extraction, or dual threshold logic.

These classes isolate candidate particle events prior to feature extraction.

Fixed window
++++++++++++

The fixed window discriminator extracts segments using a fixed length window around each threshold crossing or trigger condition.

It is useful when a constant event support is desired for all detected segments.

.. autoclass:: FlowCyPy.digital_processing.discriminator.FixedWindow
   :members:
   :show-inheritance:

Dynamic window
++++++++++++++

The dynamic window discriminator defines segment boundaries from the signal itself.

It supports threshold based extraction with configurable pre and post buffering and is useful when event duration varies across the dataset.

.. autoclass:: FlowCyPy.digital_processing.discriminator.DynamicWindow
   :members:
   :show-inheritance:

Double threshold
++++++++++++++++

The double threshold discriminator uses separate start and stop criteria.

This is useful when more stable event opening and closing behavior is needed, especially in noisy traces or when hysteresis is desirable.

.. autoclass:: FlowCyPy.digital_processing.discriminator.DoubleThreshold
   :members:
   :show-inheritance:

Peak locators
-------------

Peak locators compute numerical descriptors from each segmented event.

Typical outputs include peak position, peak height, width, area, or other summary metrics derived from the extracted waveform support.

Different algorithms can be used depending on whether the goal is global maximum extraction, local peak detection, or more specialized pulse analysis.

Global peak locator
+++++++++++++++++++

The global peak locator identifies the dominant peak within each event segment and computes summary features from that support.

.. autoclass:: FlowCyPy.digital_processing.peak_locator.GlobalPeakLocator
   :members:
   :show-inheritance:

Sliding window peak locator
+++++++++++++++++++++++++++

The sliding window peak locator searches for peaks using a moving support window.

It is useful when feature extraction should be tied to localized signal structure rather than the full event segment.

.. autoclass:: FlowCyPy.digital_processing.peak_locator.SlidingWindowPeakLocator
   :members:
   :show-inheritance:

Example
-------

The example below shows a typical digital processing configuration using a fixed window discriminator and a global peak locator.

.. code-block:: python

   from FlowCyPy.digital_processing import (
       DigitalProcessing,
       peak_locator,
       discriminator,
   )

   triggering = discriminator.FixedWindow(
       trigger_channel="side",
       threshold="4sigma",
       pre_buffer=40,
       post_buffer=40,
       max_triggers=-1,
   )

   peak_algorithm = peak_locator.GlobalPeakLocator()

   digital_processing = DigitalProcessing(
       discriminator=triggering,
       peak_algorithm=peak_algorithm,
   )
