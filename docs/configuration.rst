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
   * - ``cell_mask``
     - ``None``
     - NetCDF selecting the cells to simulate; see `Cell mask`_
   * - ``spam_file``
     - ``None``
     - SPAM physical-area NetCDF to use instead of the one picked from
       ``spam_path`` by the midpoint of the simulation period

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
     - Region reference (GeoJSON) with ``region_id`` and ``yield_<year>``
       fields, written by :mod:`~geoaquacrop_simulate.build_reference`
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

CO2 concentration
-----------------

AquaCrop scales crop water productivity with atmospheric CO2. Each run uses
annual Mauna Loa observations up to and including 2025 and an SSP pathway after
it. The pathway defaults to SSP2-4.5; set ``co2_scenario`` to match the scenario
of your climate data:

.. code-block:: python

   run(..., co2_scenario='ssp585')

A run that extends past 2025 without ``co2_scenario`` warns, since the default
pathway is unlikely to suit every scenario. Runs ending in 2025 or earlier use
observations only, so the setting has no effect on them.

Accepted values are the pathways AquaCrop ships: ``ssp119``, ``ssp126``,
``ssp245``, ``ssp370``, ``ssp434``, ``ssp460``, ``ssp534os`` and ``ssp585``
(``'SSP2-4.5'`` style is also accepted).

Irrigation management
---------------------

Irrigated runs refill the root zone whenever soil water falls below 80% of
total available water, in every growth stage but late season (AquaCrop
``irrigation_method=1``, ``SMT=[80, 80, 80, 0]``). ``irrigation_management``
changes this for every cell. Its entries are AquaCrop
:class:`IrrigationManagement` settings, merged over the default:

.. code-block:: python

   run(..., irrigation='irrigated',
       irrigation_management={'SMT': [70, 70, 70, 0], 'MaxIrrSeason': 400})

A common change is the maximum depth applied in one day, ``MaxIrr`` (mm;
AquaCrop's default is 25). Varying it gives a sweep of supply limits:

.. code-block:: python

   for depth in range(1, 11):
       run(..., irrigation='irrigated',
           irrigation_management={'MaxIrr': depth},
           output_dir=f'outputs/irr{depth:02d}mm')

Allowed keys: ``irrigation_method`` (1-5), ``SMT``, ``MaxIrr``,
``MaxIrrSeason``, ``IrrInterval``, ``NetIrrSMT``, ``Schedule``, ``depth``,
``WetSurf`` and ``AppEff``. Unknown keys raise an error, as does setting it on
a rainfed run.

Cell mask
---------

By default every cell of the weather grid inside the domain is simulated.
``cell_mask`` restricts the run to a subset, typically cells with enough area
of the crop:

.. code-block:: python

   run(..., cell_mask='processed/rainfed_rice_mask.nc')

The file is a NetCDF grid with ``y``/``x`` coordinates. Cells where its
variable is non-zero are simulated; the variable is ``mask`` if present,
otherwise the file's only data variable. Values are looked up at the nearest
mask cell, so the mask need not be on exactly the same grid. Cell ids in the
outputs are those of an unmasked run, so masked and unmasked results can be
joined on ``cell_id``. A mask that selects no cell raises an error.

SPAM crop area
--------------

Crop area per cell, used for ``production_tonnes``, comes from
``spam{2010|2020}_physical_area.nc`` in ``spam_path``, the reference year
nearest the middle of the simulation period. ``spam_file`` names the file
instead, e.g. to use SPAM 2020 for a historical baseline:

.. code-block:: python

   run(..., spam_file='processed/spam2020_physical_area.nc')

Adaptive planting
-----------------

``adaptive_planting`` lets AquaCrop choose the sowing date each season instead
of using the crop calendar date. The calendar date opens the sowing window;
AquaCrop sows on the first day that meets the rule, or at the end of the window
if none does. The rule applies to every cell, so the date it fires on varies by
cell and year.

.. code-block:: python

   run(..., adaptive_planting={
       'PlantTempThr':  12,   # mean daily temperature threshold, °C
       'PlantTWindow':  5,    # consecutive days at or above it
       'PlantMaxDelay': 60,   # longest delay after the calendar date, days
   })

Keys are AquaCrop :class:`Crop` attributes: ``PlantTempThr``,
``PlantTWindow``, ``PlantRainThr``, ``PlantRainWindow``, ``PlantSMThr``,
``PlantMaxDelay`` and ``PlantTrigger``, which is set to ``True`` for you.
Unknown keys raise an error. The date used each season is reported in the
``planting_date`` output column (see :doc:`outputs`).

Logging
-------

:func:`~geoaquacrop_simulate.run_aquacrop.setup_logging` writes a timestamped log to
``<output_dir>/logs/``. Console output is off by default — uncomment the
``StreamHandler`` in that function to see progress messages in the terminal as
well as the file.
