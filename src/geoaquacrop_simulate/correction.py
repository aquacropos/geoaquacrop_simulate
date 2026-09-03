"""
correction.py — config-driven yield bias-correction / calibration for the
geoaquacrop_simulate pipeline. All behaviour comes from one optional `correction`
block in the simulation config; when it is absent or method=None the pipeline is
untouched.

Config block (in run_aquacrop.py's config_dict)::

    'correction': {
        'method':        None,      # None | 'scale' | 'calibrate'
        'reference_path': None,     # region reference (GeoJSON/GPKG/shapefile)
                                    #   with 'region_id' and 'yield_<year>' fields
        'value_col':     'Dry yield (tonne/ha)',   # model column to correct
        'scale_mode':    'global',  # method='scale':  'global' | 'local'
        'lever':         'canopy',  # method='calibrate': 'canopy' | 'biomass'
        'bounds':         None,     # optional (lo, hi) search bounds
        'search_sample':  200,      # cells subsampled for the calibration search
        'reuse_results':  None,     # None | 'latest' | path to a saved
                                    #   summary_results_*.pkl (scale only)
        'output_name':    None,     # None -> yield_scaled.nc / yield_calibrated.nc
    }

Everything is PER YEAR: simulated seasons are never averaged, factors are fitted
and applied per year, and outputs carry a `year` dimension.

The reference keeps its native region support. Simulation cells are aggregated
UP to regions (area-weighted) for comparison; the correction is then applied
back to the full simulation grid, which is what gets written.
"""
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError:
    xr = None

from .yield_correction import (LEVERS, scale_to_reference,
                               calibrate_to_reference, aggregate_to_regions,
                               region_assignment, join_reference, fit_stats,
                               points_to_grid)


DEFAULT_CORRECTION = {
    "method": None,
    "reference_path": None,
    "value_col": "Dry yield (tonne/ha)",
    "scale_mode": "global",
    "lever": "canopy",
    "bounds": None,
    "search_sample": 200,
    "reuse_results": None,
    "output_name": None,          # derived from the method when left as None
}

# automatic output names, so the two modes never overwrite each other
OUTPUT_NAMES = {"scale": "yield_scaled.nc", "calibrate": "yield_calibrated.nc"}


# --------------------------------------------------------- config -----------

def output_name(cfg):
    """File name for this correction: the user's `output_name` if set, else one
    derived from the method (yield_scaled.nc / yield_calibrated.nc)."""
    return cfg.get("output_name") or OUTPUT_NAMES[cfg["method"]]


def normalise_correction(raw):
    """Merge a user `correction` block onto defaults and validate. Returns a
    complete dict, or None when correction is switched off."""
    if not raw or not raw.get("method"):
        return None
    cfg = {**DEFAULT_CORRECTION, **raw}
    if cfg["method"] not in ("scale", "calibrate"):
        raise ValueError("correction.method must be 'scale', 'calibrate' or None")
    if cfg["reference_path"] is None:
        raise ValueError("correction.reference_path is required when method is set")
    if cfg["method"] == "scale" and cfg["scale_mode"] not in ("global", "local"):
        raise ValueError("correction.scale_mode must be 'global' or 'local'")
    if cfg["method"] == "calibrate" and cfg["lever"] not in LEVERS:
        raise ValueError(f"correction.lever must be one of {list(LEVERS)}")
    if cfg["reuse_results"] and cfg["method"] != "scale":
        raise ValueError(
            "correction.reuse_results only works with method='scale'; "
            "calibration varies a crop parameter so it must re-simulate.")
    cfg["output_name"] = output_name(cfg)
    return cfg


# --------------------------------------------------------- reference --------

def load_reference(cfg):
    """Load the region reference.

    Returns (counties_gdf, reference_long) where counties_gdf has 'region_id' and
    geometry, and reference_long is a tidy DataFrame [region_id, year, ref] built
    from the 'yield_<year>' fields.
    """
    import geopandas as gpd

    src = cfg["reference_path"]
    gdf = src.copy() if hasattr(src, "geometry") else gpd.read_file(str(src))
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    if "region_id" not in gdf.columns:
        raise ValueError("the region reference needs a 'region_id' column; rebuild "
                         "it with build_reference.py")
    gdf["region_id"] = gdf["region_id"].astype(str)

    year_cols = [c for c in gdf.columns if str(c).startswith("yield_")]
    if not year_cols:
        raise ValueError(
            "the region reference needs per-year 'yield_<year>' fields -- "
            "corrections are applied per year. Rebuild it with "
            "build_reference.py.")
    long = gdf[["region_id"] + year_cols].melt(id_vars="region_id", var_name="year",
                                          value_name="ref")
    long["year"] = long["year"].str.replace("yield_", "", regex=False).astype(int)
    long = long.dropna(subset=["ref"])
    return gdf[["region_id", "geometry"]], long


