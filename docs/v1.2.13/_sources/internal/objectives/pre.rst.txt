Pre-Tasks
~~~~~~~~~

1. **Environment Check**:

   - Verify that **FlowCyPy** is installed correctly by running the test suite:

     .. code-block:: bash

        python -m pytest .

     If tests fail, identify the issues, debug, and ensure all functionalities are working.

   - Run a basic example script from the `examples` folder:

     .. code-block:: bash

        cd docs/examples/tutorials
        python workflow.py

     Confirm the script executes without errors and produces expected visualizations.

2. **Familiarization**:

   - Read through the `scatterer.py`, `source.py`, and `detector.py` files to understand their roles in **FlowCyPy**.
   - Modify a simple example to:

     - Change detector noise levels and observe the signal differences.
     - Adjust laser parameters (e.g., wavelength or power) and analyze the effect on scatter signals.

   - Explore the **Examples** section in the documentation and try running at least one example.
