"""
build_reference.py — build a gridded maize-yield reference for the High Plains
from county polygons + county yields + the High Plains boundary, in the format
aquacropgrid-run's correction expects: an (lat, lon) NetCDF DataArray of dry
yield in t/ha.

Sits in reference/ and reads three inputs from reference/high_plains/:
    cb_2018_us_county_500k.shp   US county boundaries (has 5-digit GEOID)
    usda_nass_*.csv              USDA NASS county maize yields, 2008-2010
    high_plains.shp              High Plains region boundary

Output: reference/high_plains_maize_reference.nc

Averages county yields over the run years, joins to county polygons by FIPS,
lays a regular lat/lon grid over the region, assigns each cell the yield of the
county it falls in, masks to the region, converts to dry t/ha, saves.

Deps: geopandas, xarray, numpy, pandas.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr

# =============================== CONFIG =====================================
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "high_plains"
OUTPUT = HERE / "high_plains_maize_reference.nc"

YEARS = (2008, 2010)          # inclusive; averaged to one value per county
RESOLUTION_DEG = 0.1          # reference grid cell size (coarse is fine)

# Column names. None = auto-detect; set explicitly to override.
COUNTY_FIPS_COL = None        # 5-digit county FIPS/GEOID in the county file
CSV_FIPS_COL = None           # single 5-digit FIPS in the csv, IF it has one
CSV_STATE_COL = None          # else: 2-digit state code   (NASS 'State ANSI')
CSV_COUNTY_COL = None         # and:  3-digit county code  (NASS 'County ANSI')
CSV_YEAR_COL = None
CSV_VALUE_COL = None          # yield value column         (NASS 'Value')

# Units: USDA county maize is bushels/acre at 15.5% moisture; AquaCrop yield is
# dry matter (t/ha). Convert bu/ac -> wet t/ha -> dry t/ha. Set False if your
# csv is already dry t/ha.
CONVERT_BUSHELS_TO_DRY_THA = True
BU_AC_TO_T_HA = 0.0627        # maize, 56 lb/bu at 15.5% moisture, per acre->ha
GRAIN_MOISTURE = 0.155        # remove to reach dry matter
# ============================================================================

# NB: do NOT put name columns ('State'/'County') here — those are names, not a
# county FIPS. The single-FIPS path is only for a genuine 5-digit code column.
_FIPS_CANDS = ["GEOID", "FIPS", "fips", "GEOID10", "STCOFIPS", "geoid"]
_YEAR_CANDS = ["Year", "year", "YEAR"]
_VALUE_CANDS = ["Value", "value", "yield", "Yield", "YIELD", "VALUE"]
_STATE_CANDS = ["State ANSI", "state_fips_code", "state_ansi", "STATEFP"]
_COUNTY_CANDS = ["County ANSI", "county_ansi", "county_code", "COUNTYFP"]


def _pick(cols, override, candidates, what):
    if override:
        return override
    for c in candidates:
        if c in cols:
            print(f"  auto-detected {what}: '{c}'")
            return c
    return None


def _find(pattern):
    hits = sorted(DATA_DIR.glob(f"*{pattern}"))
    if not hits:
        raise FileNotFoundError(f"no file matching *{pattern} in {DATA_DIR}")
    if len(hits) > 1:
        print(f"  note: multiple *{pattern} files, using {hits[0].name}")
    return hits[0]


def main():
    print("Inputs:")
    county_path = _find("county_500k.shp")
    csv_path = _find(".csv")
    hp_path = _find("plains.shp")
    print(f"  counties: {county_path.name}\n  yields:   {csv_path.name}"
          f"\n  region:   {hp_path.name}")

    # --- counties ---
    counties = gpd.read_file(county_path).to_crs(4326)
    cfips = _pick(counties.columns, COUNTY_FIPS_COL, _FIPS_CANDS, "county FIPS")
    if cfips is None:
        raise KeyError(f"set COUNTY_FIPS_COL; columns are {list(counties.columns)}")
    counties[cfips] = counties[cfips].astype(str).str.zfill(5)

    # --- yields ---
    ydf = pd.read_csv(csv_path)
    if "Geo Level" in ydf.columns:                 # NASS: keep county rows only
        ydf = ydf[ydf["Geo Level"].astype(str).str.upper() == "COUNTY"]

    yfips = _pick(ydf.columns, CSV_FIPS_COL, _FIPS_CANDS, "csv FIPS")
    if yfips is None:
        st = _pick(ydf.columns, CSV_STATE_COL, _STATE_CANDS, "csv state code")
        co = _pick(ydf.columns, CSV_COUNTY_COL, _COUNTY_CANDS, "csv county code")
        if st is None or co is None:
            raise KeyError("set CSV_FIPS_COL (or CSV_STATE_COL + CSV_COUNTY_COL); "
                           f"columns are {list(ydf.columns)}")
        # County ANSI is float with NaN for aggregate rows -> drop, then combine
        ydf = ydf.dropna(subset=[st, co])
        ydf["_FIPS"] = (ydf[st].astype(int).astype(str).str.zfill(2)
                        + ydf[co].astype(int).astype(str).str.zfill(3))
        yfips = "_FIPS"
    else:
        ydf[yfips] = ydf[yfips].astype(str).str.zfill(5)

    ycol = _pick(ydf.columns, CSV_VALUE_COL, _VALUE_CANDS, "yield value")
    yrcol = _pick(ydf.columns, CSV_YEAR_COL, _YEAR_CANDS, "year")
    if ycol is None:
        raise KeyError(f"set CSV_VALUE_COL; columns are {list(ydf.columns)}")
    ydf[ycol] = pd.to_numeric(ydf[ycol], errors="coerce")
    if yrcol is not None:
        ydf = ydf[ydf[yrcol].astype(int).between(*YEARS)]
    yield_by_fips = ydf.groupby(yfips)[ycol].mean()
    print(f"Counties with yield data: {yield_by_fips.notna().sum()}")

    counties["yield_ref"] = counties[cfips].map(yield_by_fips)
    matched = counties["yield_ref"].notna().sum()
    print(f"County polygons matched to a yield: {matched}")

    # --- High Plains region ---
    hp = gpd.read_file(hp_path).to_crs(4326)
    hp_geom = hp.union_all() if hasattr(hp, "union_all") else hp.unary_union

    # --- regular lat/lon grid over the region bbox ---
    minx, miny, maxx, maxy = hp.total_bounds
    r = RESOLUTION_DEG
    lons = np.arange(minx + r / 2, maxx, r)
    lats = np.arange(miny + r / 2, maxy, r)
    XX, YY = np.meshgrid(lons, lats)                       # (nlat, nlon)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(XX.ravel(), YY.ravel()),
                           crs=4326)

    inside = pts.within(hp_geom).values                    # region mask
    pts_in = pts[inside]

    joined = gpd.sjoin(pts_in, counties[[cfips, "yield_ref", "geometry"]],
                       how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")].reindex(pts_in.index)

    grid = np.full(XX.size, np.nan)
    grid[np.where(inside)[0]] = joined["yield_ref"].values
    grid = grid.reshape(XX.shape)

    if CONVERT_BUSHELS_TO_DRY_THA:
        grid = grid * BU_AC_TO_T_HA * (1 - GRAIN_MOISTURE)

    da = xr.DataArray(grid, coords={"lat": lats, "lon": lons},
                      dims=("lat", "lon"), name="maize_yield_dry_tha")
    da.attrs.update(units="t/ha (dry matter)", crop="maize",
                    years=f"{YEARS[0]}-{YEARS[1]}", source=csv_path.name)
    da.to_netcdf(OUTPUT)

    filled = int(np.isfinite(grid).sum())
    finite = grid[np.isfinite(grid)]
    print(f"\nGrid: {da.sizes['lat']} x {da.sizes['lon']} cells, {filled} filled")
    if finite.size:
        print(f"Yield (dry t/ha): min {finite.min():.2f}, "
              f"mean {finite.mean():.2f}, max {finite.max():.2f}")
    else:
        print("WARNING: all cells NaN — check the FIPS join above (matched count).")
    print(f"Saved -> {OUTPUT}")
    print("Point correction.reference_path at this file "
          "(reference_var='maize_yield_dry_tha').")


if __name__ == "__main__":
    main()