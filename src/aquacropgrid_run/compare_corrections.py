"""
compare_corrections.py — inspect real correction outputs at REGION scale, per
year.

Takes the NetCDFs written by calibration and scaling runs (plus the region
reference, and optionally the uncorrected run's summary pickle) and produces:

  1. maps_<year>.png    per year: the reference on its region polygons, and
                        each run's yield on the simulation grid -- each shown
                        at its own native support, shared colour scale.
  2. differences.png    region-polygon difference maps (model - reference),
                        rows = years, columns = runs, shared diverging scale,
                        plus per-year difference histograms.
  3. timeseries.png     area-weighted domain mean per year for the reference
                        and each run.
  4. stats.csv + a printed table: per year and overall, per run.

Model grids are aggregated UP to the reference's regions (area-weighted), the
same operation the corrections use. Nothing is averaged over years.

Run from the Spyder console::

    from geoaquacrop_sim.compare_corrections import main
    main([
        "--reference", "reference/high_plains_maize_reference.geojson",
        "--calibrated", "outputs/yield_calibrated.nc",
        "--scaled", "outputs/yield_scaled.nc",
        "--summary", "outputs/summary_results_20260807_120000.pkl",
        "--out-dir", "outputs/comparison",
    ])

Only --reference is required; supply whichever runs you have.
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

from .correction import load_reference, summary_to_points
from .yield_correction import (aggregate_to_regions, region_assignment,
                               join_reference, fit_stats, grid_to_points,
                               points_to_grid)


# --------------------------------------------------------- loading ----------

def load_grid(path):
    """Load a (year, y, x) yield grid from NetCDF."""
    ds = xr.open_dataset(str(path))
    names = list(ds.data_vars)
    if len(names) != 1:
        raise ValueError(f"{path} holds {len(names)} variables {names}")
    da = ds[names[0]]
    if "year" not in da.dims:
        raise ValueError(f"{path} has no 'year' dimension; corrections are "
                         f"per-year, so re-run with the current code.")
    return da


def load_summary_points(path, value_col, start_year=None):
    with open(path, "rb") as f:
        summary_results = pickle.load(f)
    return summary_to_points(summary_results, value_col, start_year)


# --------------------------------------------------------- plotting ---------

def _grid_map(ax, da2d, title, **kw):
    im = ax.pcolormesh(da2d["x"], da2d["y"], da2d.values, shading="auto", **kw)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)
    return im


def _county_map(ax, gdf, column, title, **kw):
    gdf.plot(column=column, ax=ax, legend=False, **kw)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)


def maps_figure(year, reference_gdf, ref_col, runs, units="t/ha"):
    """Reference on region polygons; each run on the simulation grid."""
    vals = [reference_gdf[ref_col].dropna().to_numpy()]
    for _, g in runs:
        v = g.sel(year=year).values
        vals.append(v[np.isfinite(v)].ravel())
    allv = np.concatenate([v for v in vals if v.size])
    vmin, vmax = np.percentile(allv, [2, 98])

    n = 1 + len(runs)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.8), squeeze=False)
    fig.suptitle(f"Yield {year} — reference at region support, "
                 f"model on the simulation grid (shared colour scale)",
                 fontweight="bold")
    _county_map(axes[0][0], reference_gdf, ref_col, f"reference {year}",
                cmap="YlGn", vmin=vmin, vmax=vmax,
                missing_kwds={"color": "#eeeeee"})
    im = None
    for ax, (label, g) in zip(axes[0][1:], runs):
        im = _grid_map(ax, g.sel(year=year), f"{label} {year}",
                       vmin=vmin, vmax=vmax, cmap="YlGn")
    if im is not None:
        fig.colorbar(im, ax=axes[0].tolist(), fraction=0.025, pad=0.02,
                     label=f"yield ({units})")
    return fig


def differences_figure(years, regions, diff_tables, units="t/ha"):
    """Region-polygon difference maps: rows = years, columns = runs."""
    allv = np.concatenate([t["residual"].to_numpy(float)
                           for t in diff_tables.values()])
    lim = float(np.percentile(np.abs(allv), 98)) or 1.0
    labels = list(diff_tables)
    ncol = len(labels)
    fig, axes = plt.subplots(len(years), ncol + 1,
                             figsize=(4.2 * ncol + 5.0, 4.2 * len(years)),
                             squeeze=False, gridspec_kw={"wspace": 0.4})
    fig.suptitle("Difference from reference (model \u2212 reference) at region "
                 "scale, per year", fontweight="bold")
    for i, yr in enumerate(years):
        for j, label in enumerate(labels):
            t = diff_tables[label]
            sub = t[t["year"] == yr]
            gdf = regions.merge(sub[["region_id", "residual"]], on="region_id",
                                 how="left")
            st = sub["residual"]
            w = sub["weight"].to_numpy(float)
            rmse = np.sqrt(np.sum(w * st.to_numpy(float) ** 2) / np.sum(w)) \
                if len(sub) else np.nan
            bias = np.sum(w * st.to_numpy(float)) / np.sum(w) if len(sub) else np.nan
            _county_map(axes[i][j], gdf, "residual",
                        f"{label} {yr}\nbias={bias:+.2f}, RMSE={rmse:.2f}",
                        cmap="RdBu_r", vmin=-lim, vmax=lim,
                        missing_kwds={"color": "#eeeeee"})
        axh = axes[i][ncol]
        for label in labels:
            t = diff_tables[label]
            v = t.loc[t["year"] == yr, "residual"].to_numpy(float)
            if v.size:
                axh.hist(v, bins=30, histtype="step", lw=1.5, label=label)
        axh.axvline(0, color="k", lw=0.8)
        axh.set_title(f"differences {yr}", fontsize=9)
        axh.set_xlabel(f"model \u2212 reference ({units})", fontsize=8)
        axh.set_ylabel("regions", fontsize=8)
        axh.tick_params(labelsize=7)
        axh.legend(fontsize=7)
        axh.grid(alpha=0.25)
    sm = plt.cm.ScalarMappable(cmap="RdBu_r",
                               norm=plt.Normalize(vmin=-lim, vmax=lim))
    fig.colorbar(sm, ax=[axes[i][j] for i in range(len(years))
                         for j in range(ncol)],
                 fraction=0.015, pad=0.015, label=f"difference ({units})")
    return fig


def timeseries_figure(series, units="t/ha"):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.set_title("Area-weighted domain mean yield per year (region scale)",
                 fontweight="bold")
    for label, s in series:
        style = "k--o" if label == "reference" else "-o"
        ax.plot(s.index.to_numpy(), s.to_numpy(), style, ms=5, lw=1.7,
                label=label)
    ax.set_xlabel("year")
    ax.set_ylabel(f"mean yield ({units})")
    ax.set_xticks(series[0][1].index.to_numpy())
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


# --------------------------------------------------------- driver -----------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compare per-year calibrated / scaled correction outputs "
                    "against the region reference.")
    ap.add_argument("--reference", required=True,
                    help="region reference (GeoJSON/GPKG) from build_reference.py")
    ap.add_argument("--calibrated", default=None)
    ap.add_argument("--scaled", default=None)
    ap.add_argument("--summary", default=None,
                    help="summary_results_*.pkl for the UNCORRECTED baseline")
    ap.add_argument("--value-col", default="Dry yield (tonne/ha)")
    ap.add_argument("--start-year", type=int, default=None)
    ap.add_argument("--units", default="t/ha")
    ap.add_argument("--out-dir", default="comparison")
    args = ap.parse_args(argv)

    regions, reference = load_reference({"reference_path": args.reference})

    runs = []            # (label, grid DataArray)
    if args.summary:
        pts = load_summary_points(args.summary, args.value_col, args.start_year)
        runs.append(("uncorrected", points_to_grid(pts)))
    if args.calibrated:
        runs.append(("calibrated", load_grid(args.calibrated)))
    if args.scaled:
        runs.append(("scaled", load_grid(args.scaled)))
    if not runs:
        ap.error("supply at least one of --calibrated / --scaled / --summary")

    years = sorted(reference["year"].unique().tolist())

    # one cell->region assignment, reused for every run
    assignment = region_assignment(grid_to_points(runs[0][1]), regions)

    diff_tables, stats_rows, series = {}, [], []
    ref_by_year = reference.groupby("year").apply(
        lambda s: np.average(s["ref"]), include_groups=False)
    series.append(("reference", ref_by_year))

    for label, grid in runs:
        table = join_reference(aggregate_to_regions(grid, assignment),
                               reference)
        table["residual"] = table["model"] - table["ref"]
        diff_tables[label] = table
        st = fit_stats(table)
        for yr, row in st["per_year"].iterrows():
            stats_rows.append({"run": label, "year": int(yr), **row.to_dict()})
        stats_rows.append({"run": label, "year": "all", **st["overall"]})
        series.append((label, table.groupby("year").apply(
            lambda s: np.average(s["model"], weights=s["weight"]),
            include_groups=False)))

    table_out = pd.DataFrame(stats_rows)
    print(f"\nReference: {args.reference}  ({len(regions)} regions, "
          f"{len(years)} years)\n")
    print(f"{'run':<14}{'year':>6}{'regions':>10}{'bias':>10}{'MAE':>10}{'RMSE':>10}")
    print("-" * 60)
    for _, r in table_out.iterrows():
        print(f"{r['run']:<14}{str(r['year']):>6}{int(r['n']):>10}"
              f"{r['bias']:>10.3f}{r['mae']:>10.3f}{r['rmse']:>10.3f}")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table_out.to_csv(out / "stats.csv", index=False)

    written = []
    for yr in years:
        ref_gdf = regions.merge(
            reference.loc[reference["year"] == yr, ["region_id", "ref"]],
            on="region_id", how="left")
        fig = maps_figure(yr, ref_gdf, "ref", runs, args.units)
        p = out / f"maps_{yr}.png"
        fig.savefig(p, dpi=130, bbox_inches="tight")
        written.append(p)

    fd = differences_figure(years, regions, diff_tables, args.units)
    fd.savefig(out / "differences.png", dpi=130, bbox_inches="tight")
    written.append(out / "differences.png")

    ft = timeseries_figure(series, args.units)
    ft.savefig(out / "timeseries.png", dpi=130, bbox_inches="tight")
    written.append(out / "timeseries.png")

    print(f"\nWritten to {out}:")
    for p in written:
        print(f"  {p.name}")
    print("  stats.csv")
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
