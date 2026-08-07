"""
correction.py — config-driven yield bias-correction / calibration for the
aquacropgrid-run pipeline. All behaviour is controlled by one optional
`correction` block in the simulation config; when it's absent or method=None the
pipeline is untouched.

Config block (put it in run_aquacrop.py's config_dict):

    'correction': {
        'method':        None,      # None | 'scale' | 'calibrate'
        'reference_path': None,     # NetCDF/GeoTIFF of reference yield, or a
                                    #   ready xarray.DataArray
        'reference_var':  None,     # variable name if the file is a Dataset
        'value_col':     'Dry yield (tonne/ha)',   # model column to correct
        'scale_mode':    'global',  # method='scale':  'global' | 'local'
        'lever':         'canopy',  # method='calibrate': 'canopy' | 'biomass'
        'bounds':         None,     # optional (lo, hi) search bounds
        'search_sample':  200,      # cells subsampled for the calibration search
        'reuse_results':  None,     # None | 'latest' | path to a saved
                                    #   summary_results_*.pkl. Set to scale a
                                    #   finished run without re-simulating.
        'output_name':   'yield_corrected.nc',
    }

Numerical primitives live in yield_correction.py. Scaling runs on the full,
dense simulation grid and reuses scale_to_reference directly. Calibration
subsamples cells for the search, so the model is a scattered set of points, not
a dense grid — those are aggregated into reference cells by spatial binning
(robust to subsampling) rather than gridded-and-interpolated.

Pipeline hooks (documented in the README): (1) a three-line crop-parameter
override in worker_run, (2) a one-line ParallelProcessor.apply_correction call.
"""
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError:
    xr = None

from .yield_correction import scale_to_reference, calibrate_to_reference, LEVERS


DEFAULT_CORRECTION = {
    "method": None,
    "reference_path": None,
    "reference_var": None,
    "value_col": "Dry yield (tonne/ha)",
    "scale_mode": "global",
    "lever": "canopy",
    "bounds": None,
    "search_sample": 200,
    "reuse_results": None,
    "output_name": "yield_corrected.nc",
}


# --------------------------------------------------------- config -----------

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
    return cfg


# --------------------------------------------------------- grids / points ---

def _to_yx(da):
    """Normalise lat/lon-style dim names to (y, x) so grids align."""
    ren = {c: s for c, s in (("lat", "y"), ("latitude", "y"),
                             ("lon", "x"), ("longitude", "x")) if c in da.dims}
    return da.rename(ren) if ren else da


def summary_to_points(summary_results, value_col):
    """List of per-cell final_stats frames -> tidy points DataFrame [y, x, val]
    (one row per cell; seasons averaged)."""
    df = pd.concat(summary_results, ignore_index=True)
    if value_col not in df.columns:
        raise KeyError(f"'{value_col}' not in summary columns: {list(df.columns)}")
    df = df.dropna(subset=["x", "y", value_col])
    return (df.groupby(["y", "x"])[value_col].mean()
              .rename("val").reset_index())


def points_to_grid(points):
    """Points [y, x, val] -> DataArray on the (dense) simulation grid."""
    return points.set_index(["y", "x"])["val"].to_xarray()


def summary_to_grid(summary_results, value_col="Dry yield (tonne/ha)"):
    """Convenience: per-cell frames -> dense yield DataArray on (y, x)."""
    return points_to_grid(summary_to_points(summary_results, value_col))


def _nearest_idx(values, axis):
    """Index of the nearest coordinate in `axis` for each value."""
    axis = np.asarray(axis, dtype=float)
    return np.abs(np.asarray(values, dtype=float)[:, None] - axis[None, :]).argmin(1)


def points_to_reference(points, reference):
    """Aggregate scattered model points onto the reference grid by assigning
    each point to its nearest reference cell and averaging. Robust to a
    subsampled (sparse) set of cells; empty reference cells stay NaN."""
    ry, rx = reference["y"].values, reference["x"].values
    iy = _nearest_idx(points["y"].values, ry)
    ix = _nearest_idx(points["x"].values, rx)
    agg = (points.assign(_iy=iy, _ix=ix)
                 .groupby(["_iy", "_ix"])["val"].mean())
    out = np.full((ry.size, rx.size), np.nan)
    for (jy, jx), v in agg.items():
        out[jy, jx] = v
    return xr.DataArray(out, coords={"y": ry, "x": rx}, dims=("y", "x"))


