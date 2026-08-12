"""
compare_corrections.py — visually inspect real correction outputs.

Takes the NetCDFs written by calibration and scaling runs (plus the reference
dataset, and optionally the uncorrected run's summary pickle) and produces:

  1. maps.png         basic yield maps: reference, uncorrected, calibrated,
                      scaled -- all on a shared colour scale, so output
                      patterns are directly comparable.
  2. differences.png  difference maps (model - reference) at the reference
                      scale for each corrected run, on a shared diverging
                      scale, plus a histogram of the differences.
  3. a printed stats table (n, bias, MAE, RMSE) for each run.

Usage (from the repo root, env active):

  python -m aquacropgrid_run.compare_corrections \\
      --reference reference/high_plains_maize_reference.nc \\
      --reference-var maize_yield_dry_tha \\
      --calibrated outputs/yield_calibrated.nc \\
      --scaled outputs/yield_scaled.nc \\
      --summary outputs/summary_results_20260807_120000.pkl \\
      --out-dir outputs/comparison

Only --reference is required; supply whichever of --calibrated / --scaled /
--summary you have. NOTE: both correction modes default to writing
'yield_corrected.nc', so set a distinct correction.output_name per run (e.g.
'yield_calibrated.nc', 'yield_scaled.nc') or rename the files before comparing.
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from .correction import _to_yx, summary_to_grid


# --------------------------------------------------------- loading ----------

def load_grid(path, var=None):
    """Load a yield grid from NetCDF as a (y, x) DataArray."""
    path = str(path)
    if var:
        da = xr.open_dataset(path)[var]
    else:
        ds = xr.open_dataset(path)
        names = [v for v in ds.data_vars]
        if len(names) != 1:
            raise ValueError(
                f"{path} holds {len(names)} variables {names}; "
                f"pass the one to use explicitly")
        da = ds[names[0]]
    return _to_yx(da.squeeze(drop=True))


def load_summary_grid(path, value_col="Dry yield (tonne/ha)"):
    """Uncorrected model yield grid from a saved summary_results_*.pkl."""
    with open(path, "rb") as f:
        summary_results = pickle.load(f)
    return _to_yx(summary_to_grid(summary_results, value_col))


# --------------------------------------------------------- comparison -------

def to_reference(model, reference, method="linear"):
    """Put a model grid on the reference grid for differencing."""
    return model.interp_like(reference, method=method)


def stats(model_on_ref, reference):
    m = np.asarray(model_on_ref.values, float).ravel()
    r = np.asarray(reference.values, float).ravel()
    ok = np.isfinite(m) & np.isfinite(r)
    m, r = m[ok], r[ok]
    if m.size == 0:
        return {"n": 0, "bias": np.nan, "mae": np.nan, "rmse": np.nan}
    d = m - r
    return {"n": int(m.size), "bias": float(d.mean()),
            "mae": float(np.abs(d).mean()),
            "rmse": float(np.sqrt((d ** 2).mean()))}


# --------------------------------------------------------- plotting ---------

def _map(ax, da, title, **kw):
    im = ax.pcolormesh(da["x"], da["y"], da.values, shading="auto", **kw)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("lon", fontsize=8)
    ax.set_ylabel("lat", fontsize=8)
    ax.tick_params(labelsize=7)
    return im


def maps_figure(layers, units="t/ha"):
    """layers: list of (label, DataArray). Shared colour scale across panels."""
    finite = np.concatenate([d.values[np.isfinite(d.values)].ravel()
                             for _, d in layers])
    vmin, vmax = np.percentile(finite, [2, 98])
    n = len(layers)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.6), squeeze=False)
    fig.suptitle("Yield patterns (shared colour scale)", fontweight="bold")
    for ax, (label, da) in zip(axes[0], layers):
        im = _map(ax, da, label, vmin=vmin, vmax=vmax, cmap="YlGn")
    fig.colorbar(im, ax=axes[0].tolist(), fraction=0.025, pad=0.02,
                 label=f"yield ({units})")
    return fig


def differences_figure(diffs, units="t/ha"):
    """diffs: list of (label, difference DataArray on the reference grid, stats)."""
    finite = np.concatenate([d.values[np.isfinite(d.values)].ravel()
                             for _, d, _ in diffs])
    lim = float(np.percentile(np.abs(finite), 98)) or 1.0
    n = len(diffs)
    fig, axes = plt.subplots(1, n + 1, figsize=(4.2 * n + 5.2, 4.6),
                             squeeze=False,
                             gridspec_kw={"wspace": 0.45})
    fig.suptitle("Difference from reference (model \u2212 reference, "
                 "at reference scale)", fontweight="bold")
    im = None
    for ax, (label, da, st) in zip(axes[0], diffs):
        im = _map(ax, da,
                  f"{label}\nbias={st['bias']:+.2f}, RMSE={st['rmse']:.2f} {units}",
                  vmin=-lim, vmax=lim, cmap="RdBu_r")
    if im is not None:
        fig.colorbar(im, ax=axes[0][:n].tolist(), fraction=0.025, pad=0.015,
                     label=f"difference ({units})")

    axh = axes[0][n]
    for label, da, _ in diffs:
        v = da.values[np.isfinite(da.values)].ravel()
        axh.hist(v, bins=40, histtype="step", lw=1.6, label=label)
    axh.axvline(0, color="k", lw=0.8)
    axh.set_title("distribution of differences", fontsize=9)
    axh.set_xlabel(f"model \u2212 reference ({units})", fontsize=8)
    axh.set_ylabel("reference cells", fontsize=8)
    axh.tick_params(labelsize=7)
    axh.legend(fontsize=7)
    axh.grid(alpha=0.25)
    return fig


# --------------------------------------------------------- driver -----------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compare calibrated / scaled correction outputs against "
                    "the reference dataset.")
    ap.add_argument("--reference", required=True,
                    help="reference yield NetCDF")
    ap.add_argument("--reference-var", default=None,
                    help="variable name inside the reference file")
    ap.add_argument("--calibrated", default=None,
                    help="NetCDF written by a method='calibrate' run")
    ap.add_argument("--scaled", default=None,
                    help="NetCDF written by a method='scale' run")
    ap.add_argument("--summary", default=None,
                    help="summary_results_*.pkl for the UNCORRECTED baseline")
    ap.add_argument("--value-col", default="Dry yield (tonne/ha)",
                    help="yield column in the summary pickle")
    ap.add_argument("--regrid", default="linear", choices=["linear", "nearest"],
                    help="how to put model grids on the reference grid")
    ap.add_argument("--units", default="t/ha", help="label for colour bars")
    ap.add_argument("--out-dir", default="comparison",
                    help="directory for the PNGs")
    args = ap.parse_args(argv)

    reference = load_grid(args.reference, args.reference_var)

    runs = []                                   # (label, grid, corrected?)
    if args.summary:
        runs.append(("uncorrected", load_summary_grid(args.summary,
                                                      args.value_col), False))
    if args.calibrated:
        runs.append(("calibrated", load_grid(args.calibrated), True))
    if args.scaled:
        runs.append(("scaled", load_grid(args.scaled), True))
    if not runs:
        ap.error("supply at least one of --calibrated / --scaled / --summary")

    # ---- stats table ----
    rows, diffs = [], []
    for label, grid, _ in runs:
        on_ref = to_reference(grid, reference, args.regrid)
        st = stats(on_ref, reference)
        rows.append((label, st))
        diffs.append((label, (on_ref - reference), st))

    print(f"\nReference: {args.reference}"
          f"  ({reference.sizes.get('y')} x {reference.sizes.get('x')} cells)")
    print(f"{'run':<14}{'n':>7}{'bias':>10}{'MAE':>10}{'RMSE':>10}")
    print("-" * 51)
    for label, st in rows:
        print(f"{label:<14}{st['n']:>7}{st['bias']:>10.3f}"
              f"{st['mae']:>10.3f}{st['rmse']:>10.3f}")
    best = min((r for r in rows if np.isfinite(r[1]["rmse"])),
               key=lambda r: r[1]["rmse"], default=None)
    if best:
        print(f"\nLowest RMSE: {best[0]}")

    # ---- figures ----
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    layers = [("reference", reference)] + [(l, g) for l, g, _ in runs]
    f1 = maps_figure(layers, args.units)
    f1.savefig(out / "maps.png", dpi=130, bbox_inches="tight")

    f2 = differences_figure(diffs, args.units)
    f2.savefig(out / "differences.png", dpi=130, bbox_inches="tight")

    print(f"Figures written to {out}/maps.png and {out}/differences.png")
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())