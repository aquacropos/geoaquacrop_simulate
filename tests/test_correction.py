"""
Unit tests for correction (config-driven, per-year, region-support).

Synthetic region polygons, per-cell summaries and a fake processor; no real
AquaCrop runs.  Run:  pytest tests/test_correction.py
"""
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")
gpd = pytest.importorskip("geopandas")
from shapely.geometry import box

from geoaquacrop_simulate.correction import (
    run_correction, normalise_correction, summary_to_points, summary_to_grid,
    load_reference, should_reuse, correct_saved_run, find_latest_summary,
    load_saved_summary, calibration_override, output_name, OUTPUT_NAMES)
from geoaquacrop_simulate.yield_correction import (region_assignment,
                                               aggregate_to_regions)

LOG = logging.getLogger("test")
LOG.addHandler(logging.NullHandler())

YEARS = [2008, 2009, 2010]
VALUE_COL = "Dry yield (tonne/ha)"


# --------------------------------------------------------- fixtures ---------

def _counties_gdf():
    polys, region_id = [], []
    for i, (x0, y0) in enumerate([(-101, 40), (-100, 40),
                                  (-101, 39), (-100, 39)], start=1):
        polys.append(box(x0, y0, x0 + 1, y0 + 1))
        region_id.append(f"2000{i}")
    return gpd.GeoDataFrame({"region_id": region_id}, geometry=polys, crs=4326)


def _coords():
    lat = np.arange(39.1, 41.0, 0.2)
    lon = np.arange(-100.9, -99.0, 0.2)
    return pd.DataFrame([(x, y) for y in lat for x in lon], columns=["x", "y"])


def _summary(coords, scale=1.0, year_factor=None, with_harvest=True):
    """final_stats-like frames: one row per cell PER SEASON."""
    year_factor = year_factor or {y: 1.0 for y in YEARS}
    rows = []
    for _, r in coords.iterrows():
        base = 6.0 + (r.y - 39.0) + 0.5 * (r.x + 101.0)
        for s, yr in enumerate(YEARS):
            row = {"x": r.x, "y": r.y, "Season": s,
                   VALUE_COL: base * scale * year_factor[yr]}
            if with_harvest:
                row["Harvest Date (YYYY/MM/DD)"] = f"{yr}/09/20"
            rows.append(row)
    return [pd.DataFrame(rows)]


def _write_reference(path, coords, year_factor=None):
    """Region reference whose values are the area-weighted aggregate of the
    default model run (optionally scaled per year)."""
    gdf = _counties_gdf()
    pts = summary_to_points(_summary(coords), VALUE_COL, 2008)
    agg = aggregate_to_regions(pts, region_assignment(pts, gdf))
    for yr in YEARS:
        vals = agg[agg["year"] == yr].set_index("region_id")["model"]
        f = (year_factor or {}).get(yr, 1.0)
        gdf[f"yield_{yr}"] = gdf["region_id"].map(vals) * f
    gdf.to_file(path, driver="GeoJSON")
    return path


class FakeProcessor:
    """Yield responds linearly to the CCx override; default is biased high."""

    def __init__(self, config, validated_inputs=None, logger=None):
        self.config = config
        self.validated_inputs = validated_inputs or {}
        self.logger = logger or LOG

    def run_parallel(self, coords_df):
        ccx = (self.config.get("crop_param_override") or {}).get("CCx", 0.96)
        return _summary(coords_df, scale=ccx / 0.70), None


class CountingProcessor(FakeProcessor):
    calls = None
    n_full_total = None

    def run_parallel(self, coords_df):
        key = "full" if len(coords_df) == type(self).n_full_total else "search"
        type(self).calls[key] += 1
        return super().run_parallel(coords_df)


@pytest.fixture
def setup(tmp_path):
    coords = _coords()
    ref = tmp_path / "ref.geojson"
    _write_reference(ref, coords)
    return coords, str(ref), str(tmp_path)


def _cfg(ref, out, **corr):
    base = {"method": "scale", "reference_path": ref}
    base.update(corr)
    return {"output_dir": out, "start_date": "2008/01/01", "correction": base}


# --------------------------------------------------------- config -----------

def test_normalise_off():
    assert normalise_correction(None) is None
    assert normalise_correction({"method": None}) is None


def test_normalise_requires_reference():
    with pytest.raises(ValueError):
        normalise_correction({"method": "scale"})


def test_calibrate_plus_reuse_rejected():
    with pytest.raises(ValueError, match="reuse_results"):
        normalise_correction({"method": "calibrate", "reference_path": "x.geojson",
                              "lever": "canopy", "reuse_results": "latest"})


# ------------------------------------------- automatic output naming --------

def test_output_name_derived_from_method():
    assert output_name({"method": "scale", "output_name": None}) == "yield_scaled.nc"
    assert output_name({"method": "calibrate",
                        "output_name": None}) == "yield_calibrated.nc"


def test_output_name_explicit_wins():
    assert output_name({"method": "scale", "output_name": "mine.nc"}) == "mine.nc"


def test_normalise_fills_output_name():
    cfg = normalise_correction({"method": "calibrate",
                                "reference_path": "x.geojson"})
    assert cfg["output_name"] == OUTPUT_NAMES["calibrate"]


def test_modes_write_distinct_files(setup):
    """The two modes must not overwrite each other."""
    coords, ref, out = setup
    for method, extra in (("scale", {}), ("calibrate", {"lever": "canopy"})):
        cfg = _cfg(ref, out, method=method, **extra)
        if method == "calibrate":
            cfg["crop_param_override"] = {"CCx": 0.70}
        run_correction(FakeProcessor(cfg, {}, LOG), _summary(coords), coords)
    assert (Path(out) / "yield_scaled.nc").exists()
    assert (Path(out) / "yield_calibrated.nc").exists()


# --------------------------------------------------------- reference --------

def test_reference_needs_year_fields(tmp_path):
    gdf = _counties_gdf()
    p = tmp_path / "noyears.geojson"
    gdf.to_file(p, driver="GeoJSON")
    with pytest.raises(ValueError, match="yield_"):
        load_reference({"reference_path": str(p)})


def test_reference_loads_long_form(setup):
    _, ref, _ = setup
    regions, long = load_reference({"reference_path": ref})
    assert set(long.columns) == {"region_id", "year", "ref"}
    assert sorted(long["year"].unique()) == YEARS
    assert "geometry" in regions


# ------------------------------------------- no temporal aggregation --------

def test_summary_to_points_keeps_every_year(setup):
    coords, _, _ = setup
    pts = summary_to_points(_summary(coords), VALUE_COL, 2008)
    assert sorted(pts["year"].unique()) == YEARS
    assert len(pts) == len(coords) * len(YEARS)


def test_summary_to_points_preserves_year_differences(setup):
    coords, _, _ = setup
    yf = {2008: 1.0, 2009: 1.5, 2010: 0.5}
    pts = summary_to_points(_summary(coords, year_factor=yf), VALUE_COL, 2008)
    m = pts.groupby("year")["val"].mean()
    assert m.loc[2009] > m.loc[2008] > m.loc[2010]


def test_year_from_harvest_date(setup):
    coords, _, _ = setup
    pts = summary_to_points(_summary(coords, with_harvest=True), VALUE_COL, None)
    assert sorted(pts["year"].unique()) == YEARS


def test_year_falls_back_to_season(setup):
    coords, _, _ = setup
    pts = summary_to_points(_summary(coords, with_harvest=False), VALUE_COL, 2008)
    assert sorted(pts["year"].unique()) == YEARS


def test_year_undeterminable_raises(setup):
    coords, _, _ = setup
    summ = [d.drop(columns=["Season"])
            for d in _summary(coords, with_harvest=False)]
    with pytest.raises(KeyError):
        summary_to_points(summ, VALUE_COL, None)


def test_summary_to_grid_has_year_dim(setup):
    coords, _, _ = setup
    assert summary_to_grid(_summary(coords), VALUE_COL, 2008).dims == \
        ("year", "y", "x")


# --------------------------------------------------------- scaling ----------

def test_scale_global_factor_differs_per_year(setup, tmp_path):
    coords, _, out = setup
    yf = {2008: 1.3, 2009: 0.8, 2010: 1.1}
    ref = tmp_path / "ref_yf.geojson"
    _write_reference(ref, coords, yf)
    cfg = _cfg(str(ref), out, scale_mode="global")
    r = run_correction(FakeProcessor(cfg, {}, LOG), _summary(coords), coords)
    for yr in YEARS:
        assert float(r["factor"].loc[yr]) == pytest.approx(yf[yr], rel=1e-6)


def test_scale_output_grid_and_county_table(setup):
    coords, ref, out = setup
    cfg = _cfg(ref, out, scale_mode="global")
    r = run_correction(FakeProcessor(cfg, {}, LOG), _summary(coords), coords)
    assert r["corrected"].dims == ("year", "y", "x")
    saved = xr.open_dataarray(Path(out) / "yield_scaled.nc")
    assert list(saved["year"].values) == YEARS
    assert (Path(out) / "yield_scaled_regions.csv").exists()
    assert {"year", "region_id", "model", "ref", "weight"} <= set(
        r["county_table"].columns)