# --------------------------------------------------------- model points -----

def _derive_year(df, start_year=None):
    """Calendar year for each summary row.

    Prefers the harvest-date year, which is how yield statistics (e.g. USDA
    NASS) are reported, so model and reference years line up. Falls back to
    start_year + Season index.
    """
    if "Harvest Date (YYYY/MM/DD)" in df.columns:
        yr = pd.to_datetime(df["Harvest Date (YYYY/MM/DD)"],
                            errors="coerce").dt.year
        if yr.notna().any():
            return yr
    if "Season" in df.columns and start_year is not None:
        return df["Season"].astype(int) + int(start_year)
    raise KeyError(
        "cannot determine the year of each simulated season: no usable "
        "'Harvest Date (YYYY/MM/DD)' column and no 'Season' + config "
        "'start_date' to fall back on.")


def summary_to_points(summary_results, value_col, start_year=None):
    """List of per-cell summary frames -> tidy points [year, y, x, val].

    One row per cell PER YEAR. No averaging over seasons at any point; the
    groupby only collapses genuine duplicates within the same cell-year.
    """
    df = pd.concat(summary_results, ignore_index=True)
    if value_col not in df.columns:
        raise KeyError(f"'{value_col}' not in summary columns: {list(df.columns)}")
    df = df.copy()
    df["year"] = _derive_year(df, start_year)
    df = df.dropna(subset=["x", "y", "year", value_col])
    df["year"] = df["year"].astype(int)
    return (df.groupby(["year", "y", "x"])[value_col].mean()
              .rename("val").reset_index())


def summary_to_grid(summary_results, value_col="Dry yield (tonne/ha)",
                    start_year=None):
    """Convenience: per-cell frames -> (year, y, x) yield DataArray."""
    return points_to_grid(summary_to_points(summary_results, value_col,
                                            start_year))


def _start_year(config):
    try:
        return int(str(config.get("start_date"))[:4])
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------- reporting --------

def log_stats(logger, label, result):
    """Log the per-year table and the overall line."""
    per_year = result.get("stats_per_year")
    logger.info(f"{label}: agreement with the reference, per year "
                f"(region scale, area-weighted)")
    if per_year is not None:
        for yr, row in per_year.iterrows():
            logger.info(f"  {yr}  regions={int(row['n']):>5}  "
                        f"bias={row['bias']:+.3f}  MAE={row['mae']:.3f}  "
                        f"RMSE={row['rmse']:.3f}")
    st = result["stats"]
    logger.info(f"  all years  n={st['n']}  bias={st['bias']:+.3f}  "
                f"MAE={st['mae']:.3f}  RMSE={st['rmse']:.3f}")


def save_correction(result, output_dir, name):
    """Write the corrected (year, y, x) grid, plus the region-level comparison
    table beside it as CSV."""
    out = Path(output_dir) / name
    da = result["corrected"].rename("yield_corrected")
    da.attrs["correction"] = result.get("mode") or result.get("lever", "")
    if "value" in result:
        da.attrs[result["parameter"]] = result["value"]
    factor = result.get("factor")
    if factor is not None and isinstance(factor, pd.Series) \
            and factor.index.nlevels == 1:
        da.attrs["factor_per_year"] = ", ".join(
            f"{int(y)}={float(v):.4f}" for y, v in factor.items())
    da.to_netcdf(out)

    table = result.get("county_table")
    if table is not None:
        table.to_csv(out.with_name(out.stem + "_regions.csv"), index=False)
    return out


# --------------------------------------------------- calibration phase 1 ----

def calibration_override(config, processor_cls, validated_inputs, coords_df,
                         logger):
    """Phase 1 of calibration: run the parameter search on a subsample of cells
    BEFORE the full simulation, so the full run happens exactly once -- with the
    calibrated parameter already applied.

    Returns {'crop_param_override': {param: value}}, or {} when not calibrating.
    """
    cfg = normalise_correction(config.get("correction"))
    if cfg is None or cfg["method"] != "calibrate":
        return {}

    regions, reference = load_reference(cfg)
    param = LEVERS[cfg["lever"]]["parameter"]
    start_year = _start_year(config)
    n = cfg["search_sample"]
    coords_search = (coords_df.sample(min(n, len(coords_df)), random_state=0)
                     if n else coords_df)

    def runner(value):
        sub_cfg = {**config, "crop_param_override": {param: value}}
        proc = processor_cls(sub_cfg, validated_inputs, logger)
        summ, _ = proc.run_parallel(coords_search)
        return summary_to_points(summ, cfg["value_col"], start_year)

    # the cell -> region mapping depends only on geometry, so build it once
    probe = runner(sum(LEVERS[cfg["lever"]]["bounds"]) / 2)
    assignment = region_assignment(probe, regions)
    logger.info(f"Calibration search: {cfg['lever']} ({param}) on "
                f"{len(coords_search)} of {len(coords_df)} cells "
                f"({assignment['region_id'].nunique()} regions), scored per year")

    cal = calibrate_to_reference(runner, reference, assignment,
                                 lever=cfg["lever"], bounds=cfg["bounds"])
    logger.info(f"Calibrated {param}={cal['value']:.4f} — applying to the full run")
    return {"crop_param_override": {param: float(cal["value"])}}


