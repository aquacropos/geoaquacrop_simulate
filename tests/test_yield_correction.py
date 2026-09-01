"""
Unit tests for yield_correction (per-year, region-support, area-weighted).

Synthetic region polygons and model points; no real AquaCrop runs.
Run:  pytest tests/test_yield_correction.py
"""
import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")
gpd = pytest.importorskip("geopandas")
from shapely.geometry import box

from geoaquacrop_sim.yield_correction import (
    LEVERS, area_weights, region_assignment, aggregate_to_regions,
    join_reference, scale_to_reference, calibrate_to_reference, fit_stats,
    points_to_grid, grid_to_points)

YEARS = [2008, 2009, 2010]


# --------------------------------------------------------- fixtures ---------

@pytest.fixture
def regions():
    """Four 1x1 degree 'regions' tiling a 2x2 degree block."""
    polys, region_id = [], []
    for i, (x0, y0) in enumerate([(-101, 40), (-100, 40),
                                  (-101, 39), (-100, 39)], start=1):
        polys.append(box(x0, y0, x0 + 1, y0 + 1))
        region_id.append(f"2000{i}")
    return gpd.GeoDataFrame({"region_id": region_id}, geometry=polys, crs=4326)


@pytest.fixture
def points():
    """Model points on a fine grid covering the regions, varying by year."""
    lat = np.arange(39.05, 41.0, 0.1)
    lon = np.arange(-100.95, -99.0, 0.1)
    rows = []
    for i, yr in enumerate(YEARS):
        for yy in lat:
            for xx in lon:
                rows.append({"year": yr, "y": yy, "x": xx,
                             "val": (6.0 + (yy - 39.0) + 0.5 * (xx + 101.0))
                                    * (1 + 0.1 * i)})
    return pd.DataFrame(rows)


@pytest.fixture
def assignment(points, regions):
    return region_assignment(points, regions)


def _reference_from(points, assignment, factor_by_year=None):
    """Reference built from the area-weighted region aggregate, so exact
    recovery assertions are meaningful."""
    agg = aggregate_to_regions(points, assignment)
    ref = agg[["year", "region_id", "model"]].rename(columns={"model": "ref"})
    if factor_by_year:
        ref = ref.assign(ref=ref["ref"] * ref["year"].map(factor_by_year))
    return ref


# --------------------------------------------------------- weights ----------

def test_area_weights_follow_cosine():
    w = area_weights([0.0, 45.0, 60.0])
    assert w[0] == pytest.approx(1.0)
    assert w[1] == pytest.approx(np.cos(np.deg2rad(45.0)))
    assert w[1] > w[2]


# --------------------------------------------------------- assignment -------

def test_assignment_covers_cells(points, regions):
    a = region_assignment(points, regions)
    assert set(a.columns) == {"y", "x", "region_id"}
    assert a["region_id"].nunique() == 4
    # unique cells only, not one row per year
    assert len(a) == points[["y", "x"]].drop_duplicates().shape[0]


def test_assignment_drops_cells_outside_counties(regions):
    pts = pd.DataFrame({"year": [2008, 2008], "y": [40.5, 10.0],
                        "x": [-100.5, 0.0], "val": [1.0, 2.0]})
    a = region_assignment(pts, regions)
    assert len(a) == 1


# --------------------------------------------------------- aggregation ------

def test_aggregate_is_per_year_and_per_county(points, assignment):
    agg = aggregate_to_regions(points, assignment)
    assert set(agg.columns) == {"year", "region_id", "model", "weight"}
    assert sorted(agg["year"].unique()) == YEARS
    assert agg["region_id"].nunique() == 4
    assert len(agg) == 4 * len(YEARS)


def test_aggregate_is_area_weighted(regions):
    """Two cells at different latitudes combine by cos(lat), not equally."""
    poly = gpd.GeoDataFrame({"region_id": ["99999"]},
                            geometry=[box(-1, 0, 1, 70)], crs=4326)
    pts = pd.DataFrame({"year": [2008, 2008], "y": [20.0, 60.0],
                        "x": [0.0, 0.0], "val": [10.0, 20.0]})
    a = region_assignment(pts, poly)
    got = float(aggregate_to_regions(pts, a)["model"].iloc[0])
    w = area_weights([20.0, 60.0])
    assert got == pytest.approx((w[0] * 10 + w[1] * 20) / w.sum())
    assert got != pytest.approx(15.0)          # NOT the unweighted mean


