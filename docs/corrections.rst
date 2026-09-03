Yield correction
================

An optional stage that brings modelled yields into line with an observational
reference. It is deliberately rough: a plausibility adjustment, not formal
parameter estimation or statistical downscaling.

.. list-table::
   :header-rows: 1
   :widths: 22 30 24 24

   * - Mode
     - What it changes
     - Where it acts
     - When
   * - ``scale`` (``global``)
     - One multiplicative factor on yield
     - Whole domain
     - Per year
   * - ``scale`` (``local``)
     - One multiplicative factor per county
     - County resolution
     - Per year
   * - ``calibrate``
     - One crop growth parameter (``CCx`` or ``WP``)
     - Whole domain, via the model
     - One value across all years

Three fixed design rules
------------------------

**1. No temporal aggregation.** Every quantity carries a year. Simulated
seasons are never averaged together: factors are fitted and applied per year,
the reference is per year, and all output keeps the year dimension. The only
cross-year quantity is the calibrated crop parameter itself, because a crop
parameter is not a per-year property — and even then its objective runs over
every (year, county) pair rather than a time-averaged field.

**2. The model is aggregated to the reference's native support.** The reference
is a set of county polygons with one yield per county per year; it is never
rasterised. Simulation cells are assigned to the county containing their centre
and combined as an area-weighted mean, with weights proportional to
``cos(latitude)``. Comparison, factors, residuals and the calibration objective
all live at county scale. The fine-scale model is reduced to the scale of the
observations, rather than county statistics being spread onto a grid whose
apparent resolution the data does not support.

**3. Corrected output stays on the simulation grid.** Only the *correction* is
derived at county scale; it is applied back to the full-resolution field, so the
written NetCDF is ``(year, y, x)`` at the model's own resolution. A county-level
comparison table is written alongside as CSV.

Building the reference
----------------------

``reference/build_reference.py`` turns county boundaries, a USDA NASS county
yield table and a region boundary into the reference file:

.. code-block:: bash

   cd reference
   python build_reference.py

It writes one GeoJSON feature per county with a ``yield_<year>`` field per year,
converting USDA bushels/acre at 15.5 % moisture to dry-matter t/ha. No
rasterisation happens at any stage, so the reference carries exactly the
information USDA published: one number per county per year.

Scaling
-------

Pure post-processing; no re-simulation.

*Global* fits one factor per year across the whole domain, so all modelled
spatial pattern within a year is preserved and only the level changes. Because
the factor is per year, it follows interannual variation in the reference.

*Local* fits one factor per year per county. Within a county the model's
relative pattern survives untouched; the county's level is pinned to the
reference. Residuals are then **exactly zero by construction** — the factor is
constant within a county and the aggregation is a linear weighted mean, so the
county mean of the corrected field equals the reference identically. A reported
RMSE of zero is arithmetic, not skill.

Reusing a finished run:

.. code-block:: python

   'correction': {
       'method': 'scale',
       'reference_path': 'reference/high_plains_maize_reference.geojson',
       'scale_mode': 'local',
       'reuse_results': 'latest',
   }

With ``reuse_results`` set, :func:`~geoaquacrop_simulate.correction.should_reuse`
returns ``True`` and the driver skips simulation entirely, scaling the saved
summary in seconds.

Calibration
-----------

Varies one physical crop parameter and lets the model respond.

.. list-table::
   :header-rows: 1
   :widths: 16 14 34 36

   * - ``lever``
     - Parameter
     - Meaning
     - Yield response
   * - ``canopy``
     - ``CCx``
     - Maximum canopy cover
     - Smooth, monotonic, concave
   * - ``biomass``
     - ``WP``
     - Normalised water productivity
     - Monotonic, near-linear

Canopy growth *rate* (``CGC``) is deliberately not offered: measured yield
sensitivity to it is essentially nil once canopy reaches ``CCx`` before season
end. Harvest index is excluded as the least physically defensible lever.

Calibration runs in two phases so the expensive full-grid simulation happens
exactly once:

1. :func:`~geoaquacrop_simulate.correction.calibration_override` runs a
   golden-section search (~15–20 evaluations) on a subsample of cells, scoring
   the area-weighted sum of squared differences over every (year, county) pair.
2. The fitted value is injected as ``crop_param_override`` and the full grid is
   simulated once with it applied.
   :func:`~geoaquacrop_simulate.correction.run_correction` then reports on that run
   without re-searching.

Wiring it into the driver:

.. code-block:: python

   from geoaquacrop_simulate.correction import calibration_override

   sim_config.config.update(
       calibration_override(sim_config.config, ParallelProcessor,
                            validated_inputs, coords_df, logger))

Interpreting the results
------------------------

``compare_corrections.py`` writes per-year maps, county-polygon difference
maps, a domain-mean time series and a statistics table:

.. code-block:: python

   from geoaquacrop_simulate.compare_corrections import main

   main([
       "--reference", "reference/high_plains_maize_reference.geojson",
       "--calibrated", "outputs/yield_calibrated.nc",
       "--scaled", "outputs/yield_scaled.nc",
       "--summary", "outputs/summary_results_20260807_120000.pkl",
       "--out-dir", "outputs/comparison",
   ])

Questions worth more than "which RMSE is lowest":

* **Does the run track interannual variation?** Per-year scaling follows the
  reference by construction; calibration reproduces it only if the model's own
  weather response does.
* **Does the calibrated run reproduce the spatial pattern**, or only the level?
  Pattern agreement under a single global parameter is a genuine result.
* **Are residuals spatially structured?** Structure implies a missing process
  that no single lever or global factor will fix.
* **Did the parameter hit a bound?** A ``CCx`` pressed against 0.30 or 0.99
  means the lever has saturated.
* **Do per-year biases have opposite signs?** Then one parameter cannot satisfy
  all years — a structural limit, not a tuning failure.

.. warning::

   USDA NASS county yields blend irrigated and rainfed production. If the run is
   configured ``irrigation: 'rainfed'``, modelled yields will sit below the
   reference in heavily irrigated counties for reasons unrelated to ``CCx`` or
   ``WP``. Any correction absorbs that gap, flattering the fit statistics while
   attributing an irrigation signal to a growth parameter. For a cleaner test,
   restrict the reference to predominantly rainfed counties or run irrigated to
   match.

Checking the machinery
----------------------

``visual_check.py`` exercises the correction code on synthetic data where the
answer is known — useful after changing the correction modules, as distinct
from ``compare_corrections.py`` which inspects real results:

.. code-block:: python

   from geoaquacrop_simulate.visual_check import main
   main()
