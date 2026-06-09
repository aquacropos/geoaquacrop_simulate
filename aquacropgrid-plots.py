# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        USER CONFIGURATION                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

SUMMARY_PKL   = '../high_plains_package/outputs/summary_results_20260521_191549.pkl'    # simulation output files
DAILY_PKL     = '../high_plains_package/outputs/daily_results_20260521_191549.pkl'
GEOJSON_PATH  = '../high_plains_package/inputdata/high_plains/high_plains.geojson'  # polygon input file (area of interest)
PROCESSED_DIR = '../high_plains_package/processed'    # preprocessing outputs (climate, soil, phenology, crop areas)
EXPORT_DIR    = '../high_plains_package/outputs/exports'    # location to save data files via export function in visualisation (NetCDF, GeoTIFF, CSV)
CELL_RES      = 0.05 # same as the preprocessing grid resolution in degrees
PORT          = 8050
# MAP_ZOOM      = 10
MAP_HEIGHT    = 550
TS_HEIGHT     = 400

MAP_VARIABLES = {
    # ── Yield ──────────────────────────────────────────────────────────────────
    'Dry yield (tonne/ha)':                    {'label': 'Dry Yield (t/ha)',              'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    'Fresh yield (tonne/ha)':                  {'label': 'Fresh Yield (t/ha)',            'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    'Yield potential (tonne/ha)':              {'label': 'Yield Potential (t/ha)',        'colorscale': 'YlOrRd',  'sum_colorscale': 'OrRd',   'default_agg': 'mean'},
    # ── Production & area ──────────────────────────────────────────────────────
    'production_tonnes':                       {'label': 'Production (tonnes)',           'colorscale': 'YlOrBr',  'sum_colorscale': 'OrRd',   'default_agg': 'sum' },
    # ── Water ──────────────────────────────────────────────────────────────────
    'Seasonal irrigation (mm)':                {'label': 'Seasonal Irrigation (mm)',      'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'sum' },
    'seasonal_precip_mm':                      {'label': 'Seasonal Precip (mm)',          'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'seasonal_et_mm':                          {'label': 'Seasonal ET (mm)',              'colorscale': 'YlGnBu',  'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'seasonal_transpiration_mm':               {'label': 'Seasonal Transpiration (mm)',   'colorscale': 'YlGnBu',  'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    'total_water_input_mm':                    {'label': 'Total Water Input (mm)',        'colorscale': 'Blues',   'sum_colorscale': 'PuBuGn', 'default_agg': 'mean'},
    # ── Water productivity ─────────────────────────────────────────────────────
    'wp_et_kg_per_m3':                         {'label': 'WP-ET (kg/m³)',                 'colorscale': 'RdYlGn',  'sum_colorscale': 'YlGn',   'default_agg': 'mean'},
    'rainfall_use_efficiency_kg_per_m3':       {'label': 'Rainfall Use Efficiency (kg/m³)','colorscale': 'RdYlGn', 'sum_colorscale': 'YlGn',   'default_agg': 'mean'},
   }

DAILY_VARIABLES = {
    'Es':           {'label': 'Soil Evaporation (mm/day)',           'table': 'water_flux',  'color': '#e67e22'},
    'EsPot':        {'label': 'Potential Soil Evaporation (mm/day)', 'table': 'water_flux',  'color': '#f39c12'},
    'Tr':           {'label': 'Crop Transpiration (mm/day)',         'table': 'water_flux',  'color': '#2980b9'},
    'TrPot':        {'label': 'Potential Transpiration (mm/day)',    'table': 'water_flux',  'color': '#3498db'},
    'Infl':         {'label': 'Infiltration (mm/day)',               'table': 'water_flux',  'color': '#1abc9c'},
    'Runoff':       {'label': 'Runoff (mm/day)',                     'table': 'water_flux',  'color': '#e74c3c'},
    'DeepPerc':     {'label': 'Deep Percolation (mm/day)',           'table': 'water_flux',  'color': '#8e44ad'},
    'Wr':           {'label': 'Water in Root Zone (mm)',             'table': 'water_flux',  'color': '#2c3e50'},
    'biomass':      {'label': 'Biomass (tonne/ha)',                  'table': 'crop_growth', 'color': '#27ae60'},
    'canopy_cover': {'label': 'Canopy Cover (-)',                    'table': 'crop_growth', 'color': '#2ecc71'},
    'gdd_cum':      {'label': 'Cumulative GDD (°C·day)',            'table': 'crop_growth', 'color': '#d35400'},
    'z_root':       {'label': 'Root Depth (m)',                     'table': 'crop_growth', 'color': '#795548'},
    'DryYield':     {'label': 'Dry Yield (t/ha)',                   'table': 'crop_growth', 'color': '#c0392b'},
}

CLIMATE_VARIABLES = {
    'MaxTemp':       {'label': 'Max Temperature (°C)',    'map_label': 'Max Temperature (°C)',    'unit': '°C',      'color': '#e74c3c', 'colorscale': 'RdYlBu_r'},
    'MinTemp':       {'label': 'Min Temperature (°C)',    'map_label': 'Min Temperature (°C)',    'unit': '°C',      'color': '#3498db', 'colorscale': 'RdYlBu_r'},
    'Precipitation': {'label': 'Precipitation (mm/day)', 'map_label': 'Precipitation (mm/year)', 'unit': 'mm/year', 'color': '#2980b9', 'colorscale': 'Blues'   },
    'ReferenceET':   {'label': 'Reference ET (mm/day)',  'map_label': 'Reference ET (mm/year)',  'unit': 'mm/year', 'color': '#e67e22', 'colorscale': 'YlOrBr'  },
}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        IMPORTS & DATA LOADING                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# pickle      — built-in
# pandas      — data manipulation
# numpy       — array operations
# xarray      — NetCDF handling
# plotly      — pip install plotly
# dash        — pip install dash
# dash_bootstrap_components — pip install dash-bootstrap-components
# rasterio    — pip install rasterio  (for GeoTIFF export)
# json        — built-in

import pickle
import os
import pandas as pd
import numpy as np
import xarray as xr
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx, ALL, Patch
import json
import glob
import copy
import math
import dash_bootstrap_components as dbc

os.makedirs(EXPORT_DIR, exist_ok=True)

with open(GEOJSON_PATH) as f:
    region_geojson = json.load(f)

with open(SUMMARY_PKL, 'rb') as f:
    summary_raw = pickle.load(f)

frames = []
for item in summary_raw:
    if isinstance(item, pd.DataFrame):
        frames.append(item)
    elif isinstance(item, dict):
        frames.append(pd.DataFrame([item]))

summary = pd.concat(frames, ignore_index=True)
summary.columns = summary.columns.str.strip()
summary['harvest_year'] = pd.to_datetime(summary['Harvest Date (YYYY/MM/DD)']).dt.year
#summary['season_label'] = summary['harvest_year'].astype(str)
summary = summary.dropna(subset=['harvest_year'])
summary['season_label'] = summary['harvest_year'].astype(int).astype(str)
summary['crop_irr']     = summary['crop'] + ' | ' + summary['irrigation']

with open(DAILY_PKL, 'rb') as f:
    daily_raw = pickle.load(f)

cell_meta      = {}
cell_id_to_idx = {}


for i, df in enumerate(summary_raw):
    if not isinstance(df, pd.DataFrame) or df.empty or 'cell_id' not in df.columns:
        continue
    row = df.iloc[0]
    if pd.notna(row.get('error', None)):
        continue
    cid = int(row['cell_id'])
    cell_meta[cid] = {
        'x':          float(row['x']),
        'y':          float(row['y']),
        'crop':       row['crop'],
        'irrigation': row['irrigation'],
        'list_idx':   i,
    }
    cell_id_to_idx[cid] = i


# Precomputed arrays for vectorized xarray lookups (built once, reused everywhere)
_cell_ids_arr = np.array(list(cell_meta.keys()), dtype=int)
_cell_xs_arr  = np.array([cell_meta[c]['x'] for c in _cell_ids_arr])
_cell_ys_arr  = np.array([cell_meta[c]['y'] for c in _cell_ids_arr])
_x_da = xr.DataArray(_cell_xs_arr, dims='pts')
_y_da = xr.DataArray(_cell_ys_arr, dims='pts')

crop_irr_list    = sorted(summary['crop_irr'].dropna().unique())
season_list      = sorted(summary['season_label'].dropna().unique())
map_var_keys     = list(MAP_VARIABLES.keys())
daily_var_keys   = list(DAILY_VARIABLES.keys())
climate_var_keys = list(CLIMATE_VARIABLES.keys())

first_harvest_date = pd.to_datetime(summary_raw[0].iloc[0]['Harvest Date (YYYY/MM/DD)'])
first_harvest_step = int(summary_raw[0].iloc[0]['Harvest Date (Step)'])
sim_start          = first_harvest_date - pd.to_timedelta(first_harvest_step, unit='D')
sim_end            = sim_start + pd.to_timedelta(len(daily_raw[0]['water_flux']) - 1, unit='D')

n_rows     = len(daily_raw[0]['water_flux'])
date_index = pd.date_range(start=sim_start, periods=n_rows, freq='D')
years = [yr for yr in sorted(date_index.year.unique())
         if (date_index.year == yr).sum() > 5]

year_rows = {}
for yr in years:
    indices = np.where(date_index.year == yr)[0]
    year_rows[str(yr)] = (int(indices[0]), int(indices[-1]))

wf0 = daily_raw[0]['water_flux'].reset_index(drop=True)
preseason_end_row  = int(wf0[wf0['season_counter'] == -1.0].index.max())
preseason_end_date = sim_start + pd.to_timedelta(preseason_end_row, unit='D')


sim_year_start = years[0]
sim_year_end   = years[-1]
year_suffix    = f'{sim_year_start}{sim_year_end}'

climate_ds = {}
for var in climate_var_keys:
    path = os.path.join(PROCESSED_DIR, f'{var}{year_suffix}.nc')
    if os.path.exists(path):
        climate_ds[var] = xr.open_dataset(path)
    else:
        # Fallback: glob if exact filename not found
        matches = glob.glob(os.path.join(PROCESSED_DIR, f'{var}*.nc'))
        if matches:
            climate_ds[var] = xr.open_dataset(matches[0])

cropcal_ds = xr.open_dataset(os.path.join(PROCESSED_DIR, 'cropcalendar.nc'),
                             decode_timedelta=True)

# ── SPAM: load and keep only variables with data ───────────────────────────────
spam_files = glob.glob(os.path.join(PROCESSED_DIR, 'spam*_physical_area.nc'))
spam_path  = spam_files[0] if spam_files else None
spam_ds = xr.open_dataset(spam_path) if spam_path and os.path.exists(spam_path) else None

spam_var_keys = []  # all SPAM vars with data
if spam_ds is not None:
    for var in sorted(spam_ds.data_vars):
        if 'spatial_ref' in var:
            continue
        arr   = spam_ds[var].values.flatten().astype(float)
        valid = arr[(~np.isnan(arr)) & (arr > 0)]
        if len(valid) > 0:
            spam_var_keys.append(var)

def spam_vars_for_crop(crop_irr):
    crop_name = crop_irr.split(' | ')[0].capitalize()
    irr_code  = IRR_MAP.get(crop_irr.split(' | ')[1], crop_irr.split(' | ')[1])
    exact     = f'{crop_name}_{irr_code}_physical_area'
    if exact in spam_var_keys:
        return [exact]
    return []  

# ── Crop calendar helper ───────────────────────────────────────────────────────
IRR_MAP = {'rainfed': 'rf', 'irrigated': 'ir'}

def get_cropcal_summary(crop_irr):
    """Return planting date, season length, harvest date for a crop_irr string."""
    try:
        parts     = crop_irr.split(' | ')
        crop_name = parts[0].capitalize()
        irr_code  = IRR_MAP.get(parts[1], parts[1])
        plant_var = f'{crop_name}_{irr_code}_planting'
        gsl_var   = f'{crop_name}_{irr_code}_growing_season_length'

        if plant_var not in cropcal_ds.data_vars:
            return None

        doy_arr = cropcal_ds[plant_var].values.flatten().astype(float)
        valid   = doy_arr[(~np.isnan(doy_arr)) & (doy_arr > 0)]
        if len(valid) == 0:
            return None
        doy = int(valid[0])
        plant_str = (pd.Timestamp('2001-01-01') +
                     pd.to_timedelta(doy - 1, unit='D')).strftime('%b %d')

        gsl = None
        if gsl_var in cropcal_ds.data_vars:
            raw       = cropcal_ds[gsl_var].values.astype('timedelta64[ns]').astype(float) / 1e9 / 86400
            valid_gsl = raw[(~np.isnan(raw)) & (raw > 0) & (raw < 10000)]
            if len(valid_gsl) > 0:
                gsl = int(valid_gsl[0])

        harvest_str = 'N/A'
        if gsl:
            h_doy = doy + gsl - 1
            harvest_str = (pd.Timestamp('2001-01-01') +
                           pd.to_timedelta(h_doy - 1, unit='D')).strftime('%b %d')

        return {'planting': plant_str, 'planting_doy': doy,
                'season_length': gsl, 'harvest': harvest_str}
    except Exception:
        return None

half  = CELL_RES / 2
cells = summary[['cell_id', 'x', 'y']].drop_duplicates()

grid_geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": str(int(row.cell_id)),
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [row.x - half, row.y - half],
                    [row.x + half, row.y - half],
                    [row.x + half, row.y + half],
                    [row.x - half, row.y + half],
                    [row.x - half, row.y - half],
                ]]
            },
            "properties": {}
        }
        for _, row in cells.iterrows()
    ]
}
all_cell_ids = [str(cid) for cid in cell_meta.keys()]
center_lat   = summary['y'].mean()
center_lon   = summary['x'].mean()


