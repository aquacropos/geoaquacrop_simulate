# geoaquacrop_simulate

> Gridded FAO AquaCrop simulation engine for the GeoAquaCrop toolchain.

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-Apache%20License%202.0-blue)

## Overview

**geoaquacrop_simulate** runs [FAO AquaCrop](https://www.fao.org/aquacrop) over large regions in gridded format. It takes the harmonised input datasets produced by [geoaquacrop_preproc](https://github.com/aquacropos/geoaquacrop_preprocess), runs an independent AquaCrop simulation for every grid cell in parallel, and writes per-cell seasonal and daily results. These outputs can then be visualized by [geoaquacrop_visualize](https://github.com/aquacropos/geoaquacrop_visualize).

It is the middle stage of the GeoAquaCrop toolchain:

```
geoaquacrop_preprocess  ->  geoaquacrop_simulate  ->  geoaquacrop_visualize
(download & harmonise)   (simulate & correct)       (explore results)
```

| Stage | Description |
| ----- | ----------- |
| Input validation | Checks that climate, soil, crop calendar and crop area files exist, share a grid, and cover the requested period; derives the simulated cells from the crop area mask |
| Per-cell simulation | Builds an AquaCrop `Soil`, `Crop` and weather series per cell, adjusts crop phenology to the local growing season, runs to termination |
| Parallel execution | Distributes cells over worker processes with a progress bar; per-cell failures are logged without stopping the run |
| Derived outputs | Adds seasonal water-balance metrics via a pluggable enricher registry |
| Yield correction | Optionally bias-corrects or calibrates yields against an observational reference, per year, at the reference's native support |

## Supported crop types

Barley, Cassava, Cotton, Dry Bean, Maize, Paddy Rice (seasons 1 & 2), Potato, Sorghum, Soybean, Sugar Beet, Sugar Cane, Sunflower, Wheat (summer & winter)

## Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/)
- Python 3.11+
- Input datasets produced by [geoaquacrop_preproc](https://github.com/aquacropos/geoaquacrop_preprocess)

## Installation

```bash
git clone https://github.com/aquacropos/geoaquacrop_simulate
cd geoaquacrop_simulate-dev
conda create -n geoaquacrop python=3.11
conda activate geoaquacrop
python -m pip install -e .
```

Optional extras: `.[dev]` (pytest), `.[correction]` (geopandas, matplotlib), `.[plots]` (dash, plotly).

## Quick start

### Option A — edit and run the main script

Open `src/geoaquacrop_simulate/run_aquacrop.py`, set the configuration dictionary at the top of `main()`, and run:

```bash
conda activate geoaquacrop
python -m geoaquacrop_simulate.run_aquacrop
```

Key input arguments:

```python
config_dict = {
    'weather_path': '/path/to/preproc/processed',
    'soil_path':    '/path/to/preproc/processed',
    'pheno_path':   '/path/to/preproc/processed',
    'spam_path':    '/path/to/preproc/processed',
    'start_date':   '2008/01/01',
    'end_date':     '2010/12/31',
    'crop':         'Maize',
    'irrigation':   'rainfed',      # 'rainfed' | 'irrigated'
    'output_dir':   'outputs',
}
```

### Option B — Python API

```python
from geoaquacrop_simulate.run_aquacrop import main

summary_file, daily_file = main()
```

This is also how to run from an IDE console (Spyder, Jupyter). Do not execute module files directly — a module run as a script has no package context and its relative imports fail.

## Output files

Written to `<output_dir>/`:

| File | Contents |
| ---- | -------- |
| `summary_results_<timestamp>.pkl` | One seasonal summary row per cell per season: yields, irrigation, harvest date, plus derived metrics |
| `daily_results_<timestamp>.pkl` | Daily water-balance and crop-growth series per cell |
| `logs/aquacrop_simulation_<timestamp>.log` | Run log, including per-cell failures |
| `yield_scaled.nc` / `yield_calibrated.nc` | Corrected yield grids, if a correction was configured |

## Yield correction

Optional. Brings modelled yields into line with an observational reference, per year, aggregating the model up to the reference's native support (e.g. counties) rather than rasterising the observations.

```python
'correction': {
    'method': 'scale',            # None | 'scale' | 'calibrate'
    'reference_path': 'reference/high_plains_maize_reference.geojson',
    'scale_mode': 'local',        # 'global' | 'local'
    'lever': 'canopy',            # calibrate: 'canopy' (CCx) | 'biomass' (WP)
    'reuse_results': 'latest',    # scale an existing run with no simulation
}
```

See the [yield correction guide](https://geoaquacrop-simulate.readthedocs.io/en/stable/corrections.html) for what each mode does and how to interpret the results.

## Documentation

Full documentation: <https://geoaquacrop-simulate.readthedocs.io>

## Tests

```bash
python -m pytest -q
```

## License

MIT — see [LICENSE](LICENSE).
