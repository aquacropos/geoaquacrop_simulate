# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        USER CONFIGURATION                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

SUMMARY_PKL   = '../outputs/summary_results_20260501_144727.pkl'    # simulation output files
DAILY_PKL     = '../outputs/daily_results_20260501_144727.pkl'
GEOJSON_PATH  = '../aquacropgrid-preproc/inputdata/germany/niedersachsen.geojson'  # polygon input file (area of interest)
PROCESSED_DIR = '../aquacropgrid-preproc/processed'    # preprocessing outputs (climate, soil, phenology, crop areas)
EXPORT_DIR    = '../outputs/exports'    # location to save data files via export function in visualisation (NetCDF, GeoTIFF, CSV) 
CELL_RES      = 0.05 # same as the preprocessing grid resolution in degrees
PORT          = 8050
MAP_ZOOM      = 10
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
    'gdd_cum':      {'label': 'Cumulative GDD',                     'table': 'crop_growth', 'color': '#d35400'},
    'z_root':       {'label': 'Root Depth (m)',                     'table': 'crop_growth', 'color': '#795548'},
    'DryYield':     {'label': 'Dry Yield (tonne/ha)',               'table': 'crop_growth', 'color': '#c0392b'},
}

CLIMATE_VARIABLES = {
    'MaxTemp':       {'label': 'Max Temperature (°C)',    'color': '#e74c3c', 'colorscale': 'RdYlBu_r'},
    'MinTemp':       {'label': 'Min Temperature (°C)',    'color': '#3498db', 'colorscale': 'RdYlBu_r'},
    'Precipitation': {'label': 'Precipitation (mm/day)', 'color': '#2980b9', 'colorscale': 'Blues'   },
    'ReferenceET':   {'label': 'Reference ET (mm/day)',  'color': '#e67e22', 'colorscale': 'YlOrBr'  },
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
# rasterio    — pip install rasterio  (for GeoTIFF export)
# json        — built-in

import pickle
import os
import pandas as pd
import numpy as np
import xarray as xr
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx, ALL
import json
import glob

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
    if not isinstance(df, pd.DataFrame) or df.empty or 'cell_id' not in df.columns or 'error' in df.columns:
        continue
    row = df.iloc[0]
    cid = int(row['cell_id'])
    cell_meta[cid] = {
        'x':          float(row['x']),
        'y':          float(row['y']),
        'crop':       row['crop'],
        'irrigation': row['irrigation'],
        'list_idx':   i,
    }
    cell_id_to_idx[cid] = i

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
#years      = sorted(date_index.year.unique())
years = [yr for yr in sorted(date_index.year.unique())
         if (date_index.year == yr).sum() > 5]

year_rows = {}
for yr in years:
    indices = np.where(date_index.year == yr)[0]
    year_rows[str(yr)] = (int(indices[0]), int(indices[-1]))

wf0 = daily_raw[0]['water_flux'].reset_index(drop=True)
preseason_end_row  = int(wf0[wf0['season_counter'] == -1.0].index.max())
preseason_end_date = sim_start + pd.to_timedelta(preseason_end_row, unit='D')

climate_ds = {}
for var in climate_var_keys:
    matches = glob.glob(os.path.join(PROCESSED_DIR, f'{var}*.nc'))
    if matches:
        climate_ds[var] = xr.open_dataset(matches[0])

cropcal_ds = xr.open_dataset(os.path.join(PROCESSED_DIR, 'cropcalendar.nc'),
                             decode_timedelta=True)

# ── SPAM: load and keep only variables with data ───────────────────────────────
spam_files = glob.glob(os.path.join(PROCESSED_DIR, 'spam*_physical_area.nc'))
spam_path  = spam_files[0] if spam_files else None
spam_ds   = xr.open_dataset(spam_path) if os.path.exists(spam_path) else None

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
    return []  # no data for this crop/irrigation combination

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
#all_cell_ids = [str(int(c)) for c in cells['cell_id'].unique()]
all_cell_ids = [str(cid) for cid in cell_meta.keys()]
center_lat   = summary['y'].mean()
center_lon   = summary['x'].mean()

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

crop_var_range_all = {}
for ci in crop_irr_list:
    crop_var_range_all[ci] = {}
    for var in map_var_keys:
        for agg in ['mean', 'sum']:
            grouped  = summary[summary['crop_irr'] == ci].groupby('cell_id')[var]
            agg_vals = grouped.sum() if agg == 'sum' else grouped.mean()
            if var == 'Seasonal irrigation (mm)':
                vmax = agg_vals.max() if agg_vals.max() > 0 else 1
                crop_var_range_all[ci][f'{var}_{agg}'] = (0, vmax)
            else:
                crop_var_range_all[ci][f'{var}_{agg}'] = (agg_vals.min(), agg_vals.max())

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
        dict(source=region_geojson, type='fill', color='rgba(26,111,175,0.06)'),
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
        grouped   = summary[summary['crop_irr'] == ci].groupby('cell_id')[map_var]
        agg_vals  = grouped.sum() if agg_func == 'sum' else grouped.mean()
        agg_df    = agg_vals.reset_index()
        agg_df.columns = ['cell_id', map_var]
        agg_df    = agg_df.merge(
            summary[['cell_id', 'x', 'y', 'crop', 'irrigation']].drop_duplicates('cell_id'),
            on='cell_id')
        subset    = agg_df.copy()
        agg_label = f"{'Sum' if agg_func == 'sum' else 'Avg'} all years"
        vmin, vmax = crop_var_range_all[ci][f'{map_var}_{agg_func}']
    else:
        subset    = summary[(summary['crop_irr'] == ci) & (summary['season_label'] == season)].copy()
        agg_label = season
        vmin, vmax = crop_var_range[ci][map_var]

    subset['cell_id_str'] = subset['cell_id'].astype(int).astype(str)

    hover_texts = []
    for _, row in subset.iterrows():
        hover_texts.append(
            f"<b>Cell {int(row.cell_id)}</b><br>"
            f"Lon: {row.x:.3f} | Lat: {row.y:.3f}<br>"
            f"Crop: {row.crop.capitalize()} ({row.irrigation})<br>"
            f"Period: {agg_label}<br>"
            f"──────────────────<br>"
            f"{var_info['label']}: {row[map_var]:.3f}<br>"
            f"<i>Click to view time series</i>"
        )

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
            marker_opacity=0.78, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['label']}<br>({agg_label})", font=dict(size=11)),
                thickness=16, len=0.55, x=1.01,
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

    locations, z_vals, hover_texts = [], [], []
    for cid, meta in cell_meta.items():
        val = float(arr.sel(x=meta['x'], y=meta['y'], method='nearest').values)
        locations.append(str(cid))
        z_vals.append(val)
        hover_texts.append(
            f"<b>Cell {cid}</b><br>"
            f"Lon: {meta['x']:.3f} | Lat: {meta['y']:.3f}<br>"
            f"{var_info['label']}: {val:.3f}<br>"
            f"<i>Click to view time series</i>"
        )

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
            marker_opacity=0.78, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(text=f"{var_info['label']}<br>({period_label})", font=dict(size=11)),
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
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision=f'{climate_var}-{season_label}',
        )
    )