def get_auto_zoom(min_lon, max_lon, min_lat, max_lat,
                  map_width_px=1300, map_height_px=MAP_HEIGHT):
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    if lon_span == 0 or lat_span == 0:
        return 8.5
    zoom_lon = math.log2(360 * map_width_px  / (256 * lon_span))
    zoom_lat = math.log2(180 * map_height_px / (256 * lat_span))
    return round(min(zoom_lon, zoom_lat) - 0.5, 1)

min_lon  = min(m['x'] for m in cell_meta.values()) - half
max_lon  = max(m['x'] for m in cell_meta.values()) + half
min_lat  = min(m['y'] for m in cell_meta.values()) - half
max_lat  = max(m['y'] for m in cell_meta.values()) + half
MAP_ZOOM = get_auto_zoom(min_lon, max_lon, min_lat, max_lat)
print(f"Auto zoom: {MAP_ZOOM}")



crop_var_range = {}
for ci in crop_irr_list:
    crop_var_range[ci] = {}
    for var in map_var_keys:
        sub = summary[summary['crop_irr'] == ci][var]
        if var == 'Seasonal irrigation (mm)':
            vmax = sub.max() if sub.max() > 0 else 1
            crop_var_range[ci][var] = (0, vmax)
        else:
            crop_var_range[ci][var] = (sub.min(), sub.max())


# ── Pre-compute all aggregations at startup ───────────────────────────────────
crop_var_range_all  = {}  # (ci, var, agg) → (vmin, vmax)
precomputed_agg     = {}  # (ci, var, agg) → DataFrame with cell_id + var columns

for ci in crop_irr_list:
    crop_var_range_all[ci] = {}
    sub_ci = summary[summary['crop_irr'] == ci]

    for var in map_var_keys:
        if var not in sub_ci.columns:
            continue
        grouped = sub_ci.groupby('cell_id')[var]

        for agg in ['mean', 'sum']:
            agg_vals = grouped.sum() if agg == 'sum' else grouped.mean()

            # Store colorbar range
            if var == 'Seasonal irrigation (mm)':
                vmax = agg_vals.max() if agg_vals.max() > 0 else 1
                crop_var_range_all[ci][f'{var}_{agg}'] = (0, vmax)
            else:
                crop_var_range_all[ci][f'{var}_{agg}'] = (agg_vals.min(), agg_vals.max())

            # Store aggregated values per cell as a DataFrame
            agg_df = agg_vals.reset_index()
            agg_df.columns = ['cell_id', var]
            agg_df = agg_df.merge(
                summary[['cell_id', 'x', 'y', 'crop', 'irrigation']].drop_duplicates('cell_id'),
                on='cell_id'
            )
            precomputed_agg[(ci, var, agg)] = agg_df


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        HELPERS                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def get_daily(cell_id):
    idx = cell_id_to_idx.get(cell_id)
    if idx is None or daily_raw[idx] is None:
        return None, None
    wf = daily_raw[idx]['water_flux'].copy().reset_index(drop=True)
    cg = daily_raw[idx]['crop_growth'].copy().reset_index(drop=True)
    wf['date'] = sim_start + pd.to_timedelta(wf.index, unit='D')
    cg['date'] = sim_start + pd.to_timedelta(cg.index, unit='D')
    return wf, cg

def get_climate_series(var, x, y):
    if var not in climate_ds:
        return None
    ds = climate_ds[var]
    pt = ds[var].sel(x=x, y=y, method='nearest')
    df = pt.to_dataframe().reset_index()[['time', var]]
    df.columns = ['date', var]
    return df

def get_climate_map_values(var, season_label):
    if var not in climate_ds:
        return None
    ds = climate_ds[var]
    if season_label == 'all':
        return ds[var].mean(dim='time')
    yr = int(season_label)
    return ds[var].sel(time=ds.time.dt.year == yr).mean(dim='time')

def get_cropcal_values(var_name, x, y):
    if var_name not in cropcal_ds:
        return None
    return float(cropcal_ds[var_name].sel(x=x, y=y, method='nearest').values)


