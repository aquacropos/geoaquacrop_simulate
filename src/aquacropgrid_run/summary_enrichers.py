"""Derived summary outputs. Add a new metric by writing a function and decorating it."""
import numpy as np

_REGISTRY = []

def enricher(func):
    """Decorator: register a function that adds columns to the summary."""
    _REGISTRY.append(func)
    return func

def apply_all(summary, context):
    """Apply every registered enricher in order. Each one mutates/returns summary."""
    for func in _REGISTRY:
        try:
            summary = func(summary, context)
        except Exception as e:
            context['logger'].warning(f"Enricher {func.__name__} failed: {e}")
    return summary


def _sum_during_season(daily_df, column, crop_obj):
    """Sum a daily column over the growing season (planting to maturity)."""
    if column not in daily_df.columns:
        return np.nan
    # AquaCrop daily outputs have 'dap' (days after planting). Season ends at MaturityCD.
    if 'dap' in daily_df.columns:
        in_season = (daily_df['dap'] >= 1) & (daily_df['dap'] <= crop_obj.MaturityCD)
        return float(daily_df.loc[in_season, column].sum())
    return float(daily_df[column].sum())


# --- Raw seasonal totals (useful on their own + building blocks for WP metrics) ---

@enricher
def add_seasonal_precip(summary, context):
    """Total precipitation during growing season (mm).
    
    AquaCrop-OSPy doesn't expose precipitation in water_flux (only ET components
    and fluxes), so we sum it from the input weather_df using the in-season
    mask derived from water_flux['dap']. Alignment is positional since both are
    daily over the simulation period.
    """
    weather_df = context.get('weather_df')
    daily = context.get('daily')
    if weather_df is None or daily is None:
        summary['seasonal_precip_mm'] = np.nan
        return summary
    
    water_flux = daily['water_flux']
    if 'dap' not in water_flux.columns:
        summary['seasonal_precip_mm'] = np.nan
        return summary
    
    crop_obj = context['crop_obj']
    in_season = (water_flux['dap'] >= 1) & (water_flux['dap'] <= crop_obj.MaturityCD)
    
    n = min(len(in_season), len(weather_df))
    in_season_arr = in_season.values[:n]
    summary['seasonal_precip_mm'] = float(
        weather_df.iloc[:n].loc[in_season_arr, 'Precipitation'].sum()
    )
    return summary


@enricher
def add_seasonal_et(summary, context):
    """Total crop evapotranspiration during growing season (mm) = Tr + Es."""
    daily = context.get('daily')
    if daily is None:
        summary['seasonal_et_mm'] = np.nan
        return summary
    water_flux = daily['water_flux']
    crop_obj = context['crop_obj']
    tr = _sum_during_season(water_flux, 'Tr', crop_obj)
    es = _sum_during_season(water_flux, 'Es', crop_obj)
    summary['seasonal_et_mm'] = tr + es
    summary['seasonal_transpiration_mm'] = tr  # Tr alone is often more interesting
    return summary


@enricher
def add_total_water_input(summary, context):
    """Total water reaching the crop during season: precipitation + irrigation (mm)."""
    precip = summary.get('seasonal_precip_mm', np.nan)
    # AquaCrop column name varies — try common options
    irr = summary.get('Seasonal irrigation (mm)', None)
    if irr is None:
        irr = summary.get('IrrCum', 0)
    try:
        irr_val = float(irr.iloc[0]) if hasattr(irr, 'iloc') else float(irr)
    except (TypeError, ValueError):
        irr_val = 0.0
    try:
        precip_val = float(precip.iloc[0]) if hasattr(precip, 'iloc') else float(precip)
    except (TypeError, ValueError):
        precip_val = np.nan
    summary['total_water_input_mm'] = precip_val + irr_val
    return summary


# --- Derived metrics ---

@enricher
def add_production(summary, context):
    """Production (tonnes) = yield (t/ha) x crop area (ha per cell)."""
    area_ha = context.get('crop_area_ha')
    if area_ha is None or (isinstance(area_ha, float) and np.isnan(area_ha)):
        summary['production_tonnes'] = np.nan
    else:
        summary['production_tonnes'] = summary['Dry yield (tonne/ha)'] * area_ha
    return summary


@enricher
def add_season_length(summary, context):
    """Crop cycle length in days from adjusted phenology."""
    summary['season_length_days'] = context['crop_obj'].MaturityCD
    return summary


@enricher
def add_water_productivity_et(summary, context):
    """Yield per unit seasonal ET (kg/m3). 1 t/ha per 100 mm = 1 kg/m3."""
    et = summary.get('seasonal_et_mm')
    try:
        et_val = float(et.iloc[0]) if hasattr(et, 'iloc') else float(et)
    except (TypeError, ValueError):
        et_val = np.nan
    if not et_val or np.isnan(et_val):
        summary['wp_et_kg_per_m3'] = np.nan
    else:
        summary['wp_et_kg_per_m3'] = (summary['Dry yield (tonne/ha)'] * 100) / et_val
    return summary


@enricher
def add_rainfall_use_efficiency(summary, context):
    """Yield per unit seasonal precipitation (kg/m3) — most meaningful for rainfed."""
    precip = summary.get('seasonal_precip_mm')
    try:
        precip_val = float(precip.iloc[0]) if hasattr(precip, 'iloc') else float(precip)
    except (TypeError, ValueError):
        precip_val = np.nan
    if not precip_val or np.isnan(precip_val):
        summary['rainfall_use_efficiency_kg_per_m3'] = np.nan
    else:
        summary['rainfall_use_efficiency_kg_per_m3'] = (summary['Dry yield (tonne/ha)'] * 100) / precip_val
    return summary


@enricher
def add_irrigation_wp(summary, context):
    """Irrigation water productivity — only meaningful for irrigated runs."""
    if context['config']['irrigation'].lower() != 'irrigated':
        return summary
    irr = summary.get('Seasonal irrigation (mm)')
    try:
        irr_val = float(irr.iloc[0]) if hasattr(irr, 'iloc') else float(irr)
    except (TypeError, ValueError):
        irr_val = np.nan
    if not irr_val or np.isnan(irr_val):
        summary['wp_irrigation_kg_per_m3'] = np.nan
    else:
        summary['wp_irrigation_kg_per_m3'] = (summary['Dry yield (tonne/ha)'] * 100) / irr_val
    return summary