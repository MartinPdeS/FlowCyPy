.. _triggering_systems:

Triggering Systems
==================

Triggering systems are responsible for selecting relevant signal segments in flow cytometry.
They define the criteria by which signal acquisition is initiated or segmented, such as threshold
crossings, time windows, or double-threshold logic.

These classes are typically used in the digital signal processing pipeline to isolate particle events
from continuous analog traces. Each triggering system supports customization of buffer size, thresholds,
and detector inputs.

Available Triggering Systems
----------------------------

.. autoclass:: FlowCyPy.triggering_system.FixedWindow
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

   This triggering strategy uses a fixed-size window around predefined event times or positions.
   It is best suited for idealized or pre-segmented data where uniform windowing is acceptable.

.. autoclass:: FlowCyPy.triggering_system.DynamicWindow
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

   A dynamic threshold-based triggering system that extracts segments based on real-time signal
   amplitude crossings. It supports pre- and post-buffering, maximum trigger count, and a configurable
   detector channel.

.. autoclass:: FlowCyPy.triggering_system.DoubleThreshold
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

   A more advanced system using both a lower and upper threshold. Events are only captured if
   the signal first rises above a lower bound and then exceeds a higher one — useful for noise
   rejection and pulse validation.

Usage Notes
-----------

Triggering systems are passed to the `SignalProcessing` class during cytometer configuration:

.. code-block:: python

   from FlowCyPy.triggering_system import DynamicWindow

   triggering = DynamicWindow(
       trigger_detector_name='forward',
       threshold=10 * units.microvolt,
       pre_buffer=20,
       post_buffer=20
   )

   signal_processing = SignalProcessing(
       digitizer=...,
       analog_processing=...,
       triggering_system=triggering,
       peak_algorithm=...
   )