def mapbox_layers():
    return [
        dict(sourcetype='raster',
             source=['https://server.arcgisonline.com/ArcGIS/rest/services/'
                     'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
             below='traces'),
        dict(source=region_geojson, type='line', color='#1a6faf', line=dict(width=2.5)),
    ]

def hex_to_rgba(hex_color, alpha):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'

def safe_date(year, month, day):
    """Clamp day to valid range for given month/year."""
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    return pd.Timestamp(year=year, month=month, day=min(day, max_day))

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        EXPORT FUNCTIONS                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def export_data(selected_cells, export_vars, start_date, end_date, formats):
    """
    Build a 3D array (time, y, x) for each selected variable and export
    to the requested formats. Returns a status message.
    """
    try:
        import rasterio
        from rasterio.transform import from_bounds
        has_rasterio = True
    except ImportError:
        has_rasterio = False

    # Resolve cell list
    cell_ids = list(cell_meta.keys()) if not selected_cells else [int(c) for c in selected_cells]

    # Date range
    start_ts = pd.Timestamp(start_date)
    end_ts   = pd.Timestamp(end_date)
    mask     = (date_index >= start_ts) & (date_index <= end_ts)
    time_idx = np.where(mask)[0]

    if len(time_idx) == 0:
        return 'No data in selected date range.'

    dates_sel = date_index[mask]

    # Grid axes from all cells
    xs = sorted(set(cell_meta[c]['x'] for c in cell_ids if c in cell_meta))
    ys = sorted(set(cell_meta[c]['y'] for c in cell_ids if c in cell_meta), reverse=True)

    exported = []

    for var in export_vars:
        var_info = DAILY_VARIABLES[var]
        # 3D array: time × y × x, filled with NaN
        arr = np.full((len(dates_sel), len(ys), len(xs)), np.nan, dtype=np.float32)

        for cid in cell_ids:
            if cid not in cell_id_to_idx:
                continue
            wf, cg = get_daily(cid)
            if wf is None:
                continue
            df = wf if var_info['table'] == 'water_flux' else cg
            df_sel = df.iloc[time_idx][var].values

            xi = xs.index(cell_meta[cid]['x'])
            yi = ys.index(cell_meta[cid]['y'])
            arr[:, yi, xi] = df_sel

        base_name = f"{var}_{start_ts.strftime('%Y%m%d')}_{end_ts.strftime('%Y%m%d')}"

        # ── NetCDF ────────────────────────────────────────────────────────────
        if 'nc' in formats:
            ds = xr.Dataset(
                {var: (['time', 'y', 'x'], arr)},
                coords={
                    'time': dates_sel,
                    'y':    ys,
                    'x':    xs,
                }
            )
            ds[var].attrs['long_name'] = var_info['label']
            ds[var].attrs['units']     = var_info['label'].split('(')[-1].replace(')', '') \
                                         if '(' in var_info['label'] else ''
            ds.attrs['description'] = f'AquaCrop gridded output: {var}'
            nc_path = os.path.join(EXPORT_DIR, base_name + '.nc')
            ds.to_netcdf(nc_path)
            exported.append(os.path.basename(nc_path))

        # ── GeoTIFF ───────────────────────────────────────────────────────────
        if 'tif' in formats:
            if not has_rasterio:
                exported.append('(rasterio not installed — GeoTIFF skipped)')
            else:
                x_min = min(xs) - half
                x_max = max(xs) + half
                y_min = min(ys) - half
                y_max = max(ys) + half
                transform = from_bounds(x_min, y_min, x_max, y_max, len(xs), len(ys))
                tif_path = os.path.join(EXPORT_DIR, base_name + '.tif')
                with rasterio.open(
                    tif_path, 'w',
                    driver='GTiff',
                    height=len(ys), width=len(xs),
                    count=len(dates_sel),
                    dtype='float32',
                    crs='EPSG:4326',
                    transform=transform,
                    nodata=np.nan,
                ) as dst:
                    for t_idx in range(len(dates_sel)):
                        dst.write(arr[t_idx], t_idx + 1)
                        dst.update_tags(t_idx + 1, date=str(dates_sel[t_idx].date()))
                exported.append(os.path.basename(tif_path))

        # ── CSV ───────────────────────────────────────────────────────────────
        if 'csv' in formats:
            rows = []
            for t_idx, dt in enumerate(dates_sel):
                for cid in cell_ids:
                    if cid not in cell_id_to_idx:
                        continue
                    xi = xs.index(cell_meta[cid]['x'])
                    yi = ys.index(cell_meta[cid]['y'])
                    rows.append({
                        'date':    str(dt.date()),
                        'cell_id': cid,
                        'x':       cell_meta[cid]['x'],
                        'y':       cell_meta[cid]['y'],
                        var:       arr[t_idx, yi, xi],
                    })
            df_csv  = pd.DataFrame(rows)
            csv_path = os.path.join(EXPORT_DIR, base_name + '.csv')
            df_csv.to_csv(csv_path, index=False)
            exported.append(os.path.basename(csv_path))

    if exported:
        return f"Saved {len(exported)} file(s) to {EXPORT_DIR}: {', '.join(exported)}"
    return 'Nothing exported — check selections.'

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        FIGURE BUILDERS                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def build_output_map(ci, season, map_var, agg_override,
                     sel_cell=None, lasso_cells=None, relayout_data=None):
    var_info = MAP_VARIABLES[map_var]
    agg_func = agg_override if agg_override in ['mean', 'sum'] else var_info['default_agg']

    if season == 'all':
        subset    = precomputed_agg.get((ci, map_var, agg_func))
        if subset is None:
            return go.Figure()
        subset    = subset.copy()
        agg_label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        vmin, vmax = crop_var_range_all[ci][f'{map_var}_{agg_func}']
    else:
        subset    = summary[(summary['crop_irr'] == ci) & (summary['season_label'] == season)].copy()
        agg_label = season
        vmin, vmax = crop_var_range[ci][map_var]

    subset['cell_id_str'] = subset['cell_id'].astype(int).astype(str)

    hover_texts = (
        '<b>Cell ' + subset['cell_id'].astype(int).astype(str) + '</b><br>'
        + 'Lon: ' + subset['x'].map('{:.3f}'.format) + ' | Lat: ' + subset['y'].map('{:.3f}'.format) + '<br>'
        + 'Crop: ' + subset['crop'].str.capitalize() + ' (' + subset['irrigation'] + ')<br>'
        + f'Period: {agg_label}<br>'
        + '──────────────────<br>'
        + var_info['label'] + ': ' + subset[map_var].map('{:.3f}'.format) + '<br>'
        + '<i>Click to view time series</i>'
    ).tolist()

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    # Lasso highlight
    lasso_ids = [str(c) for c in (lasso_cells or [])]
    lasso_z   = [1] * len(lasso_ids)

    traces = [
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=subset['cell_id_str'],
            z=subset[map_var], zmin=vmin, zmax=vmax,
            colorscale=var_info['sum_colorscale'] if agg_func == 'sum' else var_info['colorscale'],
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['label']}<br>({agg_label})",
                           font=dict(size=11, family='Arial, system-ui, sans-serif')),
                thickness=14, len=0.38,
                x=0.98, xanchor='right',
                y=0.02, yanchor='bottom',
                bgcolor='rgba(255,255,255,0.88)',
                bordercolor='rgba(0,0,0,0.12)', borderwidth=1,
                tickfont=dict(family='Arial, system-ui, sans-serif', size=10),
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
        ),
        # Clicked cell highlight
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
        # Lasso selected cells highlight
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=lasso_ids, z=lasso_z,
            colorscale=[[0, '#f39c12'], [1, '#f39c12']],
            showscale=False, marker_opacity=0.35,
            marker_line_width=2, marker_line_color='#f39c12',
            hoverinfo='skip',
        ),
        # Invisible centroid scatter for lasso tool
        go.Scattermapbox(
            lat=[cell_meta[int(cid)]['y'] for cid in all_cell_ids],
            lon=[cell_meta[int(cid)]['x'] for cid in all_cell_ids],
            mode='markers',
            marker=dict(size=8, opacity=0),
            text=all_cell_ids,
            hoverinfo='skip',
            showlegend=False,
        ),
    ]

    if relayout_data and 'mapbox.zoom' in relayout_data:
        mapbox = dict(
            style='white-bg',
            center=relayout_data.get('mapbox.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['mapbox.zoom'],
            layers=mapbox_layers(),
        )
    else:
        mapbox = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            mapbox=mapbox,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant',
            font=dict(family='Arial, system-ui, sans-serif'),
            annotations=[
                dict(x=0.016, y=0.100, xref='paper', yref='paper',
                     text='↑', font=dict(size=26, color='#2c3e50', family='Arial'),
                     showarrow=False, align='center'),
                dict(x=0.016, y=0.048, xref='paper', yref='paper',
                     text='N', font=dict(size=12, color='#2c3e50', family='Arial'),
                     showarrow=False, align='center',
                     bgcolor='rgba(255,255,255,0.82)',
                     bordercolor='rgba(0,0,0,0.10)', borderpad=4, borderwidth=1),
            ],
        )
    )


def build_output_ts(cell_id, season_label, daily_var, ts_period, ts_clicks=None):
    var_info = DAILY_VARIABLES[daily_var]

    if ts_period == 'full' or season_label == 'all':
        row_start, row_end = 0, n_rows - 1
        year_start = sim_start
        year_end   = sim_start + pd.to_timedelta(row_end, unit='D')
    else:
        row_start, row_end = year_rows[season_label]
        year_start = sim_start + pd.to_timedelta(row_start, unit='D')
        year_end   = sim_start + pd.to_timedelta(row_end,   unit='D')

    base_layout = dict(
        height=TS_HEIGHT, paper_bgcolor='white', plot_bgcolor='#f9f9f9',
        margin=dict(l=70, r=20, t=60, b=50),
        xaxis=dict(range=[str(year_start.date()), str(year_end.date())],
                   showgrid=True, gridcolor='#eeeeee', title='Date'),
        yaxis=dict(title=var_info['label'], showgrid=True, gridcolor='#eeeeee'),
        showlegend=False,
    )

    if cell_id is None:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text='← Click a cell on the map to view daily time series',
                       font=dict(size=13, color='#888888'), x=0.5),
            **base_layout)
        return fig

    wf, cg = get_daily(cell_id)
    if wf is None:
        return go.Figure()

    df      = wf if var_info['table'] == 'water_flux' else cg
    df_plot = df.iloc[row_start:row_end + 1].copy()
    meta    = cell_meta[cell_id]
    period_label = 'Full simulation' if ts_period == 'full' else season_label

    fig = go.Figure()

    if row_start <= preseason_end_row:
        shade_end = min(preseason_end_date, year_end)
        fig.add_vrect(
            x0=str(year_start.date()), x1=str(shade_end.date()),
            fillcolor='rgba(180,180,180,0.2)', layer='below', line_width=0,
            annotation_text='Pre-season', annotation_position='top left',
            annotation_font=dict(size=11, color='#888888'),
        )

    fig.add_trace(go.Scatter(
        x=df_plot['date'], y=df_plot[daily_var], mode='lines',
        line=dict(color=var_info['color'], width=1.8),
        hovertemplate='%{x|%b %d %Y}<br>' + var_info['label'] + ': %{y:.4f}<extra></extra>',
        name='Daily',
    ))

    fig = _add_mean_std_band(fig, df_plot, daily_var, var_info['color'],
                             year_start, year_end, ts_clicks)

    fig.update_layout(
        title=dict(
            text=(f"Cell {cell_id} | ({meta['x']:.3f}, {meta['y']:.3f}) | "
                  f"{meta['crop'].capitalize()} ({meta['irrigation']}) | {period_label}"),
            font=dict(size=13, family='Arial'), x=0.5),
        **base_layout)
    return fig


def build_input_map(climate_var, season_label, sel_cell=None, relayout_data=None):
    var_info = CLIMATE_VARIABLES[climate_var]
    arr      = get_climate_map_values(climate_var, season_label)

    if arr is None:
        return go.Figure()

    z_vals      = arr.sel(x=_x_da, y=_y_da, method='nearest').values.tolist()
    locations   = [str(int(c)) for c in _cell_ids_arr]
    hover_texts = [
        f"<b>Cell {cid}</b><br>Lon: {cell_meta[cid]['x']:.3f} | Lat: {cell_meta[cid]['y']:.3f}<br>{var_info['map_label']}: {val:.3f} {var_info['unit']}<br><i>Click to view time series</i>"
        for cid, val in zip(_cell_ids_arr.tolist(), z_vals)
    ]

    vmin = min(z_vals)
    vmax = max(z_vals)
    period_label = 'All years (daily mean)' if season_label == 'all' else f'{season_label} (daily mean)'

    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    traces = [
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=locations,
            z=z_vals, zmin=vmin, zmax=vmax,
            colorscale=var_info['colorscale'],
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['unit']}<br>({period_label})", font=dict(size=11)),
                thickness=16, len=0.55, x=1.01,
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
        ),
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
    ]

    if relayout_data and 'mapbox.zoom' in relayout_data:
        mapbox = dict(
            style='white-bg',
            center=relayout_data.get('mapbox.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['mapbox.zoom'],
            layers=mapbox_layers(),
        )
    else:
        mapbox = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            mapbox=mapbox,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant',
        )
    )

def build_spam_map(spam_var, sel_cell=None, relayout_data=None):
    if spam_ds is None or spam_var not in spam_ds.data_vars:
        return go.Figure()

    label       = spam_var.replace('_physical_area', '').replace('_', ' ')
    z_raw       = spam_ds[spam_var].sel(x=_x_da, y=_y_da, method='nearest').values
    z_arr       = np.where(np.isnan(z_raw), 0.0, z_raw)
    z_vals      = z_arr.tolist()
    locations   = [str(int(c)) for c in _cell_ids_arr]
    hover_texts = [
        f"<b>Cell {cid}</b><br>Lon: {cell_meta[cid]['x']:.3f} | Lat: {cell_meta[cid]['y']:.3f}<br>{label}: {val:.2f} ha"
        for cid, val in zip(_cell_ids_arr.tolist(), z_vals)
    ]

    vmin = 0
    vmax = max(z_vals) if max(z_vals) > 0 else 1
    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []

    traces = [
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=all_cell_ids,
            z=[0] * len(all_cell_ids),
            colorscale=[[0, '#cccccc'], [1, '#cccccc']],
            showscale=False, marker_opacity=0.4,
            marker_line_width=0.5, marker_line_color='white',
            hoverinfo='skip',
        ),
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=locations,
            z=z_vals, zmin=vmin, zmax=vmax,
            colorscale='YlGn',
            marker_opacity=0.95, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=label + '<br>(ha)',
                           font=dict(size=11, family='Arial, system-ui, sans-serif')),
                thickness=14, len=0.38,
                x=0.98, xanchor='right',
                y=0.02, yanchor='bottom',
                bgcolor='rgba(255,255,255,0.88)',
                bordercolor='rgba(0,0,0,0.12)', borderwidth=1,
                tickfont=dict(family='Arial, system-ui, sans-serif', size=10),
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
        ),
        go.Choroplethmapbox(
            geojson=grid_geojson, locations=sel_locations, z=sel_z,
            colorscale=[[0, '#1a6faf'], [1, '#1a6faf']],
            showscale=False, marker_opacity=0.45,
            marker_line_width=2.5, marker_line_color='#1a6faf',
            hoverinfo='skip',
        ),
    ]

    if relayout_data and 'mapbox.zoom' in relayout_data:
        mapbox = dict(
            style='white-bg',
            center=relayout_data.get('mapbox.center', dict(lat=center_lat, lon=center_lon)),
            zoom=relayout_data['mapbox.zoom'],
            layers=mapbox_layers(),
        )
    else:
        mapbox = dict(
            style='white-bg',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=MAP_ZOOM, layers=mapbox_layers(),
        )

    return go.Figure(
        data=traces,
        layout=go.Layout(
            mapbox=mapbox,
            margin=dict(l=0, r=0, t=0, b=0),
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant-spam',
            font=dict(family='Arial, system-ui, sans-serif'),
        )
    )