# --------------------------------------------------------- orchestration ----

def run_correction(processor, summary_results, coords_df):
    """Config-driven entry point. Scales, or reports the calibrated run, against
    the region reference; writes the corrected per-year grid and the region
    table. Returns the result dict (or None if correction is off)."""
    cfg = normalise_correction(processor.config.get("correction"))
    if cfg is None:
        return None
    log = processor.logger
    regions, reference = load_reference(cfg)
    points = summary_to_points(summary_results, cfg["value_col"],
                               _start_year(processor.config))
    assignment = region_assignment(points, regions)
    log.info(f"Aggregated {len(assignment)} simulation cells to "
             f"{assignment['region_id'].nunique()} regions (area-weighted)")

    if cfg["method"] == "scale":
        result = scale_to_reference(points, reference, assignment,
                                    mode=cfg["scale_mode"])
        if cfg["scale_mode"] == "global":
            log.info("Bias-correction (scale, global) factors per year: "
                     + ", ".join(f"{int(y)}={float(v):.4f}"
                                 for y, v in result["factor"].items()))
        else:
            log.info("Bias-correction (scale, local): one factor per year "
                     "per region")
        log_stats(log, "scale", result)
    else:  # calibrate — the search ran in phase 1; report on the full run
        param = LEVERS[cfg["lever"]]["parameter"]
        value = (processor.config.get("crop_param_override") or {}).get(param)
        table = join_reference(aggregate_to_regions(points, assignment),
                               reference)
        table["residual"] = table["model"] - table["ref"]
        stats = fit_stats(table)
        result = {"lever": cfg["lever"], "parameter": param,
                  "value": float(value) if value is not None else np.nan,
                  "corrected": points_to_grid(points).rename("yield_corrected"),
                  "county_table": table,
                  "stats": stats["overall"],
                  "stats_per_year": stats["per_year"]}
        log.info(f"Calibrated {param}={result['value']:.4f}")
        log_stats(log, "calibrate", result)

    out = save_correction(result, processor.config["output_dir"],
                          cfg["output_name"])
    log.info(f"Corrected yield (per year) written to {out}")
    log.info(f"Region comparison table: {out.with_name(out.stem + '_regions.csv')}")
    return result


# --------------------------------------------------- reuse a saved run ------

class _SavedRunShim:
    """Minimal ParallelProcessor stand-in for correcting a saved run. Only
    scaling reaches this path (validated in normalise_correction), so no
    simulation capability is needed."""

    def __init__(self, config, validated_inputs=None, logger=None):
        self.config = config
        self.validated_inputs = validated_inputs or {}
        self.logger = logger


def find_latest_summary(output_dir):
    """Newest summary_results_*.pkl in output_dir."""
    files = sorted(Path(output_dir).glob("summary_results_*.pkl"))
    if not files:
        raise FileNotFoundError(f"no summary_results_*.pkl in {output_dir}")
    return files[-1]


def should_reuse(config):
    """True when the config asks for correction of an already-saved run, so the
    caller can skip simulation entirely."""
    cfg = normalise_correction(config.get("correction"))
    return bool(cfg and cfg["reuse_results"])


def load_saved_summary(config, logger):
    """Load the saved per-cell summaries named by correction.reuse_results."""
    import pickle
    cfg = normalise_correction(config.get("correction"))
    where = cfg["reuse_results"]
    path = (find_latest_summary(config["output_dir"]) if where == "latest"
            else Path(where))
    logger.info(f"Reusing saved results (no simulation): {path}")
    with open(path, "rb") as f:
        return pickle.load(f)


def correct_saved_run(config, logger=None):
    """Apply the configured scaling to an already-saved run, no simulation."""
    import logging
    log = logger or logging.getLogger("aquacrop_gridded")
    if not log.handlers:
        logging.basicConfig(level=logging.INFO)

    cfg = normalise_correction(config.get("correction"))
    if cfg is None:
        return None
    summary_results = load_saved_summary(config, log)
    pts = summary_to_points(summary_results, cfg["value_col"],
                            _start_year(config))
    coords_df = pts[["x", "y"]].drop_duplicates()
    return run_correction(_SavedRunShim(config, {}, log), summary_results,
                          coords_df)
