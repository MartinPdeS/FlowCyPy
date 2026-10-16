Troubleshooting
===============

Installation and imports
------------------------

Use the same Python interpreter for installation and execution::

    python -m pip install --upgrade FlowCyPy
    python -c "import FlowCyPy; print(FlowCyPy.__version__)"

A missing native module often means that no compatible wheel was installed or
a source build did not finish. Confirm your Python version and platform before
changing the simulation. Source builds need the repository's compiler and native
library dependencies.

Plots on a server
-----------------

Use ``MPLBACKEND=Agg`` for Matplotlib on a headless machine. Save figures to files
when no interactive display is available.

Units and signal interpretation
-------------------------------

Supply dimensional inputs with ``FlowCyPy.units.ureg``. Inspect particle arrivals
and analog detector signals before adjusting triggering or classification.
Clipping, saturation, noise and thresholds can change observed event counts;
compare stages of the tutorial workflow rather than only its final plots.
