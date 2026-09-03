Quick start
===========

Option A — the Python API (recommended)
---------------------------------------

.. code-block:: python

   import geoaquacrop_simulate as simulate

   config = simulate.example_config()
   config.update({
       'weather_path': '/path/to/preprocess/processed',
       'soil_path':    '/path/to/preprocess/processed',
       'pheno_path':   '/path/to/preprocess/processed',
       'spam_path':    '/path/to/preprocess/processed',
       'start_date':   '2011/01/01',
       'end_date':     '2013/12/31',
       'crop':         'Wheat_winter',
       'irrigation':   'rainfed',
       'output_dir':   'outputs',
   })
   summary_file, daily_file = simulate.run(config)

If the whole toolchain is installed, the same call is available through the
unified façade, and the two are interchangeable:

.. code-block:: python

   import geoaquacrop as gac

   summary_file, daily_file = gac.simulate.run(config)

Option B — edit and run the script
----------------------------------

.. code-block:: python

   from geoaquacrop_simulate.run_aquacrop import main

   summary_file, daily_file = main()

This is also the way to run from an IDE console (Spyder, Jupyter): importing
``main`` establishes the package context that the module's relative imports
need.

For finer control, drive the pieces directly:

.. code-block:: python

   import logging
   from geoaquacrop_simulate.config import SimulationConfig
   from geoaquacrop_simulate.processor import ParallelProcessor

   sim_config = SimulationConfig(config_dict)
   validated = sim_config.validate_all_inputs()
   coords_df = validated['coords']

   processor = ParallelProcessor(sim_config.config, validated,
                                 logging.getLogger('geoaquacrop'))
   summary_results, daily_results = processor.run_parallel(coords_df)
   processor.save_results(summary_results, daily_results,
                          sim_config.config['output_dir'])

Required input files
--------------------

All must share a common grid, CRS (EPSG:4326) and spatial extent — which is
what geoaquacrop_preproc guarantees.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Contents
   * - ``MinTemp<years>.nc``, ``MaxTemp<years>.nc``
     - Daily minimum and maximum air temperature [°C]
   * - ``Precipitation<years>.nc``
     - Daily precipitation [mm day⁻¹]
   * - ``ReferenceET<years>.nc``
     - Daily FAO-56 Penman-Monteith reference ET₀ [mm day⁻¹]
   * - ``soil_<depth>.tif``
     - Clay, sand, silt and organic matter per depth layer [%]
   * - ``<crop>_<ir|rf>_planting_day.tif``
     - Planting day of year
   * - ``<crop>_<ir|rf>_growing_season_length.tif``
     - Growing season length [days]
   * - ``spam<year>_physical_area.nc``
     - Crop physical area [ha] — defines which cells are simulated

To print the full requirements from Python:

.. code-block:: python

   from geoaquacrop_simulate.run_aquacrop import print_input_requirements
   print_input_requirements()

Output files
------------

Written to ``<output_dir>/``:

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - File
     - Contents
   * - ``summary_results_<timestamp>.pkl``
     - One seasonal summary row per cell per season: yields, irrigation,
       harvest date, plus derived metrics
   * - ``daily_results_<timestamp>.pkl``
     - Daily water-balance and crop-growth series per cell
   * - ``logs/aquacrop_simulation_<timestamp>.log``
     - Run log, including any per-cell failures
   * - ``yield_scaled.nc`` / ``yield_calibrated.nc``
     - Corrected yield grids, if a correction was configured

Supported crop types
--------------------

Barley, Cassava, Cotton, Dry Bean, Maize, Paddy Rice (seasons 1 & 2), Potato,
Sorghum, Soybean, Sugar Beet, Sugar Cane, Sunflower, Wheat (summer & winter) —
matching the crop calendar and crop area datasets from geoaquacrop_preproc.