def build_input_ts(cell_id, climate_var, season_label, ts_period, ts_clicks=None, sel_crop_irr=None):
    if sel_crop_irr is None:
        sel_crop_irr = crop_irr_list[0]
    var_info = CLIMATE_VARIABLES[climate_var]

    if ts_period == 'full' or season_label == 'all':
        year_start = sim_start
        year_end   = sim_start + pd.to_timedelta(n_rows - 1, unit='D')
    else:
        row_start, row_end = year_rows[season_label]
        year_start = sim_start + pd.to_timedelta(row_start, unit='D')
        year_end   = sim_start + pd.to_timedelta(row_end,   unit='D')

    base_layout = dict(
        height=TS_HEIGHT, paper_bgcolor='white', plot_bgcolor='#f9f9f9',
        margin=dict(l=70, r=20, t=60, b=50),
        xaxis=dict(range=[str(year_start.date()), str(year_end.date())],
                   showgrid=True, gridcolor='#eeeeee', title='Date'),
        yaxis=dict(title=var_info['label'], showgrid=True, gridcolor='#eeeeee'),
        showlegend=False,
    )

    if cell_id is None:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text='← Click a cell on the map to view climate time series',
                       font=dict(size=13, color='#888888'), x=0.5),
            **base_layout)
        return fig

    meta = cell_meta.get(cell_id)
    if meta is None:
        return go.Figure()

    df = get_climate_series(climate_var, meta['x'], meta['y'])
    if df is None:
        return go.Figure()

    mask    = (df['date'] >= year_start) & (df['date'] <= year_end)
    df_plot = df[mask].copy()

    fig = go.Figure()

    if year_start <= preseason_end_date:
        shade_end = min(preseason_end_date, year_end)
        fig.add_vrect(
            x0=str(year_start.date()), x1=str(shade_end.date()),
            fillcolor='rgba(180,180,180,0.2)', layer='below', line_width=0,
            annotation_text='Pre-season', annotation_position='top left',
            annotation_font=dict(size=11, color='#888888'),
        )

    # Use currently selected crop from function parameter
    crop_name_ci = sel_crop_irr.split(' | ')[0].capitalize()
    irr_code_ci  = IRR_MAP.get(sel_crop_irr.split(' | ')[1], sel_crop_irr.split(' | ')[1])
    cal_var      = f'{crop_name_ci}_{irr_code_ci}_planting'
    planting_doy = get_cropcal_values(cal_var, meta['x'], meta['y'])
    if planting_doy is not None and not np.isnan(planting_doy):
        for yr in years:
            try:
                plant_date = pd.Timestamp(f'{yr}-01-01') + pd.to_timedelta(int(planting_doy) - 1, unit='D')
                if year_start <= plant_date <= year_end:
                    fig.add_vline(
                        x=plant_date.timestamp() * 1000,
                        line=dict(color='#27ae60', width=1.5, dash='dash'),
                        annotation_text=f'Planting {yr}',
                        annotation_position='top right',
                        annotation_font=dict(size=10, color='#27ae60'),
                    )
            except Exception:
                pass

    fig.add_trace(go.Scatter(
        x=df_plot['date'], y=df_plot[climate_var], mode='lines',
        line=dict(color=var_info['color'], width=1.8),
        hovertemplate='%{x|%b %d %Y}<br>' + var_info['label'] + ': %{y:.3f}<extra></extra>',
        name=var_info['label'],
    ))

    fig = _add_mean_std_band(fig, df_plot, climate_var, var_info['color'],
                             year_start, year_end, ts_clicks)

    period_label = 'Full simulation' if ts_period == 'full' else season_label
    fig.update_layout(
        title=dict(
            text=(f"Cell {cell_id} | ({meta['x']:.3f}, {meta['y']:.3f}) | "
                  f"{var_info['label']} | {period_label}"),
            font=dict(size=13, family='Arial'), x=0.5),
        **base_layout)
    return fig


def _add_mean_std_band(fig, df_plot, var_col, color, year_start, year_end, ts_clicks):
    if ts_clicks and ts_clicks.get('start') and ts_clicks.get('end'):
        sel_start = max(pd.Timestamp(ts_clicks['start']), year_start)
        sel_end   = min(pd.Timestamp(ts_clicks['end']),   year_end)
        mask      = (df_plot['date'] >= sel_start) & (df_plot['date'] <= sel_end)
        df_sel    = df_plot[mask]

        if not df_sel.empty:
            mean_val = df_sel[var_col].mean()
            std_val  = df_sel[var_col].std()
            upper    = mean_val + std_val
            lower    = mean_val - std_val
            x_band   = list(df_sel['date']) + list(df_sel['date'])[::-1]
            y_band   = ([upper] * len(df_sel)) + ([lower] * len(df_sel))

            fig.add_trace(go.Scatter(
                x=x_band, y=y_band, fill='toself',
                fillcolor=hex_to_rgba(color, 0.20),
                line=dict(width=0), hoverinfo='skip', name='Mean ± Std',
            ))
            fig.add_trace(go.Scatter(
                x=list(df_sel['date']), y=[mean_val] * len(df_sel),
                mode='lines', line=dict(color=color, width=2, dash='dash'),
                hoverinfo='skip', name='Mean',
            ))
            for boundary in [sel_start, sel_end]:
                fig.add_vline(x=boundary.timestamp() * 1000,
                              line=dict(color='#555555', width=1, dash='dot'))
            fig.add_annotation(
                x=sel_start + (sel_end - sel_start) / 2, y=upper,
                text=(f"Mean: {mean_val:.4f}<br>Std: {std_val:.4f}<br>"
                      f"{sel_start.strftime('%b %d')} – {sel_end.strftime('%b %d %Y')}"),
                showarrow=False,
                bgcolor='rgba(255,255,255,0.85)',
                bordercolor=color, borderwidth=1, borderpad=5,
                font=dict(size=11, family='Arial'), yanchor='bottom',
            )
    elif ts_clicks and ts_clicks.get('count') == 1:
        fig.add_annotation(x=0.5, y=1.02, xref='paper', yref='paper',
                           text='Click a second point to set the end of the window',
                           showarrow=False, font=dict(size=13, color='#888888'))
    else:
        fig.add_annotation(x=0.5, y=1.02, xref='paper', yref='paper',
                           text='Click two points to compute mean ± std  |  Third click resets',
                           showarrow=False, font=dict(size=13, color='#888888'))
    return fig

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        BUTTON STYLES (retained for period buttons)         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def btn_style(active, color):
    palette = {
        'blue':   ('#3d5a8a', '#eef2f7'),
        'green':  ('#4caf50', '#e8f4ea'),
        'orange': ('#e65100', '#fff3e0'),
        'purple': ('#6a1b9a', '#f3e5f5'),
        'teal':   ('#00796b', '#e0f2f1'),
        'red':    ('#c0392b', '#fdecea'),
    }
    border, bg = palette[color]
    base = dict(padding='5px 13px', margin='2px', borderRadius='4px',
                cursor='pointer', fontSize='12px',
                fontFamily='Arial, system-ui, sans-serif',
                border=f'1px solid {border}')
    if active:
        return {**base, 'backgroundColor': border, 'color': 'white'}
    return {**base, 'backgroundColor': bg, 'color': '#333'}

def dd_style(w='80px'):
    return {'display': 'inline-block', 'width': w,
            'fontSize': '12px', 'marginLeft': '4px',
            'verticalAlign': 'middle'}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        STYLE CONSTANTS                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

FONT_STACK  = 'Arial, system-ui, -apple-system, sans-serif'
ACCENT      = '#3d5a8a'
SIDEBAR_BG  = '#f8f9fa'

SIDEBAR_STYLE = {
    'backgroundColor': SIDEBAR_BG,
    'borderRight': '1px solid #dee2e6',
    'padding': '14px 12px 80px',
    'minHeight': '100vh',
    'overflowY': 'auto',
    'fontFamily': FONT_STACK,
    'position': 'relative',
}

RIBBON_STYLE = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'space-between',
    'backgroundColor': '#edf2f7',
    'padding': '6px 14px',
    'borderTop': '1px solid #dee2e6',
    'borderBottom': '1px solid #dee2e6',
    'fontFamily': FONT_STACK,
    'fontSize': '12px',
    'color': '#4a5568',
    'minHeight': '38px',
}

DD_CTRL_STYLE = {'fontFamily': FONT_STACK, 'fontSize': '12px', 'marginBottom': '8px'}

def _sec_hdr(text):
    return html.Div(text, style={
        'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
        'color': '#7a8a9a', 'letterSpacing': '1.2px', 'textTransform': 'uppercase',
        'margin': '12px 0 4px',
    })

def _ctrl_label(text):
    return html.Label(text, style={
        'fontFamily': FONT_STACK, 'fontSize': '11px', 'fontWeight': '600',
        'color': '#4a5568', 'marginBottom': '2px', 'display': 'block',
    })

# ── Variable group membership ─────────────────────────────────────────────────
_YIELD_VARS = ['Dry yield (tonne/ha)', 'Fresh yield (tonne/ha)',
               'Yield potential (tonne/ha)', 'production_tonnes']
_WATER_VARS = ['Seasonal irrigation (mm)', 'seasonal_precip_mm',
               'seasonal_et_mm', 'seasonal_transpiration_mm', 'total_water_input_mm']
_WP_VARS    = ['wp_et_kg_per_m3', 'rainfall_use_efficiency_kg_per_m3']
_FLUX_VARS  = ['Es', 'EsPot', 'Tr', 'TrPot', 'Infl', 'Runoff', 'DeepPerc']
_SOIL_VARS  = ['Wr']
_CROP_VARS  = ['biomass', 'canopy_cover', 'gdd_cum', 'z_root', 'DryYield']

def _map_dd_opts(keys):
    return [{'label': MAP_VARIABLES[v]['label'], 'value': v}
            for v in keys if v in MAP_VARIABLES]

