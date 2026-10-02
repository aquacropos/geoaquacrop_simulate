Outputs
=======

Simulation results are written as pickled lists of :class:`pandas.DataFrame`
objects, one entry per simulated cell.

Seasonal summary
----------------

``summary_results_<timestamp>.pkl`` holds one row per cell **per season**. Cell
coordinates are carried in ``x`` and ``y``.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Column
     - Description
   * - ``Season``
     - Zero-based season index within the simulation period
   * - ``Harvest Date (YYYY/MM/DD)``
     - Realised harvest date; its year is used to date each season
   * - ``Dry yield (tonne/ha)``
     - Dry-matter yield
   * - ``Fresh yield (tonne/ha)``
     - Fresh-weight yield
   * - ``Yield potential (tonne/ha)``
     - Yield without water stress
   * - ``Seasonal irrigation (mm)``
     - Applied irrigation over the season

Derived metrics
---------------

:mod:`geoaquacrop_simulate.summary_enrichers` adds further columns after each run:
seasonal precipitation and evapotranspiration, total water input, production,
season length, water productivity (ET-based), rainfall use efficiency and
irrigation water productivity.

The registry is pluggable — decorate a function with
:func:`~geoaquacrop_simulate.summary_enrichers.enricher` and it is applied
automatically:

.. code-block:: python

   from geoaquacrop_simulate.summary_enrichers import enricher

   @enricher
   def add_my_metric(summary, context):
       summary['My metric'] = summary['Dry yield (tonne/ha)'] * 2
       return summary

Daily results
-------------

``daily_results_<timestamp>.pkl`` holds the daily water balance and crop growth
per cell, including canopy cover, biomass, deep percolation, runoff,
transpiration, soil evaporation and profile water content. These feed the
time-series panels of
`geoaquacrop_visualize <https://geoaquacrop-visualize.readthedocs.io/en/latest/>`_.

Loading results
---------------

.. code-block:: python

   import pickle
   import pandas as pd

   with open('outputs/summary_results_20260807_120000.pkl', 'rb') as f:
       summary_results = pickle.load(f)

   df = pd.concat(summary_results, ignore_index=True)
   print(df.groupby('Season')['Dry yield (tonne/ha)'].mean())
