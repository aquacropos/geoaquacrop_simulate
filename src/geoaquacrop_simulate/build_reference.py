"""Build a per-year, region-level yield reference from ANY pair of:

  1. a boundary file  (shapefile / GeoJSON / GeoPackage) of the reporting
     regions -- counties, provinces, districts, whatever the statistics use;
  2. a statistics table (CSV / Excel) of yields per region per year.

The two are joined on a common column. Nothing else about the country, the
administrative level or the data source is assumed.

Output: a GeoJSON with one feature per region carrying

``region_id``
    The join key, as a string.
``yield_<year>``
    One field per year, in the units of the input table.

which is exactly what :func:`geoaquacrop_simulate.correction.load_reference`
expects.

Configure it either by editing the CONFIG block below and running the file, or
from the command line / Python::

    python -m geoaquacrop_simulate.build_reference \\
        --regions provinces.geojson --region-id NAME_LATN \\
        --table wheat_yields.csv --table-id region \\
        --year-col year --value-col yield_t_ha --out reference.geojson

    import geoaquacrop as gac

    gac.simulate.build_reference(
        regions='provinces.geojson', region_id='NAME_LATN',
        table='wheat_yields.csv', table_id='region',
        year_col='year', value_col='yield_t_ha', out='reference.geojson')

A worked example. Spanish provincial wheat yields, with the boundaries from a
provinces file whose names sit in ``NAME_LATN`` and a statistics table whose
rows are ``region, year, yield_rainfed_t_ha``::

    python -m geoaquacrop_simulate.build_reference \\
        --regions cyl_provinces.geojson --region-id NAME_LATN \\
        --table castillayleon_wheat.csv --table-id region \\
        --year-col year --value-col yield_rainfed_t_ha \\
        --out reference_castillayleon.geojson

Join keys are matched case-, accent- and whitespace-insensitively, so
"Ávila", "AVILA" and "avila " all match. Regions that fail to match are
reported explicitly rather than silently dropped -- an unmatched region is the
single most common reason for an all-NaN reference.

The yield values are written in whatever units the input table uses, so convert
to the units of the summary column being corrected (by default dry-matter
t/ha) before building, not after.

Needs the ``correction`` extra: ``pip install "geoaquacrop_simulate[correction]"``
for geopandas, plus openpyxl for .xlsx tables.
"""
import argparse
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# =============================== CONFIG =====================================
# Defaults used when the script is run with no arguments. Override any of them
# on the command line, or edit them here and run the file directly.
REGIONS = "regions.geojson"          # boundary file of the reporting regions
REGION_ID = "NAME_LATN"              # column in the boundary file holding the name/code
TABLE = "statistics.csv"             # statistics table (.csv or .xlsx)
TABLE_ID = "region"                  # column in the table holding the same name/code
YEAR_COL = "year"
VALUE_COL = "yield_t_ha"             # the yield column to use as the reference
OUT = "reference.geojson"
YEARS = None                         # None = every year in the table, or (first, last)
# ============================================================================


def _key(value):
    """Accent-, case- and whitespace-insensitive join key."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = " ".join(str(value).split())
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _read_table(path, sheet=None):
    path = str(path)
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path, sheet_name=sheet or 0)
    return pd.read_csv(path)


def _require(path, what, option):
    """Fail early and legibly when an input file is not where it was expected."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"{what} not found at '{path}'. Pass {option}, or edit the CONFIG "
            f"block at the top of build_reference.py. The defaults are "
            f"placeholders, not real files.")


