"""
visual_check.py — sanity-check the correction MACHINERY on synthetic data where
the right answer is known. Not a test, and not for inspecting real runs (use
compare_corrections.py for that).

Confirms visually that:
  * the model is aggregated UP to region support, area-weighted;
  * per-year global scaling recovers a known per-year bias;
  * per-year local scaling removes per-region bias exactly;
  * calibration recovers a known parameter, and cannot fit years that need
    opposite corrections.

Figures are saved to ./viz/ and shown.

Run from the Spyder console:
    from geoaquacrop_sim.visual_check import main
    main()
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .yield_correction import (LEVERS, area_weights, region_assignment,
                               aggregate_to_regions, join_reference,
                               scale_to_reference, calibrate_to_reference)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viz")
YEARS = [2008, 2009, 2010]
YEAR_BIAS = {2008: 1.30, 2009: 0.80, 2010: 1.10}


def _counties():
    import geopandas as gpd
    from shapely.geometry import box
    polys, region_id = [], []
    for i in range(3):
        for j in range(3):
            polys.append(box(-101 + j, 39 + i, -100 + j, 40 + i))
            region_id.append(f"9{i}{j}00")
    return gpd.GeoDataFrame({"region_id": region_id}, geometry=polys, crs=4326)


def _points():
    lat = np.arange(39.05, 42.0, 0.1)
    lon = np.arange(-100.95, -98.0, 0.1)
    rows = []
    for i, yr in enumerate(YEARS):
        for yy in lat:
            for xx in lon:
                v = 6 + 1.5 * (yy - 39) + 0.8 * (xx + 101)
                rows.append({"year": yr, "y": yy, "x": xx,
                             "val": v * (1 + 0.05 * i)})
    return pd.DataFrame(rows)


def _reference(points, assignment, year_factor=None, spatial=False):
    agg = aggregate_to_regions(points, assignment)
    ref = agg[["year", "region_id", "model"]].rename(columns={"model": "ref"})
    if year_factor:
        ref = ref.assign(ref=ref["ref"] * ref["year"].map(year_factor))
    if spatial:                     # a north-south varying bias by region row
        bump = {f: 0.75 + 0.25 * int(f[1]) for f in ref["region_id"].unique()}
        ref = ref.assign(ref=ref["ref"] * ref["region_id"].map(bump))
    return ref


def scaling_figure(points, assignment, regions):
    ref = _reference(points, assignment, YEAR_BIAS, spatial=True)
    g = scale_to_reference(points, ref, assignment, mode="global")
    l = scale_to_reference(points, ref, assignment, mode="local")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    fig.suptitle("Per-year scaling at region support "
                 "(global recovers the year factor; local also removes the "
                 "per-region bias)", fontweight="bold")
    yrs = [int(y) for y in g["factor"].index]
    ax[0].plot(yrs, [float(g["factor"].loc[y]) for y in yrs], "-o",
               color="#1565c0", label="fitted global factor")
    ax[0].plot(yrs, [YEAR_BIAS[y] for y in yrs], "k--s", ms=5,
               label="truth (year component)")
    ax[0].set_xticks(yrs); ax[0].set_xlabel("year"); ax[0].set_ylabel("factor")
    ax[0].set_title("global factor, fitted per year", fontsize=9)
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.25)

    width = 0.35
    idx = np.arange(len(yrs))
    ax[1].bar(idx - width / 2, [g["stats_per_year"].loc[y, "rmse"] for y in yrs],
              width, label="global", color="#1565c0")
    ax[1].bar(idx + width / 2, [l["stats_per_year"].loc[y, "rmse"] for y in yrs],
              width, label="local", color="#ef6c00")
    ax[1].set_xticks(idx); ax[1].set_xticklabels(yrs)
    ax[1].set_title("region-scale RMSE by year "
                    "(local is exact by construction)", fontsize=9)
    ax[1].set_ylabel("RMSE"); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.25)
    fig.tight_layout(rect=[0, 0, 1, 0.9])

    print("Per-year global factors (year component of the truth in brackets):")
    for y in yrs:
        print(f"  {y}: {float(g['factor'].loc[y]):.4f}  [{YEAR_BIAS[y]:.2f} "
              f"x per-region bias]")
    return fig


def calibration_figure(points, assignment):
    TRUE, lever = 0.65, "canopy"
    ref = _reference(points, assignment)

    def runner(p):
        out = points.copy()
        out["val"] = out["val"] * np.sqrt(p / TRUE)      # concave, monotonic
        return out

    res = calibrate_to_reference(runner, ref, assignment, lever=lever)

    lo, hi = LEVERS[lever]["bounds"]
    ps = np.linspace(lo, hi, 21)
    agg = [float(aggregate_to_regions(runner(p), assignment)["model"].mean())
           for p in ps]

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(f"Calibration: {lever} via {res['parameter']} "
                 f"(recovered {res['value']:.3f}, true {TRUE}) — one value "
                 f"across {len(YEARS)} years", fontweight="bold")
    ax[0].plot(ps, agg, "-o", ms=3, color="#1565c0", label="region-mean yield")
    ax[0].axhline(float(ref["ref"].mean()), ls=":", color="k", label="reference")
    ax[0].axvline(res["value"], ls="--", color="#ef6c00", label="recovered")
    ax[0].set_xlabel(res["parameter"]); ax[0].set_ylabel("mean yield")
    ax[0].set_title("search response curve", fontsize=9)
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.25)

    per_year = res["stats_per_year"]
    ax[1].bar([str(y) for y in per_year.index], per_year["rmse"],
              color="#6a1b9a")
    ax[1].set_title("post-calibration region RMSE by year", fontsize=9)
    ax[1].set_ylabel("RMSE"); ax[1].grid(alpha=0.25)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    return fig


def weighting_figure():
    """Aggregation to a region is area-weighted, not a plain mean."""
    import geopandas as gpd
    from shapely.geometry import box
    poly = gpd.GeoDataFrame({"region_id": ["99999"]},
                            geometry=[box(-1, 0, 1, 70)], crs=4326)
    pts = pd.DataFrame({"year": [2008, 2008], "y": [20.0, 60.0],
                        "x": [0.0, 0.0], "val": [10.0, 20.0]})
    a = region_assignment(pts, poly)
    weighted = float(aggregate_to_regions(pts, a)["model"].iloc[0])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["area-weighted\n(used)", "plain mean\n(not used)"],
           [weighted, 15.0], color=["#2e7d32", "#9e9e9e"])
    for i, v in enumerate([weighted, 15.0]):
        ax.text(i, v + 0.15, f"{v:.3f}", ha="center", fontsize=9)
    ax.set_title("Aggregating 10 t/ha at 20\u00b0N with 20 t/ha at 60\u00b0N "
                 "into one region", fontweight="bold", fontsize=10)
    ax.set_ylabel("region value"); ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    print(f"\nArea-weighted region value: {weighted:.4f}  "
          f"(plain mean would be 15.0)")
    return fig


def main():
    os.makedirs(OUT, exist_ok=True)
    regions = _counties()
    points = _points()
    assignment = region_assignment(points, regions)
    print(f"{len(points[['y','x']].drop_duplicates())} simulation cells -> "
          f"{assignment['region_id'].nunique()} regions")

    figs = [("scaling", scaling_figure(points, assignment, regions)),
            ("calibration", calibration_figure(points, assignment)),
            ("area_weighting", weighting_figure())]
    for name, fig in figs:
        fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=130,
                    bbox_inches="tight")
    print(f"\nSaved figures to {OUT}")
    plt.show()


if __name__ == "__main__":
    main()
