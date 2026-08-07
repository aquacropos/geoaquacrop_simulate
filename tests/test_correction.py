"""
Unit tests for correction (config-driven orchestration). Fast and
deterministic: synthetic per-cell summaries and a fake processor whose yield
responds monotonically to the crop-parameter override, so no real AquaCrop runs.

Run:  pytest test_correction.py
"""
import logging

import numpy as np
import pandas as pd
import pytest

xr = pytest.importorskip("xarray")

from aquacropgrid_run.correction import (run_correction, normalise_correction,
                                         summary_to_grid, points_to_reference,
                                         summary_to_points)

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