def _daily_dd_opts(keys):
    return [{'label': DAILY_VARIABLES[v]['label'], 'value': v}
            for v in keys if v in DAILY_VARIABLES]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        APP LAYOUT                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>AquaCrop Gridded Explorer</title>
        {%favicon%}
        {%css%}
        <style>
            /* ── Accordion header base ─────────────────────────────────── */
            .accordion-button {
                padding-left: 25px !important;
                font-family: Arial, system-ui, sans-serif !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                background-color: #f8f9fa !important;
                box-shadow: none !important;
                border: none !important;
            }
            /* Remove the default SVG chevron that can render as '*' and
               replace with a clean Unicode arrow instead */
            .accordion-button::after {
                background-image: none !important;
                content: '▾' !important;
                font-size: 13px !important;
                line-height: 1 !important;
                width: auto !important;
                height: auto !important;
                transform: none !important;
                transition: none !important;
                color: inherit !important;
            }
            .accordion-button.collapsed::after {
                content: '▸' !important;
                transform: none !important;
            }
            /* Expanded header: dark navy + bold */
            .accordion-button:not(.collapsed) {
                color: #1e3a5f !important;
                font-weight: 700 !important;
                background-color: #eef2f7 !important;
            }
            /* Collapsed header: muted gray */
            .accordion-button.collapsed {
                color: #6c757d !important;
            }
            /* Tighten accordion body padding */
            .accordion-body {
                padding: 5px 10px 7px !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = dbc.Container(fluid=True, style={'fontFamily': FONT_STACK, 'padding': '0'}, children=[

    dbc.Row(className='g-0', children=[

        # ══════════════════════════════════════════════════════════════════════
        # LEFT SIDEBAR
        # ══════════════════════════════════════════════════════════════════════
        dbc.Col(width=3, style=SIDEBAR_STYLE, children=[

            html.H5('AquaCrop Gridded Explorer', style={
                'fontFamily': FONT_STACK, 'fontWeight': '700',
                'color': '#2c3e50', 'marginBottom': '12px', 'fontSize': '15px',
            }),

            # ── Tab bar ───────────────────────────────────────────────────────
            dcc.Tabs(
                id='main-tabs', value='output',
                style={'marginBottom': '10px'},
                colors={'border': ACCENT, 'primary': ACCENT, 'background': SIDEBAR_BG},
                children=[
                    dcc.Tab(
                        label='Simulation Outputs', value='output',
                        style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                               'padding': '6px 8px', 'color': '#4a5568'},
                        selected_style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                        'padding': '6px 8px', 'backgroundColor': ACCENT,
                                        'color': 'white', 'borderTop': f'3px solid {ACCENT}'},
                    ),
                    dcc.Tab(
                        label='Inputs', value='input',
                        style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                               'padding': '6px 8px', 'color': '#4a5568'},
                        selected_style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                        'padding': '6px 8px', 'backgroundColor': ACCENT,
                                        'color': 'white', 'borderTop': f'3px solid {ACCENT}'},
                    ),
                ],
            ),

            # ── Data Configuration ────────────────────────────────────────────
            _sec_hdr('Data Configuration'),
            _ctrl_label('Crop & Irrigation'),
            dcc.Dropdown(
                id='crop-dropdown',
                options=[{'label': ci, 'value': ci} for ci in crop_irr_list],
                value=crop_irr_list[0], clearable=False, style=DD_CTRL_STYLE,
            ),
            _ctrl_label('Season'),
            dcc.Dropdown(
                id='season-dropdown',
                options=(
                    [{'label': s, 'value': s} for s in season_list] +
                    [{'label': 'All years', 'value': 'all'}]
                ),
                value=season_list[0], clearable=False, style=DD_CTRL_STYLE,
            ),

            # Aggregation (shown only when season=all + output tab)
            html.Div(id='agg-row', style={'display': 'none'}, children=[
                _ctrl_label('Aggregation'),
                html.Div([
                    html.Button('Mean', id={'type': 'agg-btn', 'index': 'mean'}, n_clicks=0,
                                style=btn_style(True,  'teal')),
                    html.Button('Sum',  id={'type': 'agg-btn', 'index': 'sum'},  n_clicks=0,
                                style=btn_style(False, 'teal')),
                ], style={'marginBottom': '6px'}),
            ]),

            # ── Output controls ───────────────────────────────────────────────
            html.Div(id='output-controls', children=[

                _sec_hdr('Map Variable'),
                dbc.Accordion(flush=True, always_open=True,
                              active_item=['yield'],
                              style={'marginBottom': '10px',
                                     'border': '1px solid #e2e8f0',
                                     'borderRadius': '6px', 'overflow': 'hidden'},
                              children=[
                    dbc.AccordionItem(title='Yield & Production', item_id='yield',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='mapvar-yield-dd',
                            options=_map_dd_opts(_YIELD_VARS),
                            value=map_var_keys[0] if map_var_keys[0] in _YIELD_VARS else None,
                            placeholder='Select variable…', clearable=True,
                            style=DD_CTRL_STYLE,
                        ),
                    ]),
                    dbc.AccordionItem(title='Water Balance', item_id='water',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='mapvar-water-dd',
                            options=_map_dd_opts(_WATER_VARS),
                            value=None, placeholder='Select variable…',
                            clearable=True, style=DD_CTRL_STYLE,
                        ),
                    ]),
                    dbc.AccordionItem(title='Water Productivity', item_id='wp',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='mapvar-wp-dd',
                            options=_map_dd_opts(_WP_VARS),
                            value=None, placeholder='Select variable…',
                            clearable=True, style=DD_CTRL_STYLE,
                        ),
                    ]),
                ]),

                _sec_hdr('Daily Variable'),
                dbc.Accordion(flush=True, always_open=True,
                              active_item=['flux'],
                              style={'marginBottom': '10px',
                                     'border': '1px solid #e2e8f0',
                                     'borderRadius': '6px', 'overflow': 'hidden'},
                              children=[
                    dbc.AccordionItem(title='Water Fluxes', item_id='flux',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='dailyvar-flux-dd',
                            options=_daily_dd_opts(_FLUX_VARS),
                            value=daily_var_keys[0] if daily_var_keys[0] in _FLUX_VARS else None,
                            placeholder='Select variable…', clearable=True,
                            style=DD_CTRL_STYLE,
                        ),
                    ]),
                    dbc.AccordionItem(title='Soil Water', item_id='soil',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='dailyvar-soil-dd',
                            options=_daily_dd_opts(_SOIL_VARS),
                            value=None, placeholder='Select variable…',
                            clearable=True, style=DD_CTRL_STYLE,
                        ),
                    ]),
                    dbc.AccordionItem(title='Crop Development', item_id='crop_dev',
                                      style={'padding': '2px 0'}, children=[
                        dcc.Dropdown(
                            id='dailyvar-crop-dd',
                            options=_daily_dd_opts(_CROP_VARS),
                            value=None, placeholder='Select variable…',
                            clearable=True, style=DD_CTRL_STYLE,
                        ),
                    ]),
                ]),

            ]),

            # ── Input controls ────────────────────────────────────────────────
            html.Div(id='input-controls', style={'display': 'none'}, children=[

                _sec_hdr('Climate Variable'),
                dcc.Dropdown(
                    id='climvar-dd',
                    options=[{'label': CLIMATE_VARIABLES[v]['map_label'], 'value': v}
                             for v in climate_var_keys],
                    value=climate_var_keys[0], clearable=False, style=DD_CTRL_STYLE,
                ),

                html.Div(id='spam-btn-row', children=[
                    _ctrl_label('Crop Area (SPAM)'),
                    html.Span(id='spam-btn-container', children=[]),
                ], style={'marginTop': '8px'}),
            ]),




            # ── Export button pinned at sidebar bottom ────────────────────────
            html.Div(id='export-btn-wrapper', children=[
                html.Button(
                    '⬇  Export Data...',
                    id='export-modal-open', n_clicks=0,
                    style={
                        'width': '100%', 'padding': '8px 0',
                        'backgroundColor': '#f0f4fa', 'color': ACCENT,
                        'border': f'1px solid {ACCENT}', 'borderRadius': '5px',
                        'fontFamily': FONT_STACK, 'fontSize': '12px',
                        'fontWeight': '600', 'cursor': 'pointer', 'textAlign': 'center',
                    },
                ),
            ], style={
                'position': 'absolute', 'bottom': '14px',
                'left': '12px', 'right': '12px',
            }),

        ]),  # end sidebar col

        # ══════════════════════════════════════════════════════════════════════
        # RIGHT MAIN CANVAS
        # ══════════════════════════════════════════════════════════════════════
        dbc.Col(width=9, style={'padding': '0', 'backgroundColor': 'white'}, children=[

            # ── Output panel ──────────────────────────────────────────────────
            html.Div(id='output-panel', children=[

                dcc.Graph(
                    id='output-map',
                    figure=build_output_map(crop_irr_list[0], season_list[0],
                                            map_var_keys[0], 'mean'),
                    config={'scrollZoom': True,
                            'modeBarButtonsToAdd': ['lasso2d', 'select2d']},
                    style={'width': '100%'},
                ),

                # Time series ribbon + graph (hidden until a cell is clicked)
                html.Div(id='output-ts-container', style={'display': 'none'}, children=[

                    html.Div(style=RIBBON_STYLE, children=[
                        html.Span(id='ts-ribbon-text',
                                  children='Select a cell on the map to view time series',
                                  style={'flexGrow': '1', 'fontFamily': FONT_STACK,
                                         'fontSize': '12px', 'color': '#4a5568'}),
                        html.Div([
                            html.Button(
                                'Selected season',
                                id={'type': 'out-period-btn', 'index': 'season'},
                                n_clicks=0, style=btn_style(True, 'blue')),
                            html.Button(
                                'Full simulation',
                                id={'type': 'out-period-btn', 'index': 'full'},
                                n_clicks=0, style=btn_style(False, 'blue')),
                        ], style={'flexShrink': '0', 'paddingLeft': '12px'}),
                    ]),

                    dcc.Graph(
                        id='output-ts',
                        figure=build_output_ts(None, season_list[0],
                                               daily_var_keys[0], 'season'),
                        style={'width': '100%'},
                    ),

                ]),

            ]),

            # ── Input panel ───────────────────────────────────────────────────
            html.Div(id='input-panel', style={'display': 'none'}, children=[

                html.Div([
                    html.Span('Crop calendar: ', style={
                        'fontFamily': FONT_STACK, 'fontSize': '11px',
                        'fontWeight': '600', 'color': '#4a5568', 'marginRight': '4px',
                    }),
                    html.Span(id='cropcal-info-text', children='—',
                              style={'fontFamily': FONT_STACK, 'fontSize': '11px',
                                     'color': '#555'}),
                ], style={
                    'padding': '5px 14px', 'backgroundColor': '#f8f9fa',
                    'borderBottom': '1px solid #dee2e6',
                }),

                dcc.Graph(
                    id='input-map',
                    figure=build_input_map(climate_var_keys[0], season_list[0]),
                    config={'scrollZoom': True},
                    style={'width': '100%'},
                ),

                html.Div(id='input-ts-container', style={'display': 'none'}, children=[

                    html.Div(style=RIBBON_STYLE, children=[
                        html.Span(id='input-ribbon-text',
                                  children='Select a cell on the map to view time series',
                                  style={'flexGrow': '1', 'fontFamily': FONT_STACK,
                                         'fontSize': '12px', 'color': '#4a5568'}),
                        html.Div([
                            html.Button(
                                'Selected season',
                                id={'type': 'in-period-btn', 'index': 'season'},
                                n_clicks=0, style=btn_style(True, 'blue')),
                            html.Button(
                                'Full simulation',
                                id={'type': 'in-period-btn', 'index': 'full'},
                                n_clicks=0, style=btn_style(False, 'blue')),
                        ], style={'flexShrink': '0', 'paddingLeft': '12px'}),
                    ]),

                    dcc.Graph(
                        id='input-ts',
                        figure=build_input_ts(None, climate_var_keys[0],
                                              season_list[0], 'season'),
                        style={'width': '100%'},
                    ),

                ]),

            ]),

        ]),  # end canvas col

    ]),  # end main row

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT MODAL
    # ══════════════════════════════════════════════════════════════════════════
    dbc.Modal(id='export-modal', size='lg', is_open=False, children=[

        dbc.ModalHeader(dbc.ModalTitle('Export Gridded Output',
                        style={'fontFamily': FONT_STACK, 'fontSize': '16px'})),

        dbc.ModalBody(style={'fontFamily': FONT_STACK}, children=[

            html.Div([
                html.Label('Variables', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                               'fontSize': '12px', 'marginBottom': '8px',
                                               'display': 'block'}),
                # Water Fluxes group
                html.Div([
                    html.Div('Water Fluxes', style={
                        'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                        'color': '#7a8a9a', 'letterSpacing': '1px',
                        'textTransform': 'uppercase', 'marginBottom': '4px',
                    }),
                    dcc.Checklist(
                        id='export-vars-flux',
                        options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                                 for v in _FLUX_VARS],
                        value=[_FLUX_VARS[0]], inline=True,
                        style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                        inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                    ),
                ], style={'marginBottom': '10px', 'paddingBottom': '8px',
                          'borderBottom': '1px solid #e2e8f0'}),
                # Soil Water group
                html.Div([
                    html.Div('Soil Water', style={
                        'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                        'color': '#7a8a9a', 'letterSpacing': '1px',
                        'textTransform': 'uppercase', 'marginBottom': '4px',
                    }),
                    dcc.Checklist(
                        id='export-vars-soil',
                        options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                                 for v in _SOIL_VARS],
                        value=[], inline=True,
                        style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                        inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                    ),
                ], style={'marginBottom': '10px', 'paddingBottom': '8px',
                          'borderBottom': '1px solid #e2e8f0'}),
                # Crop Development group
                html.Div([
                    html.Div('Crop Development', style={
                        'fontFamily': FONT_STACK, 'fontSize': '10px', 'fontWeight': '700',
                        'color': '#7a8a9a', 'letterSpacing': '1px',
                        'textTransform': 'uppercase', 'marginBottom': '4px',
                    }),
                    dcc.Checklist(
                        id='export-vars-crop',
                        options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                                 for v in _CROP_VARS],
                        value=[], inline=True,
                        style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                        inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
                    ),
                ]),
                # Hidden merged store consumed by run_export
                dcc.Store(id='export-vars', data=[_FLUX_VARS[0]]),
            ], style={'marginBottom': '14px'}),

            html.Div([
                html.Label('Period', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                            'fontSize': '12px', 'marginBottom': '4px',
                                            'display': 'block'}),
                dcc.Checklist(
                    id='export-whole-period',
                    options=[{'label': '  Whole simulation', 'value': 'whole'}],
                    value=[], inline=True,
                    style={'display': 'inline', 'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
                ),
                html.Span('  From:', style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                            'marginLeft': '16px'}),
                dcc.Dropdown(id='export-start-year',
                             options=[{'label': str(y), 'value': y} for y in years],
                             value=years[0], clearable=False, style=dd_style('80px')),
                dcc.Dropdown(id='export-start-month',
                             options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                             value=1, clearable=False, style=dd_style('70px')),
                dcc.Dropdown(id='export-start-day',
                             options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                             value=1, clearable=False, style=dd_style('70px')),
                html.Span('  To:', style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                          'marginLeft': '12px'}),
                dcc.Dropdown(id='export-end-year',
                             options=[{'label': str(y), 'value': y} for y in years],
                             value=years[-1], clearable=False, style=dd_style('80px')),
                dcc.Dropdown(id='export-end-month',
                             options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                             value=12, clearable=False, style=dd_style('70px')),
                dcc.Dropdown(id='export-end-day',
                             options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                             value=31, clearable=False, style=dd_style('70px')),
            ], style={'marginBottom': '14px'}),

            html.Div([
                html.Label('Cells', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                           'fontSize': '12px', 'marginBottom': '4px',
                                           'display': 'block'}),
                dcc.Checklist(
                    id='export-whole-area',
                    options=[{'label': '  Whole area', 'value': 'all'}],
                    value=['all'], inline=True,
                    style={'display': 'inline', 'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
                ),
                html.Span(id='export-cell-label',
                          children='  |  or use lasso/box on the map to select cells',
                          style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                 'color': '#888888', 'marginLeft': '8px'}),
            ], style={'marginBottom': '14px'}),

            html.Div([
                html.Label('Format', style={'fontFamily': FONT_STACK, 'fontWeight': '600',
                                            'fontSize': '12px', 'marginBottom': '4px',
                                            'display': 'block'}),
                dcc.Checklist(
                    id='export-format',
                    options=[
                        {'label': '  NetCDF (.nc)',   'value': 'nc'},
                        {'label': '  GeoTIFF (.tif)', 'value': 'tif'},
                        {'label': '  CSV (.csv)',      'value': 'csv'},
                    ],
                    value=['csv'], inline=True,
                    style={'fontFamily': FONT_STACK, 'fontSize': '12px'},
                    inputStyle={'marginRight': '4px', 'marginLeft': '14px'},
                ),
            ]),

        ]),

        dbc.ModalFooter([
            html.Span(id='export-status', children='',
                      style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                             'color': '#27ae60', 'marginRight': 'auto'}),
            html.Button('Export', id='export-btn', n_clicks=0,
                        style={**btn_style(True, 'blue'),
                               'fontSize': '13px', 'padding': '7px 28px'}),
            dbc.Button('Close', id='export-modal-close', n_clicks=0,
                       color='secondary', size='sm',
                       style={'marginLeft': '8px', 'fontFamily': FONT_STACK}),
        ]),

    ]),

    # ══════════════════════════════════════════════════════════════════════════
    # STORES 
    # ══════════════════════════════════════════════════════════════════════════
    dcc.Store(id='sel-tab',        data='output'),
    dcc.Store(id='sel-crop',       data=crop_irr_list[0]),
    dcc.Store(id='sel-season',     data=season_list[0]),
    dcc.Store(id='sel-map-var',    data=map_var_keys[0]),
    dcc.Store(id='sel-daily-var',  data=daily_var_keys[0]),
    dcc.Store(id='sel-clim-var',   data=climate_var_keys[0]),
    dcc.Store(id='sel-agg',        data='mean'),
    dcc.Store(id='sel-out-period', data='season'),
    dcc.Store(id='sel-in-period',  data='season'),
    dcc.Store(id='sel-out-cell',   data=None),
    dcc.Store(id='sel-in-cell',    data=None),
    dcc.Store(id='out-ts-clicks',  data={'count': 0, 'start': None, 'end': None}),
    dcc.Store(id='in-ts-clicks',   data={'count': 0, 'start': None, 'end': None}),
    dcc.Store(id='lasso-cells',    data=[]),
    dcc.Store(id='sel-spam-var',   data=''),
    dcc.Store(id='input-mode',     data='climate'),

])

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        CALLBACKS                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── Tab selection ─────────────────────────────────────────────────────────────
@app.callback(Output('sel-tab', 'data'),
              Input('main-tabs', 'value'))
