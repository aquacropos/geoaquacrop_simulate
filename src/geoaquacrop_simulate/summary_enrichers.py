"""Derived summary outputs. Add a new metric by writing a function and decorating it."""
import numpy as np
import pandas as pd

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


def _in_season(water_flux, crop_obj):
    """Boolean mask of in-season days (planting to maturity)."""
    return (water_flux['dap'] >= 1) & (water_flux['dap'] <= crop_obj.MaturityCD)


def _per_season(values, water_flux, crop_obj, summary):
    """Sum daily `values` over each growing season, aligned to summary['Season'].

    Grouping by water_flux['season_counter'] gives one total per season, so
    each summary row gets its own season's total. Returns NaN if the inputs
    cannot be aligned.
    """
    if 'season_counter' not in water_flux.columns or 'Season' not in summary:
        return np.nan
    mask = _in_season(water_flux, crop_obj).values
    totals = (values[mask]
              .groupby(water_flux['season_counter'].values[mask])
              .sum())
    return summary['Season'].map(totals).astype(float).values


def _sum_during_season(daily_df, column, crop_obj, summary):
    """Per-season total of a daily water_flux column."""
    if column not in daily_df.columns or 'dap' not in daily_df.columns:
        return np.nan
    return _per_season(daily_df[column].reset_index(drop=True),
                       daily_df.reset_index(drop=True), crop_obj, summary)


def _column(summary, *names, default=np.nan):
    """First of `names` present in the summary, as a float Series."""
    for name in names:
        if name in summary:
            return pd.to_numeric(summary[name], errors='coerce').astype(float)
    return pd.Series(default, index=summary.index, dtype=float)


def _per_unit_water(summary, water):
    """Yield (t/ha) per seasonal water (mm) as kg/m3; NaN where water <= 0."""
    water = water.where(water > 0)
    return summary['Dry yield (tonne/ha)'] * 100 / water


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
    # Positional alignment: both are daily over the simulation period.
    n = min(len(water_flux), len(weather_df))
    flux = water_flux.iloc[:n].reset_index(drop=True)
    precip = weather_df['Precipitation'].iloc[:n].reset_index(drop=True)
    summary['seasonal_precip_mm'] = _per_season(precip, flux, crop_obj, summary)
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
    tr = _sum_during_season(water_flux, 'Tr', crop_obj, summary)
    es = _sum_during_season(water_flux, 'Es', crop_obj, summary)
    summary['seasonal_et_mm'] = tr + es
    summary['seasonal_transpiration_mm'] = tr  # Tr alone is often more interesting
    return summary


@enricher
def add_total_water_input(summary, context):
    """Total water reaching the crop during season: precipitation + irrigation (mm).

    Row by row: the summary holds one row per season.
    """
    precip = _column(summary, 'seasonal_precip_mm')
    irr = _column(summary, 'Seasonal irrigation (mm)', 'IrrCum', default=0.0)
    summary['total_water_input_mm'] = precip + irr.fillna(0.0)
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
    """Yield per unit seasonal ET (kg/m3), per season. 1 t/ha per 100 mm = 1 kg/m3."""
    summary['wp_et_kg_per_m3'] = _per_unit_water(summary, _column(summary, 'seasonal_et_mm'))
    return summary


@enricher
def add_rainfall_use_efficiency(summary, context):
    """Yield per unit seasonal precipitation (kg/m3), per season."""
    summary['rainfall_use_efficiency_kg_per_m3'] = _per_unit_water(
        summary, _column(summary, 'seasonal_precip_mm'))
    return summary


@enricher
def add_irrigation_wp(summary, context):
    """Irrigation water productivity (kg/m3), per season; irrigated runs only."""
    if context['config']['irrigation'].lower() != 'irrigated':
        return summary
    summary['wp_irrigation_kg_per_m3'] = _per_unit_water(
        summary, _column(summary, 'Seasonal irrigation (mm)'))
    return summary
