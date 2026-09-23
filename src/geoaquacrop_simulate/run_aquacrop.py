"""
Driver script for AquaCrop gridded simulations.
Main entry point for running the model.
"""

import logging
import datetime as dt
from pathlib import Path
from multiprocessing import freeze_support
from .config import SimulationConfig, InputRequirements
from aquacrop import InitialWaterContent
from .processor import ParallelProcessor


def setup_logging(output_dir: Path) -> logging.Logger:
    """Set up logging configuration."""
    log_dir = output_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"aquacrop_simulation_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            # logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('aquacrop_gridded')


def print_input_requirements():
    """Print detailed input file requirements."""
    print("\n" + "="*80)
    print("AQUACROP GRIDDED SIMULATION - INPUT FILE REQUIREMENTS")
    print("="*80)
    
    print("\n1. WEATHER DATA (NetCDF files in weather_path/):")
    print("-" * 40)
    for var, info in InputRequirements.WEATHER_VARS.items():
        print(f"  • {var}.nc")
        print(f"    - Variable name: '{var}'")
        print(f"    - Units: {info['units']}")
        print(f"    - Description: {info['description']}")
    print("  • Required dimensions: time, y, x")
    print("  • Coordinate system: WGS84 (EPSG:4326)")
    
    print("\n2. SOIL DATA (NetCDF files in soil_path/):")
    print("-" * 40)
    for filename, description in InputRequirements.SOIL_FILES.items():
        print(f"  • {filename}")
        print(f"    - Description: {description}")
    print("  • Units: Percentage (0-100)")
    print("  • Names of variables in each NetCDF must be: Clay, Sand, Silt and Som ")
    print("  • Note: Organic matter should be pre-converted from SOC")
    print("  • Must have same grid, CRS, and spatial extent as weather data")
    
    print("\n3. PHENOLOGY DATA (GeoTIFF files in pheno_path/):")
    print("-" * 40)
    print("  • Naming convention: {crop}_{irrigation}_{type}.tif")
    print("  • Where:")
    print(f"    - crop: {', '.join(InputRequirements.CROPS)}")
    print("    - irrigation: 'ir' (irrigated) or 'rf' (rainfed)")
    print("    - type: 'planting_day' or 'growing_season_length'")
    print("  • Example: maize_ir_planting_day.tif")
    print("  • Units:")
    print("    - planting_day: Julian day (1-365/366)")
    print("    - growing_season_length: days")
    print("  • Must have same grid, CRS, and spatial extent as weather data")
    
    print("\n" + "="*80 + "\n")


#: A minimal illustrative configuration. `run()` takes these as keyword
#: arguments, so this exists to show the available settings, not to be edited.
EXAMPLE_CONFIG = {
    "data_path": "path/to/preprocess/processed",
    "start_date": "2011/01/01",
    "end_date": "2013/12/31",
    "crop": "Wheat_winter",
    "irrigation": "rainfed",
    "output_dir": "outputs",
    "correction": {
        "method": None,                          # None | 'scale' | 'calibrate'
        "reference_path": "reference/reference.geojson",
        "value_col": "Dry yield (tonne/ha)",
        "scale_mode": "global",                  # 'global' | 'local'
        "lever": "canopy",                       # 'canopy' (CCx) | 'biomass' (WP)
        "reuse_results": None,                   # None | 'latest' | path to .pkl
    },
}


# Values applied when neither `config` nor an explicit argument supplies them.
DEFAULTS = {
    "crop": "Maize",
    "irrigation": "rainfed",
    "output_dir": "outputs",
}

# The four input paths almost always point at the same geoaquacrop_preprocess
# `processed` folder, so `data_path` fills any that are not given explicitly.
INPUT_PATH_KEYS = ("weather_path", "soil_path", "pheno_path", "spam_path")


def default_initial_water_content():
    """Soil profile starting at field capacity through the top 2 m."""
    return InitialWaterContent(wc_type="Prop", method="Depth",
                               depth_layer=[0, 2], value=["FC", "FC"])


def build_config(config=None, *, data_path=None, **overrides):
    """Assemble a simulation configuration from keyword arguments.

    Layered, later winning: :data:`DEFAULTS`, then ``config`` if given, then
    ``data_path`` for any unset input path, then explicit ``overrides``.

    Parameters
    ----------
    config : dict, optional
        A complete or partial configuration to start from. Copied, never
        mutated.
    data_path : str or Path, optional
        Folder holding the preprocessed inputs. Fills whichever of
        ``weather_path``, ``soil_path``, ``pheno_path`` and ``spam_path`` are
        not set explicitly.
    **overrides
        Any configuration key, e.g. ``start_date``, ``crop``, ``irrigation``,
        ``output_dir``, ``correction``.

    Returns
    -------
    dict
        The assembled configuration.

    Raises
    ------
    ValueError
        If required keys are still missing, naming which ones.
    """
    import copy

    assembled = dict(DEFAULTS)
    if config:
        assembled.update(copy.deepcopy(config))

    # explicit arguments win over anything inherited
    assembled.update({k: v for k, v in overrides.items() if v is not None})

    if data_path is not None:
        for key in INPUT_PATH_KEYS:
            assembled.setdefault(key, data_path)
            if assembled.get(key) is None:
                assembled[key] = data_path

    assembled.setdefault("initial_water_content",
                         default_initial_water_content())

    required = set(INPUT_PATH_KEYS) | {"start_date", "end_date", "crop",
                                       "irrigation", "initial_water_content",
                                       "output_dir"}
    missing = sorted(k for k in required if assembled.get(k) is None)
    if missing:
        raise ValueError(
            "Missing simulation settings: " + ", ".join(missing) + ".\n"
            "Pass them as keyword arguments, e.g.\n"
            "    run(data_path='/path/to/processed', start_date='2011/01/01',\n"
            "        end_date='2013/12/31', crop='Wheat_winter')\n"
            "`data_path` fills all four input paths at once. Call "
            "example_config() to see every available setting.")
    return assembled


