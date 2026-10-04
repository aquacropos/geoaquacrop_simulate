geoaquacrop_simulate
====================

**geoaquacrop_simulate** runs `FAO AquaCrop <https://www.fao.org/aquacrop>`_ over
large regions in gridded format. It takes the harmonised input datasets produced
by :doc:`geoaquacrop_preproc <preproc:index>`, runs an independent AquaCrop
simulation for every grid cell in parallel, and writes per-cell seasonal and
daily results.

It is the middle stage of the GeoAquaCrop toolchain:

.. code-block:: text

   geoaquacrop_preprocess  ->  geoaquacrop_simulate  ->  geoaquacrop_visualize
   (download & harmonise)   (simulate & correct)        (explore results)

What it does
------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Stage
     - Description
   * - Input validation
     - Checks that climate, soil, crop calendar and crop area files exist,
       share a grid, and cover the requested period; derives the list of
       simulated cells from the crop area mask.
   * - Per-cell simulation
     - Builds an AquaCrop ``Soil``, ``Crop`` and weather series for each cell,
       adjusts crop phenology to the local growing season, and runs the model
       to termination across all seasons.
   * - Parallel execution
     - Distributes cells over worker processes with a progress bar; failures
       are logged per cell without stopping the run.
   * - Derived outputs
     - Adds seasonal water-balance metrics (water productivity, rainfall use
       efficiency, production, season length) via a pluggable enricher
       registry.
   * - Yield correction
     - Optionally bias-corrects or calibrates modelled yields against an
       observational reference, per year, at the reference's native support.

Outputs are pickled ``pandas`` frames (one seasonal summary row per cell per
season, plus daily water-balance and crop-growth series), ready for
`geoaquacrop_visualizer <https://sehohosseini.github.io/geoaquacrop_visualize/>`_.

.. toctree::
   :caption: Getting started
   :maxdepth: 1

   installation
   quickstart

.. toctree::
   :caption: User guide
   :maxdepth: 1

   configuration
   outputs
   corrections

.. toctree::
   :caption: API reference
   :maxdepth: 1

   api/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
