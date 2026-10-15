Getting started
===============

Install and verify
------------------

.. code-block:: console

   $ python -m pip install FlowCyPy
   $ python -c "import FlowCyPy; print(FlowCyPy.__version__)"

Configure the flow cell
-----------------------

Use explicit units for dimensional parameters. A minimal flow-cell configuration
is a useful first check before adding populations, optics and electronics.

.. code-block:: python

   from FlowCyPy.fluidics import FlowCell, SampleFlowRate, SheathFlowRate
   from FlowCyPy.units import ureg

   flow_cell = FlowCell(
       sample_volume_flow=SampleFlowRate.MEDIUM.value,
       sheath_volume_flow=SheathFlowRate.MEDIUM.value,
       width=400 * ureg.micrometer,
       height=150 * ureg.micrometer,
   )
   print(flow_cell)

For a complete acquisition, follow :doc:`gallery/tutorials/workflow_1`.
That tutorial adds particle populations, a laser source, detectors, electronics,
triggering and classification. See :doc:`guide` to choose the relevant stage.

If installation or rendering fails, see :doc:`troubleshooting`.