def run(config=None, *, data_path=None, weather_path=None, soil_path=None,
        pheno_path=None, spam_path=None, start_date=None, end_date=None,
        crop=None, irrigation=None, initial_water_content=None,
        output_dir=None, correction=None, crop_param_override=None,
        **extra):
    """Run a gridded AquaCrop simulation.

    Settings are given as keyword arguments; there is no need to build a
    configuration dictionary first::

        run(data_path='/data/region/processed',
            start_date='2011/01/01', end_date='2013/12/31',
            crop='Wheat_winter', irrigation='rainfed')

    Parameters
    ----------
    config : dict, optional
        A configuration dictionary to start from, for programmatic use. Any
        keyword argument below overrides the matching entry. The dictionary is
        copied, never modified.
    data_path : str or Path, optional
        Folder holding the preprocessed inputs, normally the
        ``processed`` directory written by geoaquacrop_preprocess. Fills
        whichever of the four input paths are not given individually.
    weather_path, soil_path, pheno_path, spam_path : str or Path, optional
        Individual input folders, for the rare case they differ.
    start_date, end_date : str
        Simulation period, ``'YYYY/MM/DD'``.
    crop : str
        Crop name, case-sensitive. Defaults to ``'Maize'``.
    irrigation : str
        ``'rainfed'`` or ``'irrigated'``. Defaults to ``'rainfed'``.
    initial_water_content : InitialWaterContent, optional
        Defaults to field capacity through the top 2 m.
    output_dir : str or Path, optional
        Where results and logs are written. Defaults to ``'outputs'``.
    correction : dict, optional
        Yield correction settings; see the documentation. Omit to disable.
    crop_param_override : dict, optional
        Crop parameters applied to every cell, e.g. ``{'CCx': 0.70}``.
    **extra
        Any further configuration key, passed through unchanged.

    Returns
    -------
    tuple
        ``(summary_file, daily_file)`` paths to the saved results, or
        ``(None, None)`` when the call only corrected an existing saved run
        (``correction.reuse_results``).

    Raises
    ------
    ValueError
        If required settings are missing, naming which ones.
    """
    config_dict = build_config(
        config, data_path=data_path, weather_path=weather_path,
        soil_path=soil_path, pheno_path=pheno_path, spam_path=spam_path,
        start_date=start_date, end_date=end_date, crop=crop,
        irrigation=irrigation, initial_water_content=initial_water_content,
        output_dir=output_dir, correction=correction,
        crop_param_override=crop_param_override, **extra)

    # --- 1. Load config from config.py ---
    sim_config = SimulationConfig(config_dict)
    
    # --- 2. Set up logging ---
    logger = setup_logging(sim_config.config['output_dir'])
    logger.info("AquaCrop gridded simulation started")
    
    # --- Optional: correct an already-saved run, skipping simulation ---
    from .correction import should_reuse, correct_saved_run
    if should_reuse(sim_config.config):
        correct_saved_run(sim_config.config, logger)
        logger.info("Correction applied to saved results; no simulation run.")
        return None, None
    
    validated_inputs = sim_config.validate_all_inputs()
    coords_df = validated_inputs['coords']

    # --- 3a. Optional calibration search (subsample) BEFORE the full run ---
    from .correction import calibration_override
    sim_config.config.update(
        calibration_override(sim_config.config, ParallelProcessor,
                             validated_inputs, coords_df, logger)
    )

    # --- 3b. Run simulations in parallel (uses the calibrated parameter) ---
    processor = ParallelProcessor(sim_config.config, validated_inputs, logger)
    summary_results, daily_results = processor.run_parallel(coords_df)

    # --- 4. Save results ---
    summary_file, daily_file = processor.save_results(
        summary_results, daily_results, sim_config.config['output_dir']
    )
    
    # --- 5. Optional config-driven yield correction ---
    processor.apply_correction(summary_results, coords_df)

    logger.info("Simulation finished successfully")
    logger.info(f"Summary saved to: {summary_file}")
    logger.info(f"Daily outputs saved to: {daily_file}")
    return summary_file, daily_file




def main():
    """Console-script entry point: runs :data:`EXAMPLE_CONFIG`.

    Edit ``EXAMPLE_CONFIG`` at the top of this module, or -- better -- call
    :func:`run` with keyword arguments from your own script.
    """
    return run(EXAMPLE_CONFIG)


if __name__ == "__main__":
    freeze_support()
    main()
