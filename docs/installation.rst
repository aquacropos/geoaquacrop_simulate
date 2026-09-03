Installation
============

Prerequisites
-------------

* `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ or
  `Anaconda <https://www.anaconda.com/>`_
* Python 3.11 or newer
* Input datasets produced by
  :doc:`geoaquacrop_preproc <preproc:index>`

Install
-------

1. **Clone the repository:**

   .. code-block:: bash

      git clone https://github.com/<your-org>/geoaquacrop_simulate-dev
      cd geoaquacrop_simulate-dev

2. **Create and activate the conda environment:**

   .. code-block:: bash

      conda create -n geoaquacrop python=3.11
      conda activate geoaquacrop

3. **Install the package (editable, for development):**

   .. code-block:: bash

      python -m pip install -e .

   Optional extras:

   .. code-block:: bash

      python -m pip install -e ".[dev]"        # pytest, pytest-cov
      python -m pip install -e ".[correction]" # geopandas, matplotlib

Verify
------

.. code-block:: bash

   python -c "import geoaquacrop_simulate; print(geoaquacrop_simulate.__file__)"

The path printed should point inside your cloned ``src/geoaquacrop_simulate``
directory.

.. note::

   Always launch through the installed package rather than by running a file
   inside ``src/geoaquacrop_simulate`` directly. Executing a module as a script
   gives it no package context, so its relative imports (``from .config import
   ...``) fail with *"attempted relative import with no known parent
   package"*. Use ``python -m geoaquacrop_simulate.run_aquacrop``, the
   ``geoaquacrop_simulate`` console command, or import ``main`` in a notebook or
   IDE console.

Running the tests
-----------------

.. code-block:: bash

   python -m pytest -q