def _fit_stats(model_on_ref, reference):
    m = np.asarray(model_on_ref.values, float).ravel()
    r = np.asarray(reference.values, float).ravel()
    ok = np.isfinite(m) & np.isfinite(r)
    m, r = m[ok], r[ok]
    if m.size == 0:
        return {"n": 0, "bias": np.nan, "rmse": np.nan, "mae": np.nan}
    return {"n": int(m.size), "bias": float(np.mean(m - r)),
            "rmse": float(np.sqrt(np.mean((m - r) ** 2))),
            "mae": float(np.mean(np.abs(m - r)))}


def load_reference(cfg):
    """Reference yield grid as an (y, x) DataArray: DataArray passthrough,
    NetCDF, or GeoTIFF (needs rioxarray)."""
    ref = cfg["reference_path"]
    if xr is not None and isinstance(ref, xr.DataArray):
        return _to_yx(ref)
    path = str(ref)
    if path.endswith((".nc", ".nc4", ".cdf")):
        da = (xr.open_dataset(path)[cfg["reference_var"]] if cfg["reference_var"]
              else xr.open_dataarray(path))
    elif path.endswith((".tif", ".tiff")):
        import rioxarray  # noqa: F401
        da = xr.open_dataarray(path, engine="rasterio").squeeze(drop=True)
    else:
        raise ValueError(f"unsupported reference format: {path}")
    return _to_yx(da)


def save_correction(result, output_dir, name):
    out = Path(output_dir) / name
    result["corrected"].rename("yield_corrected").to_netcdf(out)
    return out


# --------------------------------------------------------- orchestration ----

def run_correction(processor, summary_results, coords_df):
    """Config-driven entry point. Reads processor.config['correction'] and
    scales or calibrates gridded yield toward the reference, writes the
    corrected grid, and returns the result dict (or None if correction is off).
    """
    cfg = normalise_correction(processor.config.get("correction"))
    if cfg is None:
        return None
    log = processor.logger
    reference = load_reference(cfg)

    if cfg["method"] == "scale":
        model = _to_yx(summary_to_grid(summary_results, cfg["value_col"]))
        result = scale_to_reference(model, reference, mode=cfg["scale_mode"])
        log.info(f"Bias-correction (scale, {cfg['scale_mode']}): "
                 f"factor_mean={result['factor_mean']:.4f}, stats={result['stats']}")
    else:  # calibrate
        param = LEVERS[cfg["lever"]]["parameter"]
        n = cfg["search_sample"]
        coords_search = (coords_df.sample(min(n, len(coords_df)), random_state=0)
                         if n else coords_df)

        def _rerun(value, coords):
            sub_cfg = {**processor.config, "crop_param_override": {param: value}}
            proc = type(processor)(sub_cfg, processor.validated_inputs, log)
            summ, _ = proc.run_parallel(coords)
            return summary_to_points(summ, cfg["value_col"])

        # model already on the reference grid -> identity regrid in the search
        def grid_runner(value):
            return points_to_reference(_rerun(value, coords_search), reference)

        log.info(f"Calibrating {cfg['lever']} ({param}) on {len(coords_search)} cells...")
        cal = calibrate_to_reference(grid_runner, reference, lever=cfg["lever"],
                                     bounds=cfg["bounds"], regrid=lambda s, t: s)
        log.info(f"Calibrated {param}={cal['value']:.4f}; full-grid re-run to apply it...")

        pts_full = _rerun(cal["value"], coords_df)
        corrected = points_to_grid(pts_full)
        m_ref = points_to_reference(pts_full, reference)
        result = dict(cal)
        result.update(corrected=corrected, model_on_reference=m_ref,
                      residual_on_reference=(m_ref - reference),
                      stats=_fit_stats(m_ref, reference))

    out = save_correction(result, processor.config["output_dir"], cfg["output_name"])
    log.info(f"Corrected yield written to {out}")
    return result


# --------------------------------------------------- reuse a saved run ------

class _SavedRunShim:
    """Minimal ParallelProcessor stand-in for correcting a saved run. Only
    scaling reaches this path (reuse_results is validated to method='scale'),
    so no simulation capability is needed."""

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
    """Apply the configured scaling to an already-saved run, no simulation.

    Driven entirely by config['correction']['reuse_results']. Returns the
    result dict from run_correction, or None if correction is off.
    """
    import logging
    log = logger or logging.getLogger("aquacrop_gridded")
    if not log.handlers:
        logging.basicConfig(level=logging.INFO)

    cfg = normalise_correction(config.get("correction"))
    if cfg is None:
        return None
    summary_results = load_saved_summary(config, log)
    coords_df = summary_to_points(summary_results, cfg["value_col"])[["x", "y"]]
    return run_correction(_SavedRunShim(config, {}, log), summary_results, coords_df)