"""
visual_check.py — eyeball the gridded yield correction on synthetic data.
Not a test; a quick visual sanity check. Produces:
  * scaling: model / reference / corrected / residual maps (global + local), and
  * calibration: the search response curve and the post-calibration residual map.
Figures are shown and saved to ./viz/.

Run:  python visual_check.py
In real use the calibration grid_runner re-runs aquacropgrid with the lever
parameter overridden; here it's a synthetic monotonic response so the script is
self-contained.
"""
import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from yield_correction import (scale_to_reference, calibrate_to_reference,
                              LEVERS)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viz")
NF, COARSEN = 48, 6


def _fine(scale=1.0):
    lat = np.linspace(0, 1, NF); lon = np.linspace(0, 1, NF)
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    data = scale * (5 + 3 * yy + 2 * xx + 0.8 * np.sin(8 * xx) * np.cos(6 * yy))
    return xr.DataArray(data, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"))


def _block_mean(src, target=None):
    return src.coarsen(lat=COARSEN, lon=COARSEN, boundary="trim").mean()


def _imshow(ax, da, title, **kw):
    im = ax.pcolormesh(da["lon"], da["lat"], da.values, shading="auto", **kw)
    ax.set_title(title, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def scaling_figure():
    model = _fine()
    # reference: a spatially varying low bias vs the model (what we correct toward)
    ref_base = _block_mean(model)
    lat = ref_base["lat"]
    bias = 0.7 + 0.5 * (lat - lat.min()) / (lat.max() - lat.min())   # 0.7..1.2
    reference = ref_base * bias

    g = scale_to_reference(model, reference, mode="global", regrid=_block_mean)
    l = scale_to_reference(model, reference, mode="local", regrid=_block_mean)

    fig, ax = plt.subplots(2, 3, figsize=(12, 7))
    fig.suptitle("Gridded yield bias-correction (scaling)", fontweight="bold")
    ymax = float(model.max())
    _imshow(ax[0, 0], model, "model (sim grid)", vmin=0, vmax=ymax, cmap="viridis")
    _imshow(ax[0, 1], reference, "reference (coarse)", vmin=0, vmax=ymax, cmap="viridis")
    _imshow(ax[0, 2], g["corrected"], f"corrected: global x{g['factor_mean']:.3f}",
            vmin=0, vmax=ymax, cmap="viridis")
    rlim_g = float(abs(g["residual_on_reference"]).max()) or 1.0
    rlim_l = float(abs(l["residual_on_reference"]).max()) or 1e-12
    _imshow(ax[1, 0], g["residual_on_reference"],
            f"global residual (rmse={g['stats']['rmse']:.3f})",
            vmin=-rlim_g, vmax=rlim_g, cmap="RdBu_r")
    _imshow(ax[1, 1], l["factor"], "local factor field", cmap="magma")
    _imshow(ax[1, 2], l["residual_on_reference"],
            f"local residual (rmse={l['stats']['rmse']:.2e})",
            vmin=-rlim_l, vmax=rlim_l, cmap="RdBu_r")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def calibration_figure():
    model = _fine()
    TRUE = 0.65
    lever = "canopy"

    def grid_runner(p):                       # concave, monotonic (CCx-like)
        return model * np.sqrt(p / TRUE)

    reference = _block_mean(grid_runner(TRUE))     # 'observed' aggregate yield
    res = calibrate_to_reference(grid_runner, reference, lever=lever,
                                 regrid=_block_mean)

    lo, hi = LEVERS[lever]["bounds"]
    ps = np.linspace(lo, hi, 25)
    agg = [float(_block_mean(grid_runner(p)).mean()) for p in ps]
    target = float(reference.mean())

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(f"Calibration: {lever} via {res['parameter']} "
                 f"(recovered {res['value']:.3f}, true {TRUE})", fontweight="bold")
    ax[0].plot(ps, agg, "-o", ms=3, color="#1565c0", label="mean modelled yield")
    ax[0].axhline(target, ls=":", color="k", label="reference (target)")
    ax[0].axvline(res["value"], ls="--", color="#ef6c00", label="recovered value")
    ax[0].set_xlabel(res["parameter"]); ax[0].set_ylabel("aggregate yield")
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.25)
    ax[0].set_title("search response curve", fontsize=9)
    rlim = float(abs(res["residual_on_reference"]).max()) or 1.0
    _imshow(ax[1], res["residual_on_reference"],
            f"residual at reference scale (rmse={res['stats']['rmse']:.2e})",
            vmin=-rlim, vmax=rlim, cmap="RdBu_r")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig


def main():
    os.makedirs(OUT, exist_ok=True)
    f1, f2 = scaling_figure(), calibration_figure()
    f1.savefig(os.path.join(OUT, "scaling.png"), dpi=130, bbox_inches="tight")
    f2.savefig(os.path.join(OUT, "calibration.png"), dpi=130, bbox_inches="tight")
    print(f"saved figures to {OUT}")
    plt.show()


if __name__ == "__main__":
    main()
