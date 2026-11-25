.. _cytometer:

Flow cytometer
==============

A configured :class:`~FlowCyPy.workflow.Workflow` builds the instrument on its
first acquisition and reuses it on subsequent runs. To run all configured
stages, call:

.. code-block:: python

   result = workflow.run(run_time=1 * ureg.millisecond, random_state=42)

To compare trigger settings on the same particle events and noise, acquire once
and process the returned record with each digital processing configuration:

.. code-block:: python

   acquisition = workflow.acquire(run_time=1 * ureg.millisecond, random_state=42)
   low = acquisition.process(digital_processing=low_threshold_processing)
   high = acquisition.process(digital_processing=high_threshold_processing)

Each result has its own triggered segments and peaks. The first processing call
applies the analog circuits, and subsequent calls reuse the filtered waveform.
Call ``workflow.initialize()`` to rebuild the instrument after editing settings.

For direct control over the individual subsystems, use
:class:`~FlowCyPy.flow_cytometer.FlowCytometer`.

.. autoclass:: FlowCyPy.flow_cytometer.FlowCytometer
   :members:
   :show-inheritance:
