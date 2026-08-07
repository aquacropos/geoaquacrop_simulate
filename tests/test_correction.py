"""
Unit tests for correction (config-driven orchestration). Fast and
deterministic: synthetic per-cell summaries and a fake processor whose yield
responds monotonically to the crop-parameter override, so no real AquaCrop runs.

Run:  pytest test_correction.py
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")

from aquacropgrid_run.correction import (run_correction, normalise_correction,
                                         summary_to_grid, points_to_reference,
                                         summary_to_points, should_reuse,
                                         calibration_override,
                                         correct_saved_run, find_latest_summary,
                                         load_saved_summary)

LOG = logging.getLogger("test"); LOG.addHandler(logging.NullHandler())


# --------------------------------------------------------- fixtures ---------

def _coords(n=12):
    xs = np.linspace(0, 1, n); ys = np.linspace(0, 1, n)
    return pd.DataFrame([(x, y) for y in ys for x in xs], columns=["x", "y"])


def _summary(coords, ccx=0.7):
    """Per-cell final_stats-like frames; yield linear in ccx, 3 seasons/cell."""
    rows = []
    for _, r in coords.iterrows():
        base = 5 + 2 * r.y + 1.5 * r.x
        for s in range(3):
            rows.append({"x": r.x, "y": r.y,
                         "Dry yield (tonne/ha)": base * (ccx / 0.7) + 0.01 * s})
    return [pd.DataFrame(rows)]


class FakeProcessor:
    def __init__(self, config, validated_inputs, logger):
        self.config, self.validated_inputs, self.logger = config, validated_inputs, logger

    def run_parallel(self, coords_df):
        ccx = self.config.get("crop_param_override", {}).get("CCx", 0.7)
        return _summary(coords_df, ccx), None


@pytest.fixture
def setup(tmp_path):
    coords = _coords()
    reference = summary_to_grid(_summary(coords, 0.7)).coarsen(
        y=3, x=3, boundary="trim").mean()
    ref_path = tmp_path / "ref.nc"
    reference.to_netcdf(ref_path)
    return coords, str(ref_path), str(tmp_path)


# --------------------------------------------------------- config -----------

def test_normalise_off():
    assert normalise_correction(None) is None
    assert normalise_correction({"method": None}) is None


def test_normalise_requires_reference():
    with pytest.raises(ValueError):
        normalise_correction({"method": "scale"})


def test_normalise_bad_method():
    with pytest.raises(ValueError):
        normalise_correction({"method": "wat", "reference_path": "x.nc"})


def test_off_returns_none(setup):
    coords, _, out = setup
    p = FakeProcessor({"correction": None, "output_dir": out}, {}, LOG)
    assert run_correction(p, _summary(coords), coords) is None


# --------------------------------------------------------- scaling ----------

def test_scale_global_recovers_factor(setup):
    coords, ref, out = setup
    cfg = {"correction": {"method": "scale", "reference_path": ref,
                          "scale_mode": "global", "output_name": "s.nc"},
           "output_dir": out}
    p = FakeProcessor(cfg, {}, LOG)
    r = run_correction(p, _summary(coords, ccx=0.91), coords)   # model 1.3x high
    assert r["factor_mean"] == pytest.approx(0.7 / 0.91, rel=0.02)


def test_scale_local_near_exact(setup):
    coords, ref, out = setup
    cfg = {"correction": {"method": "scale", "reference_path": ref,
                          "scale_mode": "local", "output_name": "l.nc"},
           "output_dir": out}
    p = FakeProcessor(cfg, {}, LOG)
    r = run_correction(p, _summary(coords, ccx=0.91), coords)
    assert r["stats"]["rmse"] < 1e-6


# --------------------------------------------------------- calibration ------

def test_calibrate_recovers_parameter(setup):
    coords, ref, out = setup
    cfg = {"correction": {"method": "calibrate", "reference_path": ref,
                          "lever": "canopy", "search_sample": 40,
                          "output_name": "c.nc"},
           "output_dir": out, "crop": "Maize"}
    p = FakeProcessor(cfg, {}, LOG)
    r = run_correction(p, _summary(coords, ccx=0.96), coords)   # biased baseline
    assert r["parameter"] == "CCx"
    assert r["value"] == pytest.approx(0.70, abs=0.02)


def test_calibrate_writes_output(setup):
    import os
    coords, ref, out = setup
    cfg = {"correction": {"method": "calibrate", "reference_path": ref,
                          "lever": "biomass", "search_sample": 30,
                          "output_name": "cal.nc"},
           "output_dir": out}
    p = FakeProcessor(cfg, {}, LOG)
    run_correction(p, _summary(coords, 0.8), coords)
    assert os.path.exists(os.path.join(out, "cal.nc"))


# --------------------------------------------------------- helpers ----------

def test_points_to_reference_handles_subsample(setup):
    coords, ref, _ = setup
    reference = xr.open_dataarray(ref)
    sub = _coords().sample(20, random_state=1)
    pts = summary_to_points(_summary(sub, 0.7), "Dry yield (tonne/ha)")
    m_ref = points_to_reference(pts, reference)
    # aggregation lands on the reference grid, some cells populated
    assert m_ref.dims == ("y", "x")
    assert np.isfinite(m_ref.values).any()


# --------------------------------------------------------- reuse flag -------
# correction.reuse_results scales an already-saved run without re-simulating.
# A FakeProcessor here would mask a regression: these tests must fail if the
# reuse path ever calls run_parallel, so no simulation stand-in is provided.

def _save_summary(out_dir, summary, stamp="20260807_120000"):
    """Write a summary pickle the way ParallelProcessor.save_results does."""
    import pickle
    path = Path(out_dir) / f"summary_results_{stamp}.pkl"
    with open(path, "wb") as f:
        pickle.dump(summary, f, pickle.HIGHEST_PROTOCOL)
    return path


def _reuse_cfg(ref, out, **over):
    corr = {"method": "scale", "reference_path": ref, "scale_mode": "local",
            "reuse_results": "latest", "output_name": "reused.nc"}
    corr.update(over)
    return {"output_dir": out, "correction": corr}


def test_should_reuse_false_by_default(setup):
    _, ref, out = setup
    assert should_reuse({"output_dir": out,
                         "correction": {"method": "scale",
                                        "reference_path": ref}}) is False


def test_should_reuse_false_when_correction_off(setup):
    _, _, out = setup
    assert should_reuse({"output_dir": out, "correction": {"method": None}}) is False
    assert should_reuse({"output_dir": out}) is False


def test_should_reuse_true_when_flag_set(setup):
    _, ref, out = setup
    assert should_reuse(_reuse_cfg(ref, out)) is True


def test_calibrate_plus_reuse_rejected(setup):
    _, ref, _ = setup
    with pytest.raises(ValueError, match="reuse_results"):
        normalise_correction({"method": "calibrate", "reference_path": ref,
                              "lever": "canopy", "reuse_results": "latest"})


def test_find_latest_summary_picks_newest(setup, tmp_path):
    coords, _, out = setup
    _save_summary(out, _summary(coords), stamp="20260101_000000")
    newest = _save_summary(out, _summary(coords), stamp="20260807_235959")
    assert find_latest_summary(out) == newest


def test_find_latest_summary_raises_when_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_latest_summary(tmp_path)


def test_load_saved_summary_roundtrip(setup):
    coords, ref, out = setup
    _save_summary(out, _summary(coords, ccx=0.91))
    loaded = load_saved_summary(_reuse_cfg(ref, out), LOG)
    assert isinstance(loaded, list)
    assert "Dry yield (tonne/ha)" in loaded[0].columns


def test_correct_saved_run_recovers_factor(setup):
    """Global scaling of a saved, deliberately biased run recovers the factor
    with no simulation at all."""
    coords, ref, out = setup
    _save_summary(out, _summary(coords, ccx=0.91))          # model 1.3x high
    r = correct_saved_run(_reuse_cfg(ref, out, scale_mode="global"), logger=LOG)
    assert r["factor_mean"] == pytest.approx(0.7 / 0.91, rel=0.02)


def test_correct_saved_run_local_and_writes_output(setup):
    import os
    coords, ref, out = setup
    _save_summary(out, _summary(coords, ccx=0.91))
    r = correct_saved_run(_reuse_cfg(ref, out), logger=LOG)
    assert r["stats"]["rmse"] < 1e-6
    assert os.path.exists(os.path.join(out, "reused.nc"))


def test_correct_saved_run_explicit_path(setup):
    coords, ref, out = setup
    path = _save_summary(out, _summary(coords, ccx=0.91))
    r = correct_saved_run(_reuse_cfg(ref, out, reuse_results=str(path)), logger=LOG)
    assert r["factor_mean"] == pytest.approx(0.7 / 0.91, rel=0.02)


def test_correct_saved_run_returns_none_when_off(setup):
    coords, _, out = setup
    _save_summary(out, _summary(coords))
    assert correct_saved_run({"output_dir": out,
                              "correction": {"method": None}}, logger=LOG) is None


# ------------------------------------------- calibration runs search first ---
# The search must happen BEFORE the full simulation so the expensive full-grid
# run happens exactly once, with the calibrated parameter already applied.

class CountingProcessor(FakeProcessor):
    """Records how many full-grid vs subsample run_parallel calls happen."""
    calls = None          # set to {"full": 0, "search": 0} by the test

    def __init__(self, config, validated_inputs, logger, n_full=None):
        super().__init__(config, validated_inputs, logger)
        self.n_full = n_full

    def run_parallel(self, coords_df):
        n_full = self.n_full or type(self).n_full_total
        key = "full" if len(coords_df) == n_full else "search"
        type(self).calls[key] += 1
        return super().run_parallel(coords_df)


def test_calibration_override_empty_for_scale(setup):
    coords, ref, out = setup
    cfg = {"output_dir": out,
           "correction": {"method": "scale", "reference_path": ref}}
    assert calibration_override(cfg, FakeProcessor, {}, coords, LOG) == {}


def test_calibration_override_empty_when_off(setup):
    coords, _, out = setup
    assert calibration_override({"output_dir": out,
                                 "correction": {"method": None}},
                                FakeProcessor, {}, coords, LOG) == {}


def test_calibration_override_returns_parameter(setup):
    coords, ref, out = setup
    cfg = {"output_dir": out,
           "correction": {"method": "calibrate", "reference_path": ref,
                          "lever": "canopy", "search_sample": 30}}
    over = calibration_override(cfg, FakeProcessor, {}, coords, LOG)
    assert set(over) == {"crop_param_override"}
    assert over["crop_param_override"]["CCx"] == pytest.approx(0.70, abs=0.02)


def test_calibration_uses_exactly_one_full_run(setup):
    """The whole point of phase-1: search on a subsample, then ONE full run."""
    coords, ref, out = setup
    CountingProcessor.calls = {"full": 0, "search": 0}
    CountingProcessor.n_full_total = len(coords)
    cfg = {"output_dir": out,
           "correction": {"method": "calibrate", "reference_path": ref,
                          "lever": "canopy", "search_sample": 30,
                          "output_name": "phase1.nc"}}
    # mirror run_aquacrop.main(): search first, then the single full run
    cfg.update(calibration_override(cfg, CountingProcessor, {}, coords, LOG))
    proc = CountingProcessor(cfg, {}, LOG)
    summary_results, _ = proc.run_parallel(coords)
    result = run_correction(proc, summary_results, coords)

    assert CountingProcessor.calls["full"] == 1
    assert CountingProcessor.calls["search"] > 1          # the search happened
    assert result["value"] == pytest.approx(0.70, abs=0.02)


def test_run_correction_reports_without_researching(setup):
    """With crop_param_override already set, run_correction must NOT re-search:
    it reports on the supplied summary only."""
    coords, ref, out = setup
    CountingProcessor.calls = {"full": 0, "search": 0}
    CountingProcessor.n_full_total = len(coords)
    cfg = {"output_dir": out,
           "correction": {"method": "calibrate", "reference_path": ref,
                          "lever": "canopy", "search_sample": 30,
                          "output_name": "reportonly.nc"},
           "crop_param_override": {"CCx": 0.70}}
    proc = CountingProcessor(cfg, {}, LOG)
    result = run_correction(proc, _summary(coords, ccx=0.70), coords)
    assert CountingProcessor.calls == {"full": 0, "search": 0}   # no re-running
    assert result["value"] == pytest.approx(0.70)
    assert result["stats"]["rmse"] < 1e-6