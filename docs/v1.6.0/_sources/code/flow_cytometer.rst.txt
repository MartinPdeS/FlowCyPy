.. _cytometer:

Flow cytometer
==============

Predefined systems return a configured :class:`~FlowCyPy.flow_cytometer.FlowCytometer`.
After adding a sample, run all configured stages with the instrument's current settings.

.. code-block:: python

   result = instrument.run(run_time=1 * ureg.millisecond, random_state=42)

To compare trigger settings on the same particle events and noise, acquire once
and process the returned record with each digital processing configuration:

.. code-block:: python

   acquisition = instrument.acquire(run_time=1 * ureg.millisecond, random_state=42)
   low = acquisition.process(digital_processing=low_threshold_processing)
   high = acquisition.process(digital_processing=high_threshold_processing)

Each result has its own triggered segments and peaks. The first processing call
applies the analog circuits, and subsequent calls reuse the filtered waveform.

Migrating existing scripts
--------------------------

Replace ``Workflow.from_components(...)`` with ``FlowCytometer(...)`` using the
same component keywords. For scripts using the flat ``Workflow(...)``
constructor, start with a named system or follow
:doc:`/gallery/tutorials/assemble_a_flow_cytometer` to build each component.
Edit components directly before the next acquisition. Pass a seed as
``random_state=42`` when calling ``run`` or ``acquire``.

.. autoclass:: FlowCyPy.flow_cytometer.FlowCytometer
   :members:
   :show-inheritance:
