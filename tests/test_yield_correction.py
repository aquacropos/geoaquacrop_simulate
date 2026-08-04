"""
Unit tests for yield_correction (gridded bias-correction + rough calibration).

Fast and deterministic: synthetic xarray grids and a fake grid_runner, so no
real AquaCrop runs. Run with:  pytest test_yield_correction.py
"""
import numpy as np
import pytest
import sys

xr = pytest.importorskip("xarray")

sys.path.insert(0, "../src/aquacropgrid_run")

from yield_correction import (scale_to_reference, calibrate_to_reference,
                              regrid_to, LEVERS)

NF = 24          # fine grid size
COARSEN = 4      # fine cells per reference cell  -> 6x6 reference


# --------------------------------------------------------- fixtures ---------

def _fine_field(scale=1.0):
    """Smooth positive yield-like field on a fine lat/lon grid."""
    lat = np.linspace(0, 1, NF)
    lon = np.linspace(0, 1, NF)
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    data = scale * (5.0 + 2.0 * yy + 1.5 * xx + 0.5 * np.sin(6 * xx))
    return xr.DataArray(data, coords={"lat": lat, "lon": lon},
                        dims=("lat", "lon"))


def _block_mean(source, target=None):
    """Area-mean regridder used in tests for exact recovery (coarsen by COARSEN)."""
    return source.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()


@pytest.fixture
def model():
    return _fine_field()


# --------------------------------------------------------- scaling ----------

def test_scale_global_recovers_known_factor(model):
    factor_true = 1.3
    reference = _block_mean(model) * factor_true
    out = scale_to_reference(model, reference, mode="global", regrid=_block_mean)
    assert out["factor_mean"] == pytest.approx(factor_true, rel=1e-6)
    assert out["stats"]["rmse"] == pytest.approx(0.0, abs=1e-9)


def test_scale_local_beats_global(model):
    # strongly varying truth: factor ranges ~0.6..1.6 across reference cells
    ref_base = _block_mean(model)
    lat = ref_base["lat"]
    factor_field = 0.6 + 1.0 * (lat - lat.min()) / (lat.max() - lat.min())
    reference = ref_base * factor_field
    local = scale_to_reference(model, reference, mode="local", regrid=_block_mean)
    glob = scale_to_reference(model, reference, mode="global", regrid=_block_mean)
    # per-cell scaling should track a varying reference far better than one factor
    assert local["stats"]["rmse"] < glob["stats"]["rmse"]
    assert local["stats"]["rmse"] < 0.02 * float(reference.mean())


def test_scale_default_regrid_runs(model):
    # the default bilinear regridder should also produce a sensible factor
    reference = _block_mean(model) * 1.2
    out = scale_to_reference(model, reference, mode="global")  # regrid=regrid_to
    assert out["factor_mean"] == pytest.approx(1.2, rel=0.05)


def test_scale_invalid_mode(model):
    with pytest.raises(ValueError):
        scale_to_reference(model, _block_mean(model), mode="nonsense")


# --------------------------------------------------------- calibration ------

def test_calibrate_recovers_parameter(model):
    """Fake runner with linear yield response (like WP); recover the true value."""
    true_value = 0.70

    def grid_runner(p):
        return model * (p / true_value)       # yield linear in parameter

    reference = _block_mean(grid_runner(true_value))   # 'observed' aggregate
    out = calibrate_to_reference(grid_runner, reference, lever="biomass",
                                 bounds=(0.3, 1.5), regrid=_block_mean)
    assert out["value"] == pytest.approx(true_value, abs=0.01)
    assert out["stats"]["rmse"] < 1e-2          # rough: search tol, not exact
    assert out["parameter"] == "WP"


def test_calibrate_concave_response(model):
    """Concave (saturating) response, like CCx -> yield; still recoverable."""
    true_value = 0.65

    def grid_runner(p):
        return model * np.sqrt(p / true_value)   # concave, monotonic

    reference = _block_mean(grid_runner(true_value))
    out = calibrate_to_reference(grid_runner, reference, lever="canopy",
                                 bounds=(0.30, 0.99), regrid=_block_mean)
    assert out["value"] == pytest.approx(true_value, abs=0.02)
    assert out["parameter"] == "CCx"


def test_calibrate_reduces_error(model):
    true_value = 0.55

    def grid_runner(p):
        return model * (p / true_value)

    reference = _block_mean(grid_runner(true_value))
    start = calibrate_to_reference(grid_runner, reference, lever="biomass",
                                   bounds=(0.3, 1.5), max_iter=0, regrid=_block_mean)
    tuned = calibrate_to_reference(grid_runner, reference, lever="biomass",
                                   bounds=(0.3, 1.5), regrid=_block_mean)
    assert tuned["stats"]["rmse"] <= start["stats"]["rmse"]


def test_calibrate_invalid_lever(model):
    with pytest.raises(ValueError):
        calibrate_to_reference(lambda p: model, _block_mean(model), lever="hi")


def test_levers_exclude_cgc_and_hi():
    # documented choice: only canopy(CCx) and biomass(WP) are offered
    assert set(LEVERS) == {"canopy", "biomass"}
    assert LEVERS["canopy"]["parameter"] == "CCx"
    assert LEVERS["biomass"]["parameter"] == "WP"
