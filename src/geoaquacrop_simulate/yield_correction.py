"""
yield_correction.py — numerical primitives for rough yield bias-correction and
single-parameter calibration in geoaquacrop_simulate.

Design rules (deliberate, not configurable):

  * NO TEMPORAL AGGREGATION. Every quantity carries a `year`. Scaling factors
    are fitted and applied per year. Calibration fits ONE parameter across all
    years (a crop parameter is not a per-year quantity), but its objective runs
    over every (year, region) pair without averaging years first. All reported
    output keeps the year dimension.

  * THE MODEL IS AGGREGATED TO THE REFERENCE'S NATIVE SUPPORT. The reference is
    region polygons with a yield per region per year; it is never rasterised.
    Simulation cells are assigned to the region containing their centre and
    combined as an AREA-WEIGHTED mean (weights proportional to cos(latitude),
    the cell-area factor on a regular lat/lon grid). Comparison, factors and
    the calibration objective all live at region scale.

  * CORRECTED OUTPUT STAYS ON THE SIMULATION GRID. Only the correction is
    derived at region scale; it is applied back to the fine grid.

Data model::
    model points : tidy DataFrame [year, y, x, val]
    assignment   : tidy DataFrame [y, x, region_id]  (unique simulation cells)
    reference    : tidy DataFrame [region_id, year, ref]
    region table : tidy DataFrame [year, region_id, model, ref, weight, ...]
    corrected    : xarray.DataArray (year, y, x) on the simulation grid

Levers for calibration (measured to give a reliable, monotonic yield response)::
    canopy  -> CCx (maximum canopy cover)
    biomass -> WP  (normalised water productivity)

CGC is not offered (yield is insensitive to it once canopy reaches CCx before
season end); harvest index is excluded as the least defensible lever.
"""
import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError:
    xr = None


LEVERS = {
    "canopy":  {"parameter": "CCx", "bounds": (0.30, 0.99)},
    "biomass": {"parameter": "WP",  "bounds": (5.0, 40.0)},
}


# --------------------------------------------------------- area weights -----

def area_weights(lat):
    """Relative cell area on a regular lat/lon grid: proportional to cos(lat).
    Constant dlat/dlon cancel, so cos(lat) alone is the correct weight."""
    return np.cos(np.deg2rad(np.asarray(lat, dtype=float)))


# --------------------------------------------------------- points / grids ---

def points_to_grid(points):
    """Tidy points -> DataArray (year, y, x) on the simulation grid."""
    return (points.set_index(["year", "y", "x"])["val"]
                  .to_xarray().rename("yield"))


def grid_to_points(da):
    """DataArray (year, y, x) -> tidy points [year, y, x, val]."""
    df = da.rename("val").to_dataframe().reset_index()
    return df[["year", "y", "x", "val"]].dropna(subset=["val"])


def as_points(source):
    """Accept tidy points or a (year, y, x) DataArray; return tidy points."""
    return source if isinstance(source, pd.DataFrame) else grid_to_points(source)


# --------------------------------------------------------- region support ---