def build_spam_map(spam_var, sel_cell=None, relayout_data=None):
    if spam_ds is None or spam_var not in spam_ds.data_vars:
        return go.Figure()

    locations, z_vals, hover_texts = [], [], []
    for cid, meta in cell_meta.items():
        val = float(spam_ds[spam_var].sel(x=meta['x'], y=meta['y'], method='nearest').values)
        if np.isnan(val):
            val = 0.0
        locations.append(str(cid))
        z_vals.append(val)
        label = spam_var.replace('_physical_area', '').replace('_', ' ')
        hover_texts.append(
            f"<b>Cell {cid}</b><br>"
            f"Lon: {meta['x']:.3f} | Lat: {meta['y']:.3f}<br>"
            f"{label}: {val:.2f} ha"
        )

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
            marker_opacity=0.78, marker_line_width=0.8, marker_line_color='white',
            colorbar=dict(
                title=dict(
                    text=spam_var.replace('_physical_area', '').replace('_', ' ') + '<br>(ha)',
                    font=dict(size=11)),
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
            height=MAP_HEIGHT, paper_bgcolor='white', uirevision='constant-spam',
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
# ║                        BUTTON STYLES                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def btn_style(active, color):
    palette = {
        'blue':   ('#1a6faf', '#e8f0fb'),
        'green':  ('#4caf50', '#e8f4ea'),
        'orange': ('#e65100', '#fff3e0'),
        'purple': ('#6a1b9a', '#f3e5f5'),
        'teal':   ('#00796b', '#e0f2f1'),
        'red':    ('#c0392b', '#fdecea'),
    }
    border, bg = palette[color]
    base = dict(padding='5px 13px', margin='2px', borderRadius='4px',
                cursor='pointer', fontSize='12px', fontFamily='Arial',
                border=f'1px solid {border}')
    if active:
        return {**base, 'backgroundColor': border, 'color': 'white'}
    return {**base, 'backgroundColor': bg, 'color': '#333'}

def label_style():
    return {'fontFamily': 'Arial', 'fontWeight': 'bold',
            'marginRight': '6px', 'fontSize': '13px'}

def row_style(mb='5px'):
    return {'textAlign': 'center', 'marginBottom': mb,
            'maxWidth': '1300px', 'margin': f'0 auto {mb}'}

def dd_style(w='80px'):
    return {'display': 'inline-block', 'width': w,
            'fontSize': '12px', 'marginLeft': '4px',
            'verticalAlign': 'middle'}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        APP LAYOUT                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

app = dash.Dash(__name__)

app.layout = html.Div([

    html.H2('AquaCrop Gridded Explorer',
            style={'textAlign': 'center', 'fontFamily': 'Arial', 'marginBottom': '8px'}),

    # ── Tab toggle ─────────────────────────────────────────────────────────────
    html.Div([
        html.Button('Simulation Outputs', id={'type': 'tab-btn', 'index': 'output'}, n_clicks=0,
                    style=btn_style(True, 'blue')),
        html.Button('Inputs',             id={'type': 'tab-btn', 'index': 'input'},  n_clicks=0,
                    style=btn_style(False, 'red')),
    ], style={'textAlign': 'center', 'marginBottom': '10px'}),

    # ── Shared: Crop buttons ───────────────────────────────────────────────────
    html.Div([
        html.Span('Crop & Irrigation:', style=label_style()),
        *[html.Button(ci, id={'type': 'crop-btn', 'index': ci}, n_clicks=0,
                      style=btn_style(ci == crop_irr_list[0], 'blue'))
          for ci in crop_irr_list],
    ], style=row_style('5px')),

    # ── Shared: Season buttons ─────────────────────────────────────────────────
    html.Div([
        html.Span('Season:', style=label_style()),
        *[html.Button(s, id={'type': 'season-btn', 'index': s}, n_clicks=0,
                      style=btn_style(s == season_list[0], 'green'))
          for s in season_list],
        html.Button('All years', id={'type': 'season-btn', 'index': 'all'}, n_clicks=0,
                    style=btn_style(False, 'teal')),
    ], style=row_style('5px')),

    # ── Aggregation row (output tab, all years only) ───────────────────────────
    html.Div(
        id='agg-row',
        children=[
            html.Span('Aggregation:', style=label_style()),
            html.Button('Mean', id={'type': 'agg-btn', 'index': 'mean'}, n_clicks=0,
                        style=btn_style(True, 'teal')),
            html.Button('Sum',  id={'type': 'agg-btn', 'index': 'sum'},  n_clicks=0,
                        style=btn_style(False, 'teal')),
        ],
        style={'textAlign': 'center', 'maxWidth': '1300px',
               'margin': '0 auto 5px', 'display': 'none'},
    ),

    # ── Output tab controls ────────────────────────────────────────────────────
    html.Div(id='output-controls', children=[
        html.Div([
            html.Span('Map variable:', style=label_style()),
            *[html.Button(MAP_VARIABLES[v]['label'],
                          id={'type': 'mapvar-btn', 'index': v}, n_clicks=0,
                          style=btn_style(v == map_var_keys[0], 'orange'))
              for v in map_var_keys],
        ], style=row_style('5px')),
        html.Div([
            html.Span('Daily variable:', style=label_style()),
            *[html.Button(DAILY_VARIABLES[v]['label'],
                          id={'type': 'dailyvar-btn', 'index': v}, n_clicks=0,
                          style=btn_style(v == daily_var_keys[0], 'purple'))
              for v in daily_var_keys],
        ], style=row_style('12px')),
    ]),


    # ── Input tab controls ─────────────────────────────────────────────────────
    html.Div(id='input-controls', children=[
        html.Div([
            html.Span('Climate variable:', style=label_style()),
            *[html.Button(CLIMATE_VARIABLES[v]['label'],
                          id={'type': 'climvar-btn', 'index': v}, n_clicks=0,
                          style=btn_style(v == climate_var_keys[0], 'red'))
              for v in climate_var_keys],
        ], style=row_style('5px')),
        html.Div(id='spam-btn-row', children=[
            html.Span('Crop area (SPAM):', style=label_style()),
            html.Span(id='spam-btn-container', children=[]),
        ], style=row_style('12px')),
    ], style={'display': 'none'}),

    # ── Output panel ───────────────────────────────────────────────────────────
    html.Div(id='output-panel', children=[
        dcc.Graph(
            id='output-map',
            figure=build_output_map(crop_irr_list[0], season_list[0], map_var_keys[0], 'mean'),
            config={'scrollZoom': True, 'modeBarButtonsToAdd': ['lasso2d', 'select2d']},
            style={'maxWidth': '1300px', 'margin': '0 auto'},
        ),
        html.Div(id='output-ts-container', children=[
            html.Div([
                html.Span('Time series period:', style=label_style()),
                html.Button('Selected season', id={'type': 'out-period-btn', 'index': 'season'}, n_clicks=0,
                            style=btn_style(True, 'purple')),
                html.Button('Full simulation', id={'type': 'out-period-btn', 'index': 'full'},   n_clicks=0,
                            style=btn_style(False, 'purple')),
            ], style={'textAlign': 'right', 'maxWidth': '1300px',
                      'margin': '8px auto 2px', 'paddingRight': '20px'}),
            dcc.Graph(id='output-ts',
                      figure=build_output_ts(None, season_list[0], daily_var_keys[0], 'season')),
        ], style={'display': 'none'}),

        # ── Export panel ───────────────────────────────────────────────────────
        html.Hr(style={'maxWidth': '1300px', 'margin': '24px auto 16px'}),
        html.H3('Export Gridded Output',
                style={'textAlign': 'center', 'fontFamily': 'Arial',
                       'fontSize': '15px', 'marginBottom': '14px'}),

        # Variables
        html.Div([
            html.Span('Variables:', style=label_style()),
            dcc.Checklist(
                id='export-vars',
                options=[{'label': f'  {DAILY_VARIABLES[v]["label"]}', 'value': v}
                         for v in daily_var_keys],
                value=[daily_var_keys[0]],
                inline=True,
                style={'fontFamily': 'Arial', 'fontSize': '12px', 'display': 'inline'},
                inputStyle={'marginRight': '4px', 'marginLeft': '12px'},
            ),
        ], style=row_style('10px')),

        # Period
        html.Div([
            html.Span('Period:', style=label_style()),
            dcc.Checklist(
                id='export-whole-period',
                options=[{'label': '  Whole simulation', 'value': 'whole'}],
                value=[],
                inline=True,
                style={'display': 'inline', 'fontFamily': 'Arial', 'fontSize': '12px'},
                inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
            ),
            html.Span('  From:', style={'fontFamily': 'Arial', 'fontSize': '12px', 'marginLeft': '16px'}),
            dcc.Dropdown(id='export-start-year',
                         options=[{'label': str(y), 'value': y} for y in years],
                         value=years[0], clearable=False, style=dd_style('80px')),
            dcc.Dropdown(id='export-start-month',
                         options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                         value=1, clearable=False, style=dd_style('70px')),
            dcc.Dropdown(id='export-start-day',
                         options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                         value=1, clearable=False, style=dd_style('70px')),
            html.Span('  To:', style={'fontFamily': 'Arial', 'fontSize': '12px', 'marginLeft': '12px'}),
            dcc.Dropdown(id='export-end-year',
                         options=[{'label': str(y), 'value': y} for y in years],
                         value=years[-1], clearable=False, style=dd_style('80px')),
            dcc.Dropdown(id='export-end-month',
                         options=[{'label': f'{m:02d}', 'value': m} for m in range(1, 13)],
                         value=12, clearable=False, style=dd_style('70px')),
            dcc.Dropdown(id='export-end-day',
                         options=[{'label': f'{d:02d}', 'value': d} for d in range(1, 32)],
                         value=31, clearable=False, style=dd_style('70px')),
        ], style=row_style('10px')),

        # Cells
        html.Div([
            html.Span('Cells:', style=label_style()),
            dcc.Checklist(
                id='export-whole-area',
                options=[{'label': '  Whole area', 'value': 'all'}],
                value=['all'],
                inline=True,
                style={'display': 'inline', 'fontFamily': 'Arial', 'fontSize': '12px'},
                inputStyle={'marginRight': '4px', 'marginLeft': '4px'},
            ),
            html.Span(id='export-cell-label',
                      children='  |  or use lasso/box on the map above to select cells',
                      style={'fontFamily': 'Arial', 'fontSize': '12px',
                             'color': '#888888', 'marginLeft': '8px'}),
        ], style=row_style('10px')),

        # Format
        html.Div([
            html.Span('Format:', style=label_style()),
            dcc.Checklist(
                id='export-format',
                options=[
                    {'label': '  NetCDF (.nc)',   'value': 'nc'},
                    {'label': '  GeoTIFF (.tif)', 'value': 'tif'},
                    {'label': '  CSV (.csv)',      'value': 'csv'},
                ],
                value=['csv'],
                inline=True,
                style={'fontFamily': 'Arial', 'fontSize': '12px', 'display': 'inline'},
                inputStyle={'marginRight': '4px', 'marginLeft': '14px'},
            ),
        ], style=row_style('14px')),

        # Export button + status
        html.Div([
            html.Button('Export', id='export-btn', n_clicks=0,
                        style={**btn_style(True, 'blue'),
                               'fontSize': '14px', 'padding': '8px 32px'}),
            html.Span(id='export-status', children='',
                      style={'fontFamily': 'Arial', 'fontSize': '12px',
                             'marginLeft': '16px', 'color': '#27ae60'}),
        ], style={'textAlign': 'center', 'marginBottom': '24px'}),

    ]),

# ── Input panel ────────────────────────────────────────────────────────────
    html.Div(id='input-panel', children=[

        # ── Crop calendar info ─────────────────────────────────────────────────
        html.Div([
            html.Span('Crop calendar:', style=label_style()),
            html.Span(id='cropcal-info-text', children='—',
                      style={'fontFamily': 'Arial', 'fontSize': '12px', 'color': '#555'}),
        ], style={'textAlign': 'center', 'maxWidth': '1300px',
                  'margin': '0 auto 5px', 'padding': '3px 0'}),

        dcc.Graph(
            id='input-map',
            figure=build_input_map(climate_var_keys[0], season_list[0]),
            config={'scrollZoom': True},
            style={'maxWidth': '1300px', 'margin': '0 auto'},
        ),
        html.Div(id='input-ts-container', children=[
            html.Div([
                html.Span('Time series period:', style=label_style()),
                html.Button('Selected season', id={'type': 'in-period-btn', 'index': 'season'}, n_clicks=0,
                            style=btn_style(True, 'red')),
                html.Button('Full simulation', id={'type': 'in-period-btn', 'index': 'full'},   n_clicks=0,
                            style=btn_style(False, 'red')),
            ], style={'textAlign': 'right', 'maxWidth': '1300px',
                      'margin': '8px auto 2px', 'paddingRight': '20px'}),
                
            dcc.Graph(id='input-ts',
                      figure=build_input_ts(None, climate_var_keys[0], season_list[0], 'season')),
        ], style={'display': 'none'}),
    ], style={'display': 'none'}),

    # ── Stores ────────────────────────────────────────────────────────────────
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

], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '10px'})

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        CALLBACKS                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@app.callback(Output('sel-tab', 'data'),
              Input({'type': 'tab-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_tab(_):
    t = ctx.triggered_id
    return t['index'] if t else 'output'

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

@app.callback(Output('sel-crop', 'data'),
              Input({'type': 'crop-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_crop(_):
    t = ctx.triggered_id
    return t['index'] if t else crop_irr_list[0]

@app.callback(Output('sel-season', 'data'),
              Input({'type': 'season-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_season(_):
    t = ctx.triggered_id
    return t['index'] if t else season_list[0]

@app.callback(Output('sel-map-var', 'data'),
              Input({'type': 'mapvar-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_map_var(_):
    t = ctx.triggered_id
    return t['index'] if t else map_var_keys[0]

@app.callback(Output('sel-daily-var', 'data'),
              Input({'type': 'dailyvar-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_daily_var(_):
    t = ctx.triggered_id
    return t['index'] if t else daily_var_keys[0]

@app.callback(Output('sel-clim-var', 'data'),
              Input({'type': 'climvar-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_clim_var(_):
    t = ctx.triggered_id
    return t['index'] if t else climate_var_keys[0]

@app.callback(Output('sel-agg', 'data'),
              Input({'type': 'agg-btn', 'index': ALL}, 'n_clicks'),
              prevent_initial_call=True)
def set_agg(_):
    t = ctx.triggered_id
    return t['index'] if t else 'mean'

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

@app.callback(Output('sel-out-cell', 'data'),
              Input('output-map', 'clickData'),
              prevent_initial_call=True)
def set_out_cell(click_data):
    if click_data is None:
        return None
    pt = click_data['points'][0]
    # Click on choropleth tile
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
        # Centroid scatter points carry cell_id as text
        cell_ids = []
        for pt in selected_data['points']:
            if 'text' in pt:
                try:
                    cell_ids.append(int(pt['text']))
                except Exception:
                    pass
        if cell_ids:
            return cell_ids, f'  |  {len(cell_ids)} cells selected via lasso/box'

    return [], '  |  or use lasso/box on the map above to select cells'

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

# ── Button styles ─────────────────────────────────────────────────────────────
@app.callback(
    Output({'type': 'tab-btn',        'index': ALL}, 'style'),
    Output({'type': 'crop-btn',       'index': ALL}, 'style'),
    Output({'type': 'season-btn',     'index': ALL}, 'style'),
    Output({'type': 'agg-btn',        'index': ALL}, 'style'),
    Output({'type': 'mapvar-btn',     'index': ALL}, 'style'),
    Output({'type': 'dailyvar-btn',   'index': ALL}, 'style'),
    Output({'type': 'climvar-btn',    'index': ALL}, 'style'),
    Output({'type': 'out-period-btn', 'index': ALL}, 'style'),
    Output({'type': 'in-period-btn',  'index': ALL}, 'style'),
    Input('sel-tab',        'data'),
    Input('sel-crop',       'data'),
    Input('sel-season',     'data'),
    Input('sel-agg',        'data'),
    Input('sel-map-var',    'data'),
    Input('sel-daily-var',  'data'),
    Input('sel-clim-var',   'data'),
    Input('sel-out-period', 'data'),
    Input('sel-in-period',  'data'),
)
def update_btn_styles(sel_tab, sel_crop, sel_season, sel_agg,
                      sel_map_var, sel_daily_var, sel_clim_var,
                      sel_out_period, sel_in_period):
    all_seasons = season_list + ['all']
    return (
        [btn_style(t == sel_tab,         'blue' if t == 'output' else 'red') for t in ['output', 'input']],
        [btn_style(ci == sel_crop,       'blue')   for ci in crop_irr_list],
        [btn_style(s == sel_season,      'green' if s != 'all' else 'teal') for s in all_seasons],
        [btn_style(a == sel_agg,         'teal')   for a  in ['mean', 'sum']],
        [btn_style(v == sel_map_var,     'orange') for v  in map_var_keys],
        [btn_style(v == sel_daily_var,   'purple') for v  in daily_var_keys],
        [btn_style(v == sel_clim_var,    'red')    for v  in climate_var_keys],
        [btn_style(p == sel_out_period,  'purple') for p  in ['season', 'full']],
        [btn_style(p == sel_in_period,   'red')    for p  in ['season', 'full']],
    )

@app.callback(
    Output('agg-row', 'style'),
    Input('sel-season', 'data'),
    Input('sel-tab',    'data'),
)
def toggle_agg_row(sel_season, sel_tab):
    base = {'textAlign': 'center', 'maxWidth': '1300px', 'margin': '0 auto 5px'}
    if sel_season == 'all' and sel_tab == 'output':
        return {**base, 'display': 'block'}
    return {**base, 'display': 'none'}

# ── Output map ────────────────────────────────────────────────────────────────
@app.callback(
    Output('output-map',  'figure'),
    Input('sel-crop',     'data'),
    Input('sel-season',   'data'),
    Input('sel-map-var',  'data'),
    Input('sel-agg',      'data'),
    Input('sel-out-cell', 'data'),
    Input('lasso-cells',  'data'),
    State('output-map',   'relayoutData'),
)
def update_output_map(sel_crop, sel_season, sel_map_var, sel_agg,
                      sel_cell, lasso_cells, relayout_data):
    return build_output_map(sel_crop, sel_season, sel_map_var, sel_agg,
                            sel_cell, lasso_cells, relayout_data)

# ── Crop calendar info text ───────────────────────────────────────────────────
@app.callback(
    Output('cropcal-info-text', 'children'),
    Input('sel-crop', 'data'),
)
def update_cropcal_info(sel_crop):
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
    Input({'type': 'climvar-btn', 'index': ALL}, 'n_clicks'),
    State('sel-spam-var', 'data'),
    prevent_initial_call=False,
)
def update_spam_buttons(sel_crop, spam_clicks, clim_clicks, current_spam_var):
    triggered = ctx.triggered_id

    # Determine which SPAM vars match the selected crop
    relevant = spam_vars_for_crop(sel_crop)
    default_spam = relevant[0] if relevant else ''

    # Determine mode and active SPAM var
    if triggered and isinstance(triggered, dict):
        if triggered.get('type') == 'spamvar-btn':
            active_spam = triggered['index']
            mode = 'spam'
        elif triggered.get('type') == 'climvar-btn':
            active_spam = current_spam_var or default_spam
            mode = 'climate'
        else:
            active_spam = default_spam
            mode = 'climate'
    else:
        active_spam = default_spam
        mode = 'climate'

    # Rebuild buttons for this crop
    if not relevant:
        buttons = [html.Span('No SPAM data for this crop.',
                             style={'fontFamily': 'Arial', 'fontSize': '12px',
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


# ── Input map: handles both climate and SPAM ──────────────────────────────────
@app.callback(
    Output('input-map',   'figure'),
    Input('sel-clim-var', 'data'),
    Input('sel-spam-var', 'data'),
    Input('input-mode',   'data'),
    Input('sel-season',   'data'),
    Input('sel-in-cell',  'data'),
    State('input-map',    'relayoutData'),
)
def update_input_map(sel_clim_var, sel_spam_var, input_mode,
                     sel_season, sel_cell, relayout_data):
    if input_mode == 'spam' and sel_spam_var:
        return build_spam_map(sel_spam_var, sel_cell, relayout_data)
    return build_input_map(sel_clim_var, sel_season, sel_cell, relayout_data)

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
            {'maxWidth': '1300px', 'margin': '10px auto 0', 'display': 'block'})

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
            {'maxWidth': '1300px', 'margin': '10px auto 0', 'display': 'block'})

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
    State('export-vars',         'value'),
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

    # Resolve period
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

    # Resolve cells
    if 'all' in (whole_area or []) or not lasso_cells:
        selected_cells = list(cell_meta.keys())
    else:
        selected_cells = lasso_cells

    status = export_data(selected_cells, export_vars,
                         str(start_date.date()), str(end_date.date()), formats)
    return status


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