def set_tab(active_tab):
    return active_tab or 'output'

@app.callback(
    Output('output-panel',    'style'),
    Output('input-panel',     'style'),
    Output('output-controls', 'style'),
    Output('input-controls',  'style'),
    Input('sel-tab', 'data'),
)
def toggle_tabs(sel_tab):
    show, hide = {'display': 'block'}, {'display': 'none'}
    if sel_tab == 'output':
        return show, hide, show, hide
    return hide, show, hide, show

# ── Crop & season ─────────────────────────────────────────────────────────────
@app.callback(Output('sel-crop', 'data'),
              Input('crop-dropdown', 'value'))
def set_crop(val):
    return val or crop_irr_list[0]

@app.callback(Output('sel-season', 'data'),
              Input('season-dropdown', 'value'))
def set_season(val):
    return val or season_list[0]

# ── Aggregation ───────────────────────────────────────────────────────────────
@app.callback(Output('sel-agg', 'data'),
              Input({'type': 'agg-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_agg(_):
    t = ctx.triggered_id
    return t['index'] if t else 'mean'

@app.callback(
    Output({'type': 'agg-btn', 'index': ALL}, 'style'),
    Input('sel-agg', 'data'),
)
def style_agg_btns(sel_agg):
    return [btn_style(a == sel_agg, 'teal') for a in ['mean', 'sum']]

@app.callback(
    Output('agg-row', 'style'),
    Input('sel-season', 'data'),
    Input('sel-tab',    'data'),
)
def toggle_agg_row(sel_season, sel_tab):
    if sel_season == 'all' and sel_tab == 'output':
        return {'display': 'block'}
    return {'display': 'none'}

# ── Map variable selection (three accordion dropdowns → one store) ─────────────
@app.callback(
    Output('sel-map-var',    'data'),
    Output('mapvar-yield-dd', 'value'),
    Output('mapvar-water-dd', 'value'),
    Output('mapvar-wp-dd',    'value'),
    Input('mapvar-yield-dd', 'value'),
    Input('mapvar-water-dd', 'value'),
    Input('mapvar-wp-dd',    'value'),
    prevent_initial_call=True,
)
def set_map_var(yield_v, water_v, wp_v):
    t = ctx.triggered_id
    if t == 'mapvar-yield-dd' and yield_v:
        return yield_v, yield_v, None, None
    if t == 'mapvar-water-dd' and water_v:
        return water_v, None, water_v, None
    if t == 'mapvar-wp-dd' and wp_v:
        return wp_v, None, None, wp_v
    return map_var_keys[0], map_var_keys[0], None, None

# ── Daily variable selection ──────────────────────────────────────────────────
@app.callback(
    Output('sel-daily-var',    'data'),
    Output('dailyvar-flux-dd', 'value'),
    Output('dailyvar-soil-dd', 'value'),
    Output('dailyvar-crop-dd', 'value'),
    Input('dailyvar-flux-dd', 'value'),
    Input('dailyvar-soil-dd', 'value'),
    Input('dailyvar-crop-dd', 'value'),
    prevent_initial_call=True,
)
def set_daily_var(flux_v, soil_v, crop_v):
    t = ctx.triggered_id
    if t == 'dailyvar-flux-dd' and flux_v:
        return flux_v, flux_v, None, None
    if t == 'dailyvar-soil-dd' and soil_v:
        return soil_v, None, soil_v, None
    if t == 'dailyvar-crop-dd' and crop_v:
        return crop_v, None, None, crop_v
    return daily_var_keys[0], daily_var_keys[0], None, None

# ── Climate variable selection ────────────────────────────────────────────────
@app.callback(Output('sel-clim-var', 'data'),
              Input('climvar-dd', 'value'))
def set_clim_var(val):
    return val or climate_var_keys[0]

# ── Period buttons ────────────────────────────────────────────────────────────
@app.callback(Output('sel-out-period', 'data'),
              Input({'type': 'out-period-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_out_period(_):
    t = ctx.triggered_id
    return t['index'] if t else 'season'

@app.callback(Output('sel-in-period', 'data'),
              Input({'type': 'in-period-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_in_period(_):
    t = ctx.triggered_id
    return t['index'] if t else 'season'

@app.callback(
    Output({'type': 'out-period-btn', 'index': ALL}, 'style'),
    Output({'type': 'in-period-btn',  'index': ALL}, 'style'),
    Input('sel-out-period', 'data'),
    Input('sel-in-period',  'data'),
)
def style_period_btns(sel_out, sel_in):
    return (
        [btn_style(p == sel_out, 'blue') for p in ['season', 'full']],
        [btn_style(p == sel_in,  'blue') for p in ['season', 'full']],
    )

# ── Cell click selection ──────────────────────────────────────────────────────
@app.callback(Output('sel-out-cell', 'data'),
              Input('output-map', 'clickData'),
              prevent_initial_call=True)
def set_out_cell(click_data):
    if click_data is None:
        return None
    pt = click_data['points'][0]
    if 'location' in pt:
        return int(pt['location'])
    return None

@app.callback(Output('sel-in-cell', 'data'),
              Input('input-map', 'clickData'),
              prevent_initial_call=True)
def set_in_cell(click_data):
    if click_data is None:
        return None
    pt = click_data['points'][0]
    if 'location' in pt:
        return int(pt['location'])
    return None

# ── Lasso selection ───────────────────────────────────────────────────────────
@app.callback(
    Output('lasso-cells',       'data'),
    Output('export-cell-label', 'children'),
    Input('output-map',         'selectedData'),
    Input('export-whole-area',  'value'),
    prevent_initial_call=True,
)
def handle_lasso(selected_data, whole_area):
    if 'all' in (whole_area or []):
        return [], '  |  Whole area selected'
    if selected_data and selected_data.get('points'):
        cell_ids = []
        for pt in selected_data['points']:
            if 'text' in pt:
                try:
                    cell_ids.append(int(pt['text']))
                except Exception:
                    pass
        if cell_ids:
            return cell_ids, f'  |  {len(cell_ids)} cells selected via lasso/box'
    return [], '  |  or use lasso/box on the map to select cells'

# ── Date dropdowns: disable when whole period checked ─────────────────────────
@app.callback(
    Output('export-start-year',  'disabled'),
    Output('export-start-month', 'disabled'),
    Output('export-start-day',   'disabled'),
    Output('export-end-year',    'disabled'),
    Output('export-end-month',   'disabled'),
    Output('export-end-day',     'disabled'),
    Input('export-whole-period', 'value'),
)
def toggle_date_dropdowns(whole_period):
    disabled = 'whole' in (whole_period or [])
    return [disabled] * 6

# ── Merge categorised export checklists → export-vars store ──────────────────
@app.callback(
    Output('export-vars', 'data'),
    Input('export-vars-flux', 'value'),
    Input('export-vars-soil', 'value'),
    Input('export-vars-crop', 'value'),
)
def merge_export_vars(flux, soil, crop):
    return (flux or []) + (soil or []) + (crop or [])

# ── Export modal toggle ───────────────────────────────────────────────────────
@app.callback(
    Output('export-modal', 'is_open'),
    Input('export-modal-open',  'n_clicks'),
    Input('export-modal-close', 'n_clicks'),
    State('export-modal', 'is_open'),
    prevent_initial_call=True,
)
def toggle_export_modal(open_n, close_n, is_open):
    return not is_open

# ── Time series ribbon text ───────────────────────────────────────────────────
@app.callback(
    Output('ts-ribbon-text', 'children'),
    Input('sel-out-cell',   'data'),
    Input('sel-crop',       'data'),
    Input('sel-season',     'data'),
    Input('sel-out-period', 'data'),
)
def update_ts_ribbon_text(cell_id, crop, season, period):
    if cell_id is None:
        return 'Select a cell on the map to view time series'
    meta = cell_meta.get(cell_id, {})
    period_label = 'Full simulation' if period == 'full' else season
    return (f"Selected: Cell {cell_id}  |  "
            f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
            f"Crop: {crop}  |  Season: {period_label}")

@app.callback(
    Output('input-ribbon-text', 'children'),
    Input('sel-in-cell',   'data'),
    Input('sel-clim-var',  'data'),
    Input('sel-season',    'data'),
    Input('sel-in-period', 'data'),
)
def update_input_ribbon_text(cell_id, clim_var, season, period):
    if cell_id is None:
        return 'Select a cell on the map to view time series'
    meta = cell_meta.get(cell_id, {})
    period_label = 'Full simulation' if period == 'full' else season
    var_label = CLIMATE_VARIABLES.get(clim_var, {}).get('label', clim_var)
    return (f"Selected: Cell {cell_id}  |  "
            f"Location: ({meta.get('x', 0):.3f}, {meta.get('y', 0):.3f})  |  "
            f"Variable: {var_label}  |  Season: {period_label}")

# ── Output map: data layer (Patch only z/text/colorscale — GeoJSON stays in browser) ──
@app.callback(
    Output('output-map', 'figure', allow_duplicate=True),
    Input('sel-crop',    'data'),
    Input('sel-season',  'data'),
    Input('sel-map-var', 'data'),
    Input('sel-agg',     'data'),
    prevent_initial_call=True,
)
def patch_output_map_data(sel_crop, sel_season, sel_map_var, sel_agg):
    var_info = MAP_VARIABLES[sel_map_var]
    agg_func = sel_agg if sel_agg in ['mean', 'sum'] else var_info['default_agg']

    if sel_season == 'all':
        subset = precomputed_agg.get((sel_crop, sel_map_var, agg_func))
        if subset is None:
            patched = Patch()
            patched['data'][1]['locations'] = []
            patched['data'][1]['z']         = []
            patched['data'][1]['text']      = []
            return patched
        subset    = subset.copy()
        agg_label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        vmin, vmax = crop_var_range_all[sel_crop][f'{sel_map_var}_{agg_func}']
    else:
        subset    = summary[(summary['crop_irr'] == sel_crop) & (summary['season_label'] == sel_season)].copy()
        agg_label = sel_season
        vmin, vmax = crop_var_range[sel_crop][sel_map_var]

    subset['cell_id_str'] = subset['cell_id'].astype(int).astype(str)

    hover_texts = (
        '<b>Cell ' + subset['cell_id'].astype(int).astype(str) + '</b><br>'
        + 'Lon: ' + subset['x'].map('{:.3f}'.format) + ' | Lat: ' + subset['y'].map('{:.3f}'.format) + '<br>'
        + 'Crop: ' + subset['crop'].str.capitalize() + ' (' + subset['irrigation'] + ')<br>'
        + f'Period: {agg_label}<br>'
        + '──────────────────<br>'
        + var_info['label'] + ': ' + subset[sel_map_var].map('{:.3f}'.format) + '<br>'
        + '<i>Click to view time series</i>'
    ).tolist()

    patched = Patch()
    patched['data'][1]['locations']                 = subset['cell_id_str'].tolist()
    patched['data'][1]['z']                         = subset[sel_map_var].tolist()
    patched['data'][1]['zmin']                      = float(vmin)
    patched['data'][1]['zmax']                      = float(vmax)
    patched['data'][1]['colorscale']                = var_info['sum_colorscale'] if agg_func == 'sum' else var_info['colorscale']
    patched['data'][1]['text']                      = hover_texts
    patched['data'][1]['colorbar']['title']['text'] = f"{var_info['label']}<br>({agg_label})"
    return patched


# ── Output map: highlight layers (click + lasso) ──────────────────────────────
@app.callback(
    Output('output-map',  'figure', allow_duplicate=True),
    Input('sel-out-cell', 'data'),
    Input('lasso-cells',  'data'),
    prevent_initial_call=True,
)
def patch_output_map_highlights(sel_cell, lasso_cells):
    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []
    lasso_ids     = [str(c) for c in (lasso_cells or [])]
    lasso_z       = [1] * len(lasso_ids)

    patched = Patch()
    patched['data'][2]['locations'] = sel_locations
    patched['data'][2]['z']         = sel_z
    patched['data'][3]['locations'] = lasso_ids
    patched['data'][3]['z']         = lasso_z
    return patched


# ── Crop calendar info text ───────────────────────────────────────────────────
@app.callback(
    Output('cropcal-info-text', 'children'),
    Input('sel-crop', 'data'),
    Input('sel-tab',  'data'),
)
def update_cropcal_info(sel_crop, sel_tab):
    info = get_cropcal_summary(sel_crop)
    if info is None:
        return 'No crop calendar data found for this crop and irrigation type.'
    return (f"Planting: {info['planting']} (DOY {info['planting_doy']})  |  "
            f"Season length: {info['season_length']} days  |  "
            f"Approx. harvest: {info['harvest']}")


# ── SPAM buttons: show only buttons for the selected crop ─────────────────────
@app.callback(
    Output('spam-btn-container', 'children'),
    Output('sel-spam-var',       'data'),
    Output('input-mode',         'data'),
    Input('sel-crop',    'data'),
    Input({'type': 'spamvar-btn', 'index': ALL}, 'n_clicks'),
    Input('climvar-dd',  'value'),
    State('sel-spam-var', 'data'),
    prevent_initial_call=False,
)
def update_spam_buttons(sel_crop, spam_clicks, clim_val, current_spam_var):
    triggered = ctx.triggered_id

    relevant     = spam_vars_for_crop(sel_crop)
    default_spam = relevant[0] if relevant else ''

    if triggered and isinstance(triggered, dict):
        if triggered.get('type') == 'spamvar-btn':
            active_spam = triggered['index']
            mode = 'spam'
        elif triggered == 'climvar-dd':
            active_spam = current_spam_var or default_spam
            mode = 'climate'
        else:
            active_spam = default_spam
            mode = 'climate'
    else:
        active_spam = default_spam
        mode = 'climate'

    if not relevant:
        buttons = [html.Span('No SPAM data for this crop.',
                             style={'fontFamily': FONT_STACK, 'fontSize': '12px',
                                    'color': '#888'})]
    else:
        buttons = [
            html.Button(
                v.replace('_physical_area', '').replace('_', ' '),
                id={'type': 'spamvar-btn', 'index': v},
                n_clicks=0,
                style=btn_style(v == active_spam and mode == 'spam', 'green'),
            )
            for v in relevant
        ]

    return buttons, active_spam, mode


# ── Input map: data layer (Patch only z/text/colorscale — GeoJSON stays in browser) ──
@app.callback(
    Output('input-map',   'figure', allow_duplicate=True),
    Input('sel-clim-var', 'data'),
    Input('sel-spam-var', 'data'),
    Input('input-mode',   'data'),
    Input('sel-season',   'data'),
    prevent_initial_call=True,
)


def patch_input_map_data(sel_clim_var, sel_spam_var, input_mode, sel_season):
    if input_mode == 'spam' and sel_spam_var:
        if spam_ds is None or sel_spam_var not in spam_ds.data_vars:
            return Patch()
        label   = sel_spam_var.replace('_physical_area', '').replace('_', ' ')
        z_raw   = spam_ds[sel_spam_var].sel(x=_x_da, y=_y_da, method='nearest').values
        z_vals  = np.where(np.isnan(z_raw), 0.0, z_raw).tolist()
        locs    = [str(int(c)) for c in _cell_ids_arr]
        vmin, vmax = 0.0, float(max(z_vals)) if max(z_vals) > 0 else 1.0
        texts   = [
            f"<b>Cell {cid}</b><br>Lon: {cell_meta[cid]['x']:.3f} | Lat: {cell_meta[cid]['y']:.3f}<br>{label}: {val:.2f} ha"
            for cid, val in zip(_cell_ids_arr.tolist(), z_vals)
        ]
        colorscale = 'YlGn'
        cb_title   = f"{label}<br>(ha)"
    else:
        arr = get_climate_map_values(sel_clim_var, sel_season)
        if arr is None:
            return Patch()
        var_info   = CLIMATE_VARIABLES[sel_clim_var]
        z_vals     = arr.sel(x=_x_da, y=_y_da, method='nearest').values.tolist()
        locs       = [str(int(c)) for c in _cell_ids_arr]
        vmin, vmax = float(min(z_vals)), float(max(z_vals))
        period_label = 'All years (daily mean)' if sel_season == 'all' else f'{sel_season} (daily mean)'
        texts = [
            f"<b>Cell {cid}</b><br>Lon: {cell_meta[cid]['x']:.3f} | Lat: {cell_meta[cid]['y']:.3f}<br>{var_info['map_label']}: {val:.3f} {var_info['unit']}<br><i>Click to view time series</i>"
            for cid, val in zip(_cell_ids_arr.tolist(), z_vals)
        ]
        colorscale = var_info['colorscale']
        cb_title = f"{var_info['unit']}<br>({period_label})"

    patched = Patch()
    patched['data'][1]['locations']                 = locs
    patched['data'][1]['z']                         = z_vals
    patched['data'][1]['zmin']                      = vmin
    patched['data'][1]['zmax']                      = vmax
    patched['data'][1]['colorscale']                = colorscale
    patched['data'][1]['text']                      = texts
    patched['data'][1]['colorbar']['title']['text'] = cb_title
    return patched


# ── Input map: highlight layer (click) ────────────────────────────────────────
@app.callback(
    Output('input-map',  'figure', allow_duplicate=True),
    Input('sel-in-cell', 'data'),
    prevent_initial_call=True,
)
def patch_input_map_highlight(sel_cell):
    sel_locations = [str(sel_cell)] if sel_cell is not None else []
    sel_z         = [1] if sel_cell is not None else []
    patched = Patch()
    patched['data'][2]['locations'] = sel_locations
    patched['data'][2]['z']         = sel_z
    return patched

# ── Output time series ────────────────────────────────────────────────────────
@app.callback(
    Output('output-ts',           'figure'),
    Output('output-ts-container', 'style'),
    Input('sel-out-cell',   'data'),
    Input('sel-season',     'data'),
    Input('sel-daily-var',  'data'),
    Input('sel-out-period', 'data'),
    Input('out-ts-clicks',  'data'),
)
def update_output_ts(cell_id, season_label, daily_var, ts_period, ts_clicks):
    effective_period = 'full' if season_label == 'all' else ts_period
    effective_season = season_list[0] if season_label == 'all' else season_label
    if cell_id is None:
        return (build_output_ts(None, effective_season, daily_var, effective_period, ts_clicks),
                {'display': 'none'})
    return (build_output_ts(cell_id, effective_season, daily_var, effective_period, ts_clicks),
            {'display': 'block', 'maxWidth': '100%', 'margin': '0 auto'})

# ── Input time series ─────────────────────────────────────────────────────────
@app.callback(
    Output('input-ts',           'figure'),
    Output('input-ts-container', 'style'),
    Input('sel-in-cell',   'data'),
    Input('sel-clim-var',  'data'),
    Input('sel-season',    'data'),
    Input('sel-in-period', 'data'),
    Input('in-ts-clicks',  'data'),
    Input('sel-crop',      'data'),
)
def update_input_ts(cell_id, clim_var, season_label, ts_period, ts_clicks, sel_crop):
    effective_period = 'full' if season_label == 'all' else ts_period
    effective_season = season_list[0] if season_label == 'all' else season_label
    if cell_id is None:
        return (build_input_ts(None, clim_var, effective_season, effective_period,
                               ts_clicks, sel_crop_irr=sel_crop),
                {'display': 'none'})
    return (build_input_ts(cell_id, clim_var, effective_season, effective_period,
                           ts_clicks, sel_crop_irr=sel_crop),
            {'display': 'block', 'maxWidth': '100%', 'margin': '0 auto'})

# ── TS click handlers ─────────────────────────────────────────────────────────
def _handle_click(click_data, ts_clicks):
    if click_data is None:
        return ts_clicks
    clicked_date = click_data['points'][0]['x']
    count = ts_clicks['count']
    if count == 0:
        return {'count': 1, 'start': clicked_date, 'end': None}
    elif count == 1:
        start = ts_clicks['start']
        if clicked_date < start:
            start, clicked_date = clicked_date, start
        return {'count': 2, 'start': start, 'end': clicked_date}
    return {'count': 0, 'start': None, 'end': None}

@app.callback(Output('out-ts-clicks', 'data'),
              Input('output-ts', 'clickData'),
              State('out-ts-clicks', 'data'),
              prevent_initial_call=True)
def handle_out_ts_click(click_data, ts_clicks):
    return _handle_click(click_data, ts_clicks)

@app.callback(Output('in-ts-clicks', 'data'),
              Input('input-ts', 'clickData'),
              State('in-ts-clicks', 'data'),
              prevent_initial_call=True)
def handle_in_ts_click(click_data, ts_clicks):
    return _handle_click(click_data, ts_clicks)

@app.callback(
    Output('out-ts-clicks', 'data', allow_duplicate=True),
    Input('sel-out-cell',  'data'),
    Input('sel-season',    'data'),
    Input('sel-daily-var', 'data'),
    prevent_initial_call=True,
)
def reset_out_clicks(_, __, ___):
    return {'count': 0, 'start': None, 'end': None}

@app.callback(
    Output('in-ts-clicks', 'data', allow_duplicate=True),
    Input('sel-in-cell',  'data'),
    Input('sel-season',   'data'),
    Input('sel-clim-var', 'data'),
    prevent_initial_call=True,
)
def reset_in_clicks(_, __, ___):
    return {'count': 0, 'start': None, 'end': None}

# ── Export ────────────────────────────────────────────────────────────────────
@app.callback(
    Output('export-status', 'children'),
    Input('export-btn',          'n_clicks'),
    State('export-vars',         'data'),
    State('export-whole-period', 'value'),
    State('export-start-year',   'value'),
    State('export-start-month',  'value'),
    State('export-start-day',    'value'),
    State('export-end-year',     'value'),
    State('export-end-month',    'value'),
    State('export-end-day',      'value'),
    State('export-whole-area',   'value'),
    State('lasso-cells',         'data'),
    State('export-format',       'value'),
    prevent_initial_call=True,
)
def run_export(n_clicks, export_vars, whole_period,
               start_year, start_month, start_day,
               end_year,   end_month,   end_day,
               whole_area, lasso_cells, formats):

    if not export_vars:
        return 'Select at least one variable.'
    if not formats:
        return 'Select at least one format.'

    if 'whole' in (whole_period or []):
        start_date = sim_start
        end_date   = sim_end
    else:
        try:
            start_date = safe_date(start_year, start_month, start_day)
            end_date   = safe_date(end_year,   end_month,   end_day)
        except Exception as e:
            return f'Invalid date: {e}'
        if start_date > end_date:
            return 'Start date must be before end date.'

    if 'all' in (whole_area or []) or not lasso_cells:
        selected_cells = list(cell_meta.keys())
    else:
        selected_cells = lasso_cells

    status = export_data(selected_cells, export_vars,
                         str(start_date.date()), str(end_date.date()), formats)
    return status

@app.callback(
    Output('export-btn-wrapper', 'style'),
    Input('sel-tab', 'data'),
)
def toggle_export_btn(sel_tab):
    base = {'position': 'absolute', 'bottom': '14px', 'left': '12px', 'right': '12px'}
    if sel_tab == 'output':
        return {**base, 'display': 'block'}
    return {**base, 'display': 'none'}

# ── Export: constrain end date dropdowns based on start date ─────────────────
@app.callback(
    Output('export-end-year',  'options'),
    Output('export-end-year',  'value'),
    Output('export-end-month', 'options'),
    Output('export-end-month', 'value'),
    Output('export-end-day',   'options'),
    Output('export-end-day',   'value'),
    Input('export-start-year',   'value'),
    Input('export-start-month',  'value'),
    Input('export-start-day',    'value'),
    State('export-end-year',     'value'),
    State('export-end-month',    'value'),
    State('export-end-day',      'value'),
)
def constrain_end_date(sy, sm, sd, ey, em, ed):
    import calendar
    year_opts  = [{'label': str(y), 'value': y} for y in years if y >= sy]
    new_ey     = ey if ey >= sy else sy
    if new_ey == sy:
        month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(sm, 13)]
        new_em     = em if em >= sm else sm
    else:
        month_opts = [{'label': f'{m:02d}', 'value': m} for m in range(1, 13)]
        new_em     = em
    max_day = calendar.monthrange(new_ey, new_em)[1]
    if new_ey == sy and new_em == sm:
        day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(sd, max_day + 1)]
        new_ed   = ed if ed >= sd else sd
    else:
        day_opts = [{'label': f'{d:02d}', 'value': d} for d in range(1, max_day + 1)]
        new_ed   = min(ed, max_day)
    return year_opts, new_ey, month_opts, new_em, day_opts, new_ed


if __name__ == '__main__':
    app.run(debug=False, port=PORT)
