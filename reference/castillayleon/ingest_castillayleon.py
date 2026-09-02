"""
ingest_castillayleon.py — turn the Junta de Castilla y León crop statistics
workbook into a tidy table the generic reference builder can consume.

Input : wheat_2024.xlsx (or the equivalent workbook for another crop), as
        published at https://agriculturaganaderia.jcyl.es
Output: castillayleon_wheat.csv with one row per province per year:

    region, year, area_ha, production_t, yield_t_ha,
    yield_rainfed_t_ha, yield_irrigated_t_ha

`yield_t_ha` is production / area, i.e. the blended rainfed+irrigated yield.
The split columns come from the "rendimientos en secano y regadío" sheet and let
you match the reference to a rainfed-only or irrigated-only model run.

Yields are converted from the published fresh weight at market moisture to DRY
MATTER, to match AquaCrop's "Dry yield (tonne/ha)". Set GRAIN_MOISTURE to 0 to
keep fresh weight.

Run:
    python ingest_castillayleon.py                 # uses the defaults below
    python ingest_castillayleon.py --help
"""
import argparse
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# Sheet names in the published workbook. Change these if the layout moves.
SHEET_AREA = "2.1.2.2"        # provincial area (ha), wide by province
SHEET_PRODUCTION = "2.1.2.3"  # provincial production (t), wide by province
SHEET_SPLIT = "2.1.2.6"       # provincial yields (kg/ha), secano / regadío

GRAIN_MOISTURE = 0.13         # wheat grain sold at ~13% moisture -> dry matter
REGION_TOTAL = "Castilla y León"   # aggregate row/column, excluded from output


def _clean(name):
    """Normalise a province label: strip, collapse spaces, drop accents for
    matching but keep the original spelling for output."""
    if name is None:
        return None
    s = " ".join(str(name).split())
    return s


def _key(name):
    """Accent- and case-insensitive key for joining to a boundary file."""
    s = _clean(name)
    if s is None:
        return None
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _year(cell):
    """Year from a cell that may carry a footnote marker, e.g. '2024*'."""
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    digits = "".join(c for c in str(cell) if c.isdigit())
    return int(digits) if len(digits) == 4 else None


def _read_wide(path, sheet, value_name):
    """Parse a 'year x province' sheet into long form [region, year, value]."""
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    # the header row is the one whose first cell is 'Años'
    hdr = raw.index[raw[0].astype(str).str.strip().str.lower() == "años"]
    if len(hdr) == 0:
        raise ValueError(f"sheet {sheet}: no 'Años' header row found")
    hdr = int(hdr[0])
    names = [_clean(v) for v in raw.iloc[hdr + 1].tolist()]
    rows = []
    for _, r in raw.iloc[hdr + 2:].iterrows():
        year = _year(r[0])
        if year is None:
            continue
        for col, region in enumerate(names):
            if col == 0 or not region or region == REGION_TOTAL:
                continue
            v = r[col]
            if pd.notna(v) and isinstance(v, (int, float)):
                rows.append({"region": region, "year": year,
                             value_name: float(v)})
    return pd.DataFrame(rows)


def _read_split(path, sheet):
    """Parse the secano/regadío yield sheet.

    The sheet holds two stacked blocks, each with a province label every second
    column and a Secano/Regadío pair beneath. Labels in the second block are
    partly corrupted by merged-cell artefacts, so the province names are taken
    from the columns that sit directly above a 'Secano' cell.
    """
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    rows = []
    for i in raw.index:
        vals = [str(v).strip().lower() if pd.notna(v) else "" for v in raw.iloc[i]]
        if "secano" not in vals:
            continue
        label_row = raw.iloc[i - 1]
        cols = [c for c, v in enumerate(vals) if v == "secano"]
        block = {}
        for c in cols:
            region = _clean(label_row[c])
            if region and region != REGION_TOTAL:
                block[region] = c
        # data rows run until the next blank/'Años' row
        for j in range(i + 1, len(raw)):
            year = _year(raw.iloc[j, 0])
            if year is None:
                if str(raw.iloc[j, 0]).strip().lower() == "años":
                    break
                continue
            for region, c in block.items():
                sec, reg = raw.iloc[j, c], raw.iloc[j, c + 1]
                rows.append({
                    "region": region, "year": year,
                    "yield_rainfed_kg_ha": float(sec) if pd.notna(sec) else np.nan,
                    "yield_irrigated_kg_ha": float(reg) if pd.notna(reg) else np.nan,
                })
    return pd.DataFrame(rows).drop_duplicates(subset=["region", "year"])