def build(regions=REGIONS, region_id=REGION_ID, table=TABLE, table_id=TABLE_ID,
          year_col=YEAR_COL, value_col=VALUE_COL, out=OUT, years=YEARS,
          sheet=None, keep_unmatched=False, quiet=False):
    """Join a boundary file to a yield table and write the reference GeoJSON.

    Parameters
    ----------
    regions : str
        Path to the boundary file (any format geopandas can read).
    region_id : str
        Column in the boundary file used as the join key.
    table : str
        Path to the statistics table (.csv or .xlsx).
    table_id, year_col, value_col : str
        Columns in the table holding the join key, the year, and the yield.
    out : str
        Output GeoJSON path.
    years : tuple, optional
        ``(first, last)`` inclusive. Defaults to every year present.
    sheet : str, optional
        Sheet name when the table is an Excel workbook.
    keep_unmatched : bool
        Keep regions with no statistics (all-NaN fields) instead of dropping
        them. Useful for seeing the full domain on a map.
    quiet : bool
        Suppress the join report and the per-year summary.

    Returns
    -------
    geopandas.GeoDataFrame
        The reference, as written.

    Raises
    ------
    FileNotFoundError
        If either input file is missing.
    KeyError
        If a named column is not present in its file; the available columns
        are listed.
    ValueError
        If no region matches between the two files.
    """
    import geopandas as gpd

    say = (lambda *a: None) if quiet else print

    _require(regions, "Boundary file", "--regions")
    _require(table, "Statistics table", "--table")

    gdf = gpd.read_file(str(regions))
    if region_id not in gdf.columns:
        raise KeyError(f"'{region_id}' is not a column in {regions}. "
                       f"Available: {list(gdf.columns)}")
    if gdf.crs is None:
        say(f"  warning: {regions} has no CRS; assuming EPSG:4326")
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    df = _read_table(table, sheet)
    for col in (table_id, year_col, value_col):
        if col not in df.columns:
            raise KeyError(f"'{col}' is not a column in {table}. "
                           f"Available: {list(df.columns)}")

    df = df[[table_id, year_col, value_col]].copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[table_id, year_col])
    if years is not None:
        df = df[df[year_col].between(int(years[0]), int(years[1]))]

    gdf["_key"] = gdf[region_id].map(_key)
    df["_key"] = df[table_id].map(_key)

    # report the join before doing it -- silent mismatches are the usual failure
    g_keys, t_keys = set(gdf["_key"].dropna()), set(df["_key"].dropna())
    matched = g_keys & t_keys
    say(f"Regions in boundary file : {len(g_keys)}")
    say(f"Regions in yield table   : {len(t_keys)}")
    say(f"Matched                  : {len(matched)}")
    if g_keys - t_keys:
        say(f"  no statistics for: "
            f"{sorted(gdf.loc[gdf['_key'].isin(g_keys - t_keys), region_id].unique())}")
    if t_keys - g_keys:
        say(f"  no boundary for  : "
            f"{sorted(df.loc[df['_key'].isin(t_keys - g_keys), table_id].unique())}")
    if not matched:
        raise ValueError(
            "no regions matched. Check that --region-id and --table-id name "
            "the columns holding the SAME identifier (both names, or both "
            "codes) in the two files.")

    wide = df.pivot_table(index="_key", columns=year_col, values=value_col,
                          aggfunc="mean")
    year_list = [int(y) for y in wide.columns]
    for yr in year_list:
        gdf[f"yield_{yr}"] = gdf["_key"].map(wide[yr])

    gdf["region_id"] = gdf[region_id].astype(str)
    cols = ["region_id"] + [f"yield_{y}" for y in year_list] + ["geometry"]
    ref = gdf[cols]
    if not keep_unmatched:
        ref = ref[gdf["_key"].isin(matched)].reset_index(drop=True)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    ref.to_file(str(out), driver="GeoJSON")

    say(f"\n{'year':>6}{'regions':>9}{'min':>8}{'mean':>8}{'max':>8}")
    for yr in year_list:
        v = ref[f"yield_{yr}"].dropna()
        if len(v):
            say(f"{yr:>6}{len(v):>9}{v.min():>8.2f}{v.mean():>8.2f}{v.max():>8.2f}")
        else:
            say(f"{yr:>6}{0:>9}{'-':>8}{'-':>8}{'-':>8}")
    say(f"\nSaved -> {out}")
    say("Point reference_path at this file.")
    return ref


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="geoaquacrop_simulate.build_reference",
        description="Build a per-year, region-level yield reference from a "
                    "boundary file and a statistics table.")
    ap.add_argument("--regions", default=REGIONS)
    ap.add_argument("--region-id", default=REGION_ID)
    ap.add_argument("--table", default=TABLE)
    ap.add_argument("--table-id", default=TABLE_ID)
    ap.add_argument("--year-col", default=YEAR_COL)
    ap.add_argument("--value-col", default=VALUE_COL)
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--years", nargs=2, type=int, default=None,
                    metavar=("FIRST", "LAST"))
    ap.add_argument("--keep-unmatched", action="store_true")
    a = ap.parse_args(argv)
    build(a.regions, a.region_id, a.table, a.table_id, a.year_col,
          a.value_col, a.out, a.years, a.sheet, a.keep_unmatched)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
