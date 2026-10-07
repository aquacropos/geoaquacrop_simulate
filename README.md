<p align="center">
  <img src="https://raw.githubusercontent.com/aquacropos/geoaquacrop_simulate/main/docs/_static/logo-mark.png"
       alt="" width="130">
</p>

<h1 align="center">geoaquacrop_simulate</h1>

<p align="center">Gridded AquaCrop-OSPy simulation engine for the GeoAquaCrop toolchain.</p>

<p align="center">
  <a href="https://pypi.org/project/geoaquacrop-simulate/"><img src="https://img.shields.io/pypi/v/geoaquacrop-simulate" alt="PyPI"></a>
  <a href="https://pypi.org/project/geoaquacrop-simulate/"><img src="https://img.shields.io/pypi/pyversions/geoaquacrop-simulate" alt="Python"></a>
  <a href="https://geoaquacrop-simulate.readthedocs.io/en/stable/"><img src="https://img.shields.io/readthedocs/geoaquacrop-simulate" alt="Docs"></a>
  <a href="https://github.com/aquacropos/geoaquacrop_simulate/actions/workflows/tests.yml"><img src="https://github.com/aquacropos/geoaquacrop_simulate/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/aquacropos/geoaquacrop_simulate/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-Apache%202.0-blue" alt="Licence"></a>
</p>

## Install

```bash
pip install geoaquacrop_simulate
```

Or install the whole toolchain in one go:

```bash
pip install geoaquacrop
```

Optional extras:

| Extra | Brings in | For |
|---|---|---|
| `correction` | geopandas, matplotlib | Yield correction and comparison figures |
| `docs` | sphinx, furo | Building the documentation locally |
| `dev` | pytest, pytest-cov | Running the test suite |

```bash
pip install "geoaquacrop_simulate[correction]"
```

Requires Python 3.11+ and the harmonised input datasets produced by
[geoaquacrop_preprocess](https://github.com/aquacropos/geoaquacrop_preprocess).

## Overview

**geoaquacrop_simulate** runs [AquaCrop-OSPy](https://github.com/aquacropos/aquacrop)
over large regions in gridded format. It takes the harmonised input datasets produced
by [geoaquacrop_preprocess](https://github.com/aquacropos/geoaquacrop_preprocess), runs
an independent AquaCrop-OSPy simulation for every grid cell in parallel, and writes per-cell
seasonal and daily results. Those outputs can then be explored with
[geoaquacrop_visualize](https://github.com/aquacropos/geoaquacrop_visualize).

It is the middle stage of the GeoAquaCrop toolchain:

```
geoaquacrop_preprocess  ->  geoaquacrop_simulate  ->  geoaquacrop_visualize
(download & harmonise)      (simulate & correct)      (explore results)
```

| Stage | Description |
|---|---|
| Input validation | Checks that climate, soil, crop calendar and crop area files exist, share a grid, and cover the requested period; derives the simulated cells from the crop area mask |
| Per-cell simulation | Builds an AquaCrop `Soil`, `Crop` and weather series per cell, adjusts crop phenology to the local growing season, runs to termination |
| Parallel execution | Distributes cells over worker processes with a progress bar; per-cell failures are logged without stopping the run |
| Derived outputs | Adds seasonal water-balance metrics via a pluggable enricher registry |
| Yield correction | Optionally bias-corrects or calibrates yields against an observational reference, per year, at the reference's native support |

## Quick start

```python
import geoaquacrop_simulate as simulate

summary_file, daily_file = simulate.run(
    data_path='/path/to/geoaquacrop_preprocess/processed',
    start_date='2008/01/01',
    end_date='2010/12/31',
    crop='Maize',
    irrigation='rainfed',          # 'rainfed' | 'irrigated'
    output_dir='outputs',
)
```

`data_path` fills the four input paths at once. Set `weather_path`, `soil_path`,
`pheno_path` and `spam_path` individually if they live in different places.

The same call through the unified toolchain façade:

```python
import geoaquacrop as gac

summary_file, daily_file = gac.simulate.run(data_path='...', crop='Maize')
```

To see every available setting:

```python
import geoaquacrop_simulate as simulate

print(simulate.example_config())        # the full settings dictionary
print(simulate.input_requirements())    # the input files each stage expects
```

This works from a script, a notebook or an IDE console (Spyder, Jupyter).

## Supported crop types

Barley, Cassava, Cotton, Dry Bean, Maize, Paddy Rice (seasons 1 & 2), Potato,
Sorghum, Soybean, Sugar Beet, Sugar Cane, Sunflower, Wheat (summer & winter).

## Output files

Written to `<output_dir>/`:

| File | Contents |
|---|---|
| `summary_results_<timestamp>.pkl` | One seasonal summary row per cell per season: yields, irrigation, harvest date, plus derived metrics |
| `daily_results_<timestamp>.pkl` | Daily water-balance and crop-growth series per cell |
| `logs/aquacrop_simulation_<timestamp>.log` | Run log, including per-cell failures |
| `yield_scaled.nc` / `yield_calibrated.nc` | Corrected yield grids, if a correction was configured |

Load them back with `simulate.load_results()`.

## Yield correction

Optional. Brings modelled yields into line with an observational reference, per year,
aggregating the model up to the reference's native support (counties, provinces,
districts) rather than rasterising the observations.

First build the reference from any boundary file and any table of yields per region
per year:

```python
simulate.build_reference(
    regions='provinces.geojson', region_id='NAME_LATN',
    table='wheat_yields.csv', table_id='region',
    year_col='year', value_col='yield_t_ha',
    out='reference.geojson',
)
```

Then pass a `correction` block to `run()`:

```python
correction = {
    'method': 'scale',                    # None | 'scale' | 'calibrate'
    'reference_path': 'reference.geojson',
    'scale_mode': 'local',                # 'global' | 'local'
    'lever': 'canopy',                    # calibrate: 'canopy' (CCx) | 'biomass' (WP)
    'reuse_results': 'latest',            # correct an existing run, no re-simulation
}
```

See the [yield correction guide](https://geoaquacrop-simulate.readthedocs.io/en/latest/corrections.html)
for what each mode does and how to interpret the results.

## Documentation

Full documentation: https://geoaquacrop-simulate.readthedocs.io/en/latest/

## Development

To work on the package itself:

```bash
git clone https://github.com/aquacropos/geoaquacrop_simulate
cd geoaquacrop_simulate
conda create -n geoaquacrop python=3.11
conda activate geoaquacrop
python -m pip install -e ".[dev,correction]"
```

Run the tests:

```bash
python -m pytest -q
```

From a checkout you can also set the configuration dictionary at the top of
`main()` in `src/geoaquacrop_simulate/run_aquacrop.py` and run the module directly:

```bash
python -m geoaquacrop_simulate.run_aquacrop
```

Do not execute module files directly — a module run as a script has no package
context and its relative imports fail.

## Licence

Apache 2.0 — see [LICENSE](https://github.com/aquacropos/geoaquacrop_simulate/blob/main/LICENSE).