def test_aggregate_weight_is_summed_area(points, assignment):
    agg = aggregate_to_regions(points, assignment)
    total = agg.loc[agg["year"] == 2008, "weight"].sum()
    expected = area_weights(
        points.loc[points["year"] == 2008]
              .merge(assignment, on=["y", "x"])["y"].values).sum()
    assert total == pytest.approx(expected)


def test_aggregate_accepts_grid(points, assignment):
    from_points = aggregate_to_regions(points, assignment)
    from_grid = aggregate_to_regions(points_to_grid(points), assignment)
    merged = from_points.merge(from_grid, on=["year", "region_id"],
                               suffixes=("_p", "_g"))
    assert np.allclose(merged["model_p"], merged["model_g"])


# --------------------------------------------------------- scaling ----------

def test_scale_global_recovers_factor_per_year(points, assignment):
    truth = {2008: 1.3, 2009: 0.8, 2010: 1.1}
    ref = _reference_from(points, assignment, truth)
    res = scale_to_reference(points, ref, assignment, mode="global")
    for yr in YEARS:
        assert float(res["factor"].loc[yr]) == pytest.approx(truth[yr], rel=1e-9)


def test_scale_corrected_stays_on_simulation_grid(points, assignment):
    ref = _reference_from(points, assignment)
    res = scale_to_reference(points, ref, assignment, mode="global")
    assert res["corrected"].dims == ("year", "y", "x")
    assert list(res["corrected"]["year"].values) == YEARS


def test_scale_local_is_exact_per_county_per_year(points, assignment):
    ref = _reference_from(points, assignment, {2008: 1.3, 2009: 0.8, 2010: 1.1})
    res = scale_to_reference(points, ref, assignment, mode="local")
    assert res["stats"]["rmse"] == pytest.approx(0.0, abs=1e-9)
    assert res["county_table"]["factor"].nunique() > 1


def test_scale_reports_per_year_stats(points, assignment):
    ref = _reference_from(points, assignment, {2008: 1.3, 2009: 0.8, 2010: 1.1})
    res = scale_to_reference(points, ref, assignment, mode="global")
    assert list(res["stats_per_year"].index) == YEARS


def test_scale_bad_mode(points, assignment):
    with pytest.raises(ValueError):
        scale_to_reference(points, _reference_from(points, assignment),
                           assignment, mode="nope")


# --------------------------------------------------------- calibration ------

def test_calibrate_recovers_parameter(points, assignment):
    TRUE = 0.70
    ref = _reference_from(points, assignment)

    def runner(p):
        out = points.copy()
        out["val"] = out["val"] * (p / TRUE)
        return out

    res = calibrate_to_reference(runner, ref, assignment, lever="canopy",
                                 bounds=(0.3, 1.2))
    assert res["parameter"] == "CCx"
    assert res["value"] == pytest.approx(TRUE, abs=0.01)
    assert list(res["stats_per_year"].index) == YEARS


def test_calibrate_single_value_cannot_fit_diverging_years(points, assignment):
    """When years need opposite corrections, one parameter lands in between and
    per-year biases keep opposite signs -- an honest structural limit."""
    ref = _reference_from(points, assignment,
                          {2008: 0.7, 2009: 1.0, 2010: 1.3})

    def runner(p):
        out = points.copy()
        out["val"] = out["val"] * p
        return out

    res = calibrate_to_reference(runner, ref, assignment, lever="biomass",
                                 bounds=(0.5, 1.5))
    b = res["stats_per_year"]["bias"]
    assert b.loc[2008] > 0
    assert b.loc[2010] < 0


def test_calibrate_bad_lever(points, assignment):
    with pytest.raises(ValueError):
        calibrate_to_reference(lambda p: points,
                               _reference_from(points, assignment),
                               assignment, lever="harvest_index")


def test_levers_are_only_ccx_and_wp():
    assert set(LEVERS) == {"canopy", "biomass"}
    assert LEVERS["canopy"]["parameter"] == "CCx"
    assert LEVERS["biomass"]["parameter"] == "WP"


# --------------------------------------------------------- stats ------------

def test_fit_stats_per_year_and_overall(points, assignment):
    ref = _reference_from(points, assignment)
    table = join_reference(aggregate_to_regions(points, assignment), ref)
    st = fit_stats(table)
    assert st["overall"]["rmse"] == pytest.approx(0.0, abs=1e-9)
    assert len(st["per_year"]) == len(YEARS)


def test_roundtrip_points_grid(points):
    back = grid_to_points(points_to_grid(points))
    assert len(back) == len(points)