def build(path, out_csv, moisture=GRAIN_MOISTURE):
    area = _read_wide(path, SHEET_AREA, "area_ha")
    prod = _read_wide(path, SHEET_PRODUCTION, "production_t")
    split = _read_split(path, SHEET_SPLIT)

    # join on a normalised key: the sheets spell provinces inconsistently
    # ("Ávila" vs "Avila"), which silently drops rows if joined on the raw name
    for frame in (area, prod, split):
        frame["region_key"] = frame["region"].map(_key)
    df = area.merge(prod.drop(columns=["region"]), on=["region_key", "year"],
                    how="outer")
    df = df.merge(split.drop(columns=["region"]), on=["region_key", "year"],
                  how="left")
    df["region"] = df["region"].fillna(
        df["region_key"].str.title())

    dry = 1.0 - moisture
    df["yield_t_ha"] = (df["production_t"] / df["area_ha"]) * dry
    df["yield_rainfed_t_ha"] = df["yield_rainfed_kg_ha"] / 1000.0 * dry
    df["yield_irrigated_t_ha"] = df["yield_irrigated_kg_ha"] / 1000.0 * dry
    df = df[["region", "region_key", "year", "area_ha", "production_t",
             "yield_t_ha", "yield_rainfed_t_ha", "yield_irrigated_t_ha"]]
    df = df.sort_values(["region", "year"]).reset_index(drop=True)
    df.to_csv(out_csv, index=False)
    return df


def quality_report(df):
    """Flag provinces whose rainfed/irrigated split looks duplicated between
    columns in the source workbook, and years where the split is inconsistent
    with production / area."""
    print("\nQuality checks")
    print("-" * 62)

    # 1. identical rainfed series shared between two provinces
    piv = df.pivot_table(index="year", columns="region",
                         values="yield_rainfed_t_ha")
    dupes = []
    cols = list(piv.columns)
    for a in range(len(cols)):
        for b in range(a + 1, len(cols)):
            both = piv[[cols[a], cols[b]]].dropna()
            if len(both) >= 3 and np.allclose(both.iloc[:, 0], both.iloc[:, 1]):
                dupes.append((cols[a], cols[b], len(both)))
            elif len(both) >= 3:
                same = np.isclose(both.iloc[:, 0], both.iloc[:, 1]).sum()
                if same >= 3:
                    dupes.append((cols[a], cols[b], int(same)))
    if dupes:
        print("  Identical rainfed values shared between provinces "
              "(likely a copy error in the source workbook):")
        for a, b, n in dupes:
            print(f"    {a} == {b} in {n} year(s)")
        print("  -> prefer 'yield_t_ha' (production / area) for those provinces.")
    else:
        print("  No duplicated rainfed series detected.")

    # 2. blended yield should sit between the rainfed and irrigated values
    ok = df.dropna(subset=["yield_t_ha", "yield_rainfed_t_ha",
                           "yield_irrigated_t_ha"])
    lo = np.minimum(ok["yield_rainfed_t_ha"], ok["yield_irrigated_t_ha"])
    hi = np.maximum(ok["yield_rainfed_t_ha"], ok["yield_irrigated_t_ha"])
    bad = ok[(ok["yield_t_ha"] < lo - 0.05) | (ok["yield_t_ha"] > hi + 0.05)]
    print(f"  Blended yield outside the rainfed-irrigated range: "
          f"{len(bad)} of {len(ok)} province-years")
    if len(bad):
        for _, r in bad.head(5).iterrows():
            print(f"    {r['region']} {r['year']}: total={r['yield_t_ha']:.2f}, "
                  f"rainfed={r['yield_rainfed_t_ha']:.2f}, "
                  f"irrigated={r['yield_irrigated_t_ha']:.2f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--excel", default=str(HERE / "wheat_2024.xlsx"))
    ap.add_argument("--out", default=str(HERE / "castillayleon_wheat.csv"))
    ap.add_argument("--moisture", type=float, default=GRAIN_MOISTURE,
                    help="grain moisture fraction removed to reach dry matter "
                         "(0 keeps published fresh weight)")
    args = ap.parse_args(argv)

    df = build(args.excel, args.out, args.moisture)
    print(f"Parsed {df['region'].nunique()} provinces x "
          f"{df['year'].nunique()} years = {len(df)} rows")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")
    print(f"\nDry-matter yield (t/ha) summary by province:")
    s = df.groupby("region")["yield_t_ha"].agg(["min", "mean", "max"]).round(2)
    print(s.to_string())
    quality_report(df)
    print(f"\nSaved -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