def region_assignment(points, regions):
    """Assign each unique simulation cell to the region containing its centre.

    points   : tidy points (only y/x are used)
    regions : GeoDataFrame with a 'region_id' column, EPSG:4326

    Returns a DataFrame [y, x, region_id]; cells outside every region are dropped.
    Computed once per cell set and reused across calibration iterations, since
    the geometry does not change with the trial parameter.
    """
    import geopandas as gpd

    cells = points[["y", "x"]].drop_duplicates().reset_index(drop=True)
    gdf = gpd.GeoDataFrame(cells,
                           geometry=gpd.points_from_xy(cells["x"], cells["y"]),
                           crs=4326)
    joined = gpd.sjoin(gdf, regions[["region_id", "geometry"]], how="left",
                       predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    out = joined[["y", "x", "region_id"]].dropna(subset=["region_id"])
    return out.reset_index(drop=True)


def aggregate_to_regions(source, assignment):
    """Area-weighted aggregation of model values to regions, per year.

    Returns a DataFrame [year, region_id, model, weight] where `weight` is the summed
    cos(latitude) of the contributing simulation cells -- i.e. the region's
    simulated area, used later to weight region-level statistics.
    """
    points = as_points(source)
    df = points.merge(assignment, on=["y", "x"], how="inner")
    if df.empty:
        return pd.DataFrame(columns=["year", "region_id", "model", "weight"])
    df = df.assign(_w=area_weights(df["y"].values))
    df["_wv"] = df["_w"] * df["val"].astype(float)
    g = df.groupby(["year", "region_id"])[["_w", "_wv"]].sum()
    out = (g["_wv"] / g["_w"]).rename("model").reset_index()
    out["weight"] = g["_w"].values
    return out


def join_reference(county_model, reference):
    """Inner-join aggregated model to the reference on (year, region_id)."""
    ref = reference.rename(columns={"value": "ref"}) if "value" in reference \
        else reference
    out = county_model.merge(ref[["year", "region_id", "ref"]],
                             on=["year", "region_id"], how="inner")
    return out.dropna(subset=["model", "ref"])


# --------------------------------------------------------- statistics -------

def _wstats(d, w):
    if d.size == 0:
        return {"n": 0, "bias": np.nan, "mae": np.nan, "rmse": np.nan}
    return {"n": int(d.size),
            "bias": float(np.sum(w * d) / np.sum(w)),
            "mae": float(np.sum(w * np.abs(d)) / np.sum(w)),
            "rmse": float(np.sqrt(np.sum(w * d ** 2) / np.sum(w)))}


def fit_stats(table):
    """Area-weighted agreement statistics from a joined region table.

    Returns {'per_year': DataFrame indexed by year, 'overall': dict}. Counties
    are weighted by their simulated area, so a region with a handful of
    simulated cells does not count the same as a large one.
    """
    rows = []
    for yr, sub in table.groupby("year"):
        d = (sub["model"] - sub["ref"]).to_numpy(float)
        rows.append({"year": int(yr), **_wstats(d, sub["weight"].to_numpy(float))})
    per_year = (pd.DataFrame(rows).set_index("year") if rows
                else pd.DataFrame(columns=["n", "bias", "mae", "rmse"]))
    d = (table["model"] - table["ref"]).to_numpy(float)
    overall = _wstats(d, table["weight"].to_numpy(float))
    return {"per_year": per_year, "overall": overall}


def _weighted_sse(table):
    """Area-weighted sum of squared differences over every (year, region) pair.
    Years are never averaged before differencing."""
    if table.empty:
        return np.inf
    d = (table["model"] - table["ref"]).to_numpy(float)
    w = table["weight"].to_numpy(float)
    return float(np.sum(w * d ** 2))


# --------------------------------------------------------- scaling ----------

def scale_to_reference(source, reference, assignment, mode="global"):
    """Per-year multiplicative bias correction, derived at region scale.

    mode="global"  one factor PER YEAR for the whole domain.
    mode="local"   one factor PER YEAR PER REGION, applied to that region's
                   simulation cells.

    The corrected field is returned on the simulation grid.
    """
    points = as_points(source)
    grid = points_to_grid(points)
    county_model = aggregate_to_regions(points, assignment)
    table = join_reference(county_model, reference)

    if mode == "global":
        f = (table.assign(_r=table["weight"] * table["ref"],
                          _m=table["weight"] * table["model"])
                  .groupby("year")[["_r", "_m"]].sum())
        factor = (f["_r"] / f["_m"]).rename("factor")          # one per year
        table = table.merge(factor, left_on="year", right_index=True)
    elif mode == "local":
        table = table.assign(factor=table["ref"] / table["model"])
        factor = table.set_index(["year", "region_id"])["factor"]
    else:
        raise ValueError("mode must be 'global' or 'local'")

    corrected = _apply_factor(grid, points, assignment, table, mode)

    # the factor is constant within a region and the aggregation is a weighted
    # mean (linear), so the corrected region mean is exactly model x factor
    table["corrected"] = table["model"] * table["factor"]
    table["residual"] = table["corrected"] - table["ref"]
    stats = fit_stats(table.assign(model=table["corrected"]))
    return {"mode": mode,
            "factor": factor,
            "corrected": corrected.rename("yield_corrected"),
            "county_table": table,
            "stats": stats["overall"],
            "stats_per_year": stats["per_year"]}


def _apply_factor(grid, points, assignment, table, mode):
    """Multiply the simulation grid by the per-year (and per-region) factor."""
    if mode == "global":
        per_year = table.groupby("year")["factor"].first()
        f = xr.DataArray(per_year.to_numpy(float),
                         coords={"year": per_year.index.to_numpy()},
                         dims=("year",))
        return grid * f
    cell_factor = (points.merge(assignment, on=["y", "x"], how="left")
                         .merge(table[["year", "region_id", "factor"]],
                                on=["year", "region_id"], how="left"))
    cell_factor["factor"] = cell_factor["factor"].fillna(1.0)
    f = (cell_factor.set_index(["year", "y", "x"])["factor"].to_xarray())
    return grid * f.reindex_like(grid).fillna(1.0)


# --------------------------------------------------------- calibration ------

def _golden(f, a, b, tol, max_iter):
    """Golden-section minimisation of a 1-D unimodal f on [a, b]; one new
    evaluation per iteration."""
    gr = (5 ** 0.5 - 1) / 2
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(max_iter):
        if (b - a) < tol:
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = f(d)
    return (a + b) / 2.0


def calibrate_to_reference(runner, reference, assignment, lever="canopy",
                           bounds=None, tol=1e-3, max_iter=20):
    """Fit ONE crop parameter so region-aggregated model yield matches the
    reference, scored over every (year, region) pair.

    runner(value) -> tidy model points from a run with the parameter set.
    """
    if lever not in LEVERS:
        raise ValueError(f"lever must be one of {list(LEVERS)}")
    spec = LEVERS[lever]
    lo, hi = bounds if bounds is not None else spec["bounds"]

    def objective(p):
        table = join_reference(
            aggregate_to_regions(runner(p), assignment), reference)
        return _weighted_sse(table)

    best = _golden(objective, lo, hi, tol * (hi - lo), max_iter)

    points = as_points(runner(best))
    table = join_reference(aggregate_to_regions(points, assignment), reference)
    table["residual"] = table["model"] - table["ref"]
    stats = fit_stats(table)
    return {"lever": lever,
            "parameter": spec["parameter"],
            "value": float(best),
            "corrected": points_to_grid(points).rename("yield_corrected"),
            "county_table": table,
            "stats": stats["overall"],
            "stats_per_year": stats["per_year"]}
