Configuration reference
=======================

Every setting below is a keyword argument to
:func:`~geoaquacrop_simulate.run_aquacrop.run`; a dictionary can also be passed
as ``config=`` for programmatic use, and individual arguments then override it.
``data_path`` is a shorthand that fills all four input paths at once.
Internally the assembled settings are validated by
:class:`~geoaquacrop_simulate.config.SimulationConfig`. Validation checks that all
required keys are present and that the referenced files exist, share a grid and
cover the requested period; unknown keys are ignored, so optional blocks can be
added freely.

Simulation
----------

.. list-table::
   :header-rows: 1
   :widths: 26 18 56

   * - Parameter
     - Default
     - Description
   * - ``data_path``
     - *see note*
     - Folder holding the preprocessed inputs; fills the four paths below
   * - ``weather_path``
     - *required*
     - Directory holding the climate NetCDF files
   * - ``soil_path``
     - *required*
     - Directory holding the soil GeoTIFFs
   * - ``pheno_path``
     - *required*
     - Directory holding the crop calendar GeoTIFFs
   * - ``spam_path``
     - *required*
     - Directory holding the SPAM crop area NetCDF
   * - ``start_date``
     - *required*
     - First day of the simulation, ``'YYYY/MM/DD'``
   * - ``end_date``
     - *required*
     - Last day of the simulation, ``'YYYY/MM/DD'``
   * - ``crop``
     - ``'Maize'``
     - Crop name, case-sensitive (see :doc:`quickstart`)
   * - ``irrigation``
     - ``'rainfed'``
     - ``'rainfed'`` or ``'irrigated'``; selects the crop calendar and crop
       area layers
   * - ``initial_water_content``
     - field capacity
     - An AquaCrop :class:`InitialWaterContent` object
   * - ``output_dir``
     - ``'outputs'``
     - Where results and logs are written

Yield correction
----------------

Optional. Omit the block, or set ``method`` to ``None``, and the pipeline is
numerically untouched. See :doc:`corrections` for what each mode does.

.. code-block:: python

   'correction': {
       'method':        None,
       'reference_path': None,
       'value_col':     'Dry yield (tonne/ha)',
       'scale_mode':    'global',
       'lever':         'canopy',
       'bounds':         None,
       'search_sample':  200,
       'reuse_results':  None,
       'output_name':    None,
   }

.. list-table::
   :header-rows: 1
   :widths: 24 20 56

   * - Parameter
     - Default
     - Description
   * - ``method``
     - ``None``
     - ``None`` (off), ``'scale'`` (multiplicative bias correction) or
       ``'calibrate'`` (fit one crop parameter)
   * - ``reference_path``
     - ``None``
     - County reference (GeoJSON) with ``fips`` and ``yield_<year>`` fields,
       written by ``reference/build_reference.py``
   * - ``value_col``
     - ``'Dry yield (tonne/ha)'``
     - Summary column to correct; must match the reference's units
   * - ``scale_mode``
     - ``'global'``
     - ``'global'`` (one factor per year) or ``'local'`` (one factor per year
       per county)
   * - ``lever``
     - ``'canopy'``
     - Parameter varied when calibrating: ``'canopy'`` (``CCx``) or
       ``'biomass'`` (``WP``)
   * - ``bounds``
     - ``None``
     - ``(lo, hi)`` search bounds; defaults per lever
   * - ``search_sample``
     - ``200``
     - Cells subsampled for the calibration search (reproducible,
       ``random_state=0``)
   * - ``reuse_results``
     - ``None``
     - ``'latest'`` or a path to a saved ``summary_results_*.pkl`` — scales an
       existing run with no simulation. Scaling only
   * - ``output_name``
     - ``None``
     - Derived from the method (``yield_scaled.nc`` /
       ``yield_calibrated.nc``) so the two modes never overwrite each other

Crop parameter override
-----------------------

``crop_param_override`` is a dictionary of AquaCrop :class:`Crop` attributes
applied to every cell, e.g. ``{'CCx': 0.70}``. Calibration sets it
automatically; you can also set it by hand to run a sensitivity experiment.

Logging
-------

:func:`~geoaquacrop_simulate.run_aquacrop.setup_logging` writes a timestamped log to
``<output_dir>/logs/``. Console output is off by default — uncomment the
``StreamHandler`` in that function to see progress messages in the terminal as
well as the file.
