"""
yield_correction.py — rough, optional adjustment of gridded AquaCrop yield
toward a reference dataset, for the aquacropgrid simulation distro.

Two modes, both deliberately approximate (this is "close enough", not formal
estimation):

  scale_to_reference(model, reference, ...)
      Bias-correction. Multiply modelled yield by a factor (single global
      factor, or one per reference cell) so it matches the reference. Pure
      post-processing -- no re-run.

  calibrate_to_reference(grid_runner, reference, lever=..., ...)
      Vary ONE growth parameter by a quick 1-D golden-section search until the
      modelled yield matches the reference. One lever at a time:
          lever="canopy"  -> CCx  (maximum canopy cover)
          lever="biomass" -> WP   (normalised water productivity)

Lever choice (measured, not assumed): dry yield responds monotonically and
smoothly to CCx and linearly to WP, so both are reliable. CGC (canopy growth
*rate*) is deliberately NOT offered -- yield is insensitive to it once canopy
reaches CCx before season end. Harvest index is excluded as the least
realistic lever.

Grids: the simulation grid (fine) and the reference grid (usually coarser) need
not match. The functions regrid the model onto the reference grid to compute
the correction and report residuals AT THE REFERENCE SCALE, while returning the
corrected field on the original simulation grid. Default regridding is bilinear
(rough, universal); pass your own `regrid` (e.g. a conservative/area-mean
regridder) for strongly mismatched grids.

Everything operates on xarray.DataArrays with lat/lon-like dims. No aquacrop
imports here: calibration takes a `grid_runner` callback you wire to your own
aquacropgrid run function.
"""
import numpy as np

try:
    import xarray as xr
except ImportError:                       # keeps import cheap if xarray absent
    xr = None


# lever -> controlling crop parameter and a rough search range
LEVERS = {
    "canopy":  {"parameter": "CCx", "bounds": (0.30, 0.99)},
    "biomass": {"parameter": "WP",  "bounds": (5.0, 40.0)},
}


# --------------------------------------------------------- grid helpers -----

def regrid_to(source, target, method="linear"):
    """Put `source` on `target`'s grid. Default bilinear interpolation, which
    works whether the target is finer or coarser. For a strongly coarser
    reference, an area-mean/conservative regridder is more correct -- pass it
    via the `regrid=` argument of the functions below."""
    return source.interp_like(target, method=method)


def _stats(model_on_ref, reference):
    """Goodness-of-fit at the reference scale."""
    m = np.asarray(model_on_ref.values, dtype=float).ravel()
    r = np.asarray(reference.values, dtype=float).ravel()
    ok = np.isfinite(m) & np.isfinite(r)
    m, r = m[ok], r[ok]
    if m.size == 0:
        return {"n": 0, "bias": np.nan, "rmse": np.nan, "mae": np.nan}
    return {"n": int(m.size),
            "bias": float(np.mean(m - r)),
            "rmse": float(np.sqrt(np.mean((m - r) ** 2))),
            "mae": float(np.mean(np.abs(m - r)))}


# --------------------------------------------------------- scaling ----------

def scale_to_reference(model, reference, mode="global", regrid=regrid_to):
    """Bias-correct gridded yield toward `reference`.

    mode="global"  one multiplicative factor = sum(reference)/sum(model) over
                   the overlap, applied to the whole simulation grid.
    mode="local"   one factor per reference cell (reference/model), broadcast
                   back onto the simulation grid.

    Returns a dict with the corrected field on the simulation grid, the factor
    (scalar or field), the residuals on the reference grid, and fit stats.
    """
    m_on_ref = regrid(model, reference)
    mask = np.isfinite(m_on_ref) & np.isfinite(reference)

    if mode == "global":
        denom = float(m_on_ref.where(mask).sum())
        factor = float(reference.where(mask).sum() / denom) if denom != 0 else 1.0
        corrected = model * factor
        factor_out, factor_mean = factor, factor
    elif mode == "local":
        factor_field = (reference / m_on_ref).where(mask)
        # broadcast each reference-cell factor onto the fine grid; reindex
        # (not interp) so edge cells clamp to the nearest cell instead of NaN
        f_fine = factor_field.reindex_like(model, method="nearest")
        corrected = model * f_fine
        factor_out = factor_field
        factor_mean = float(np.nanmean(factor_field.values))
    else:
        raise ValueError("mode must be 'global' or 'local'")

    corr_on_ref = regrid(corrected, reference)
    residual = (corr_on_ref - reference).where(mask)
    return {"factor": factor_out,
            "factor_mean": factor_mean,
            "corrected": corrected,
            "model_on_reference": m_on_ref,
            "residual_on_reference": residual,
            "stats": _stats(corr_on_ref.where(mask), reference.where(mask))}


# --------------------------------------------------------- calibration ------

def _golden(f, a, b, tol, max_iter):
    """Efficient golden-section minimisation of unimodal f on [a,b]
    (one new evaluation per iteration)."""
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


def calibrate_to_reference(grid_runner, reference, lever="canopy", bounds=None,
                           tol=1e-3, max_iter=20, regrid=regrid_to):
    """Vary one growth parameter so gridded yield matches `reference`.

    grid_runner(value) -> xr.DataArray of yield on the simulation grid, run with
    the lever's crop parameter set to `value` (applied across the grid). Keep
    the run light during search (short period / subsampled cells) since this is
    called once per iteration; apply the returned value to the full grid after.

    Returns the best parameter value, the calibrated yield field, residuals on
    the reference grid, and fit stats.
    """
    if lever not in LEVERS:
        raise ValueError(f"lever must be one of {list(LEVERS)}")
    spec = LEVERS[lever]
    lo, hi = bounds if bounds is not None else spec["bounds"]

    def sse(p):
        m_on_ref = regrid(grid_runner(p), reference)
        mask = np.isfinite(m_on_ref) & np.isfinite(reference)
        d = (m_on_ref - reference).where(mask)
        return float((d ** 2).sum())

    best = _golden(sse, lo, hi, tol * (hi - lo), max_iter)
    model = grid_runner(best)
    m_on_ref = regrid(model, reference)
    mask = np.isfinite(m_on_ref) & np.isfinite(reference)
    residual = (m_on_ref - reference).where(mask)
    return {"lever": lever,
            "parameter": spec["parameter"],
            "value": float(best),
            "model": model,
            "model_on_reference": m_on_ref,
            "residual_on_reference": residual,
            "stats": _stats(m_on_ref.where(mask), reference.where(mask))}