def test_scale_local_factor_per_county(setup, tmp_path):
    coords, _, out = setup
    ref = tmp_path / "ref_l.geojson"
    _write_reference(ref, coords, {2008: 1.3, 2009: 0.8, 2010: 1.1})
    cfg = _cfg(str(ref), out, scale_mode="local")
    r = run_correction(FakeProcessor(cfg, {}, LOG), _summary(coords), coords)
    assert list(r["stats_per_year"].index) == YEARS
    assert r["stats"]["rmse"] == pytest.approx(0.0, abs=1e-9)


def test_off_returns_none(setup):
    coords, _, out = setup
    p = FakeProcessor({"correction": None, "output_dir": out}, {}, LOG)
    assert run_correction(p, _summary(coords), coords) is None


# --------------------------------------------------------- calibration ------

def test_calibration_override_empty_for_scale(setup):
    coords, ref, out = setup
    assert calibration_override(_cfg(ref, out), FakeProcessor, {}, coords,
                                LOG) == {}


def test_calibration_override_returns_parameter(setup):
    coords, ref, out = setup
    cfg = _cfg(ref, out, method="calibrate", lever="canopy", search_sample=40)
    over = calibration_override(cfg, FakeProcessor, {}, coords, LOG)
    assert over["crop_param_override"]["CCx"] == pytest.approx(0.70, abs=0.02)


def test_calibration_uses_exactly_one_full_run(setup):
    coords, ref, out = setup
    CountingProcessor.calls = {"full": 0, "search": 0}
    CountingProcessor.n_full_total = len(coords)
    cfg = _cfg(ref, out, method="calibrate", lever="canopy", search_sample=40)
    cfg.update(calibration_override(cfg, CountingProcessor, {}, coords, LOG))
    proc = CountingProcessor(cfg, {}, LOG)
    summary_results, _ = proc.run_parallel(coords)
    result = run_correction(proc, summary_results, coords)
    assert CountingProcessor.calls["full"] == 1
    assert CountingProcessor.calls["search"] > 1
    assert result["value"] == pytest.approx(0.70, abs=0.02)
    assert list(result["stats_per_year"].index) == YEARS


def test_run_correction_reports_without_researching(setup):
    coords, ref, out = setup
    CountingProcessor.calls = {"full": 0, "search": 0}
    CountingProcessor.n_full_total = len(coords)
    cfg = _cfg(ref, out, method="calibrate", lever="canopy", search_sample=40)
    cfg["crop_param_override"] = {"CCx": 0.70}
    proc = CountingProcessor(cfg, {}, LOG)
    r = run_correction(proc, _summary(coords, scale=1.0), coords)
    assert CountingProcessor.calls == {"full": 0, "search": 0}
    assert r["value"] == pytest.approx(0.70)


# --------------------------------------------------------- reuse ------------

def _save_summary(out_dir, summary, stamp="20260807_120000"):
    path = Path(out_dir) / f"summary_results_{stamp}.pkl"
    with open(path, "wb") as f:
        pickle.dump(summary, f, pickle.HIGHEST_PROTOCOL)
    return path


def test_should_reuse_flags(setup):
    coords, ref, out = setup
    assert should_reuse(_cfg(ref, out)) is False
    assert should_reuse(_cfg(ref, out, reuse_results="latest")) is True
    assert should_reuse({"output_dir": out,
                         "correction": {"method": None}}) is False


def test_find_latest_summary_picks_newest(setup):
    coords, _, out = setup
    _save_summary(out, _summary(coords), stamp="20260101_000000")
    newest = _save_summary(out, _summary(coords), stamp="20260807_235959")
    assert find_latest_summary(out) == newest


def test_find_latest_summary_raises_when_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_latest_summary(tmp_path)


def test_load_saved_summary_roundtrip(setup):
    coords, ref, out = setup
    _save_summary(out, _summary(coords))
    loaded = load_saved_summary(_cfg(ref, out, reuse_results="latest"), LOG)
    assert VALUE_COL in loaded[0].columns


def test_correct_saved_run_per_year_no_simulation(setup, tmp_path):
    coords, _, out = setup
    yf = {2008: 1.3, 2009: 0.8, 2010: 1.1}
    ref = tmp_path / "ref_reuse.geojson"
    _write_reference(ref, coords, yf)
    _save_summary(out, _summary(coords))
    cfg = _cfg(str(ref), out, scale_mode="global", reuse_results="latest")
    r = correct_saved_run(cfg, logger=LOG)
    for yr in YEARS:
        assert float(r["factor"].loc[yr]) == pytest.approx(yf[yr], rel=1e-6)
    assert (Path(out) / "yield_scaled.nc").exists()


def test_correct_saved_run_returns_none_when_off(setup):
    coords, _, out = setup
    _save_summary(out, _summary(coords))
    assert correct_saved_run({"output_dir": out,
                              "correction": {"method": None}}, logger=LOG) is None
