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
    
    print("\n2. SOIL DATA (GeoTIFF files in soil_path/):")
    print("-" * 40)
    for filename, description in InputRequirements.SOIL_FILES.items():
        print(f"  • {filename}")
        print(f"    - Description: {description}")
    print("  • Units: Percentage (0-100)")
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


def main():
    """
    Main function to run AquaCrop gridded simulations.
    """

    # --- USER EDITS THESE VALUES ---
    # Available crops (must match exact case-sensitive spelling):
    #   Barley, Cassava, Cotton, DryBean, Maize, Potato, Sorghum, Soybean,
    #   SugarBeet, SugarCane, Sunflower
    #   PaddyRice1, PaddyRice2           (first / second rice season)
    #   Wheat_summer, Wheat_winter       (spring-sown / autumn-sown wheat)
    config_dict = {
        'weather_path': '../01_geoaquacrop-preproc-dev/processed',
        'soil_path': '../01_geoaquacrop-preproc-dev/processed',
        'pheno_path': '../01_geoaquacrop-preproc-dev/processed',
        'spam_path': '../01_geoaquacrop-preproc-dev/processed',
        'start_date': '2011/01/01',
        'end_date': '2013/12/31',
        'crop': 'Wheat_winter',
        'irrigation': 'rainfed',
        'initial_water_content': InitialWaterContent(
            wc_type='Prop',
            method='Depth',
            depth_layer=[0, 2],
            value=['FC', 'FC']),   # %
        'output_dir': 'outputs',
        'correction': {
            'method': 'calibrate',            # None (off) | 'scale' | 'calibrate'
            'reference_path': 'reference/castillayleon/reference_castillayleon.geojson',    # e.g. 'reference/spam_yield.nc' (or a DataArray)
            'reference_var': "yield_rainfed_t_ha",     # variable name if the file is a Dataset
            'value_col': 'Dry yield (tonne/ha)',
            'scale_mode': 'global',    # scale:     'global' | 'local'
            'lever': 'canopy',         # calibrate: 'canopy' (CCx) | 'biomass' (WP)
            'bounds': None,            # optional (lo, hi) search bounds
            'search_sample': 100,      # cells subsampled for the calibration search
            'reuse_results': None,    # <-- None (normal run) | 'latest' | path to a .pkl
            'output_name': 'yield_calibrated_global.nc',
        },
    }
    
    

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


if __name__ == "__main__":
    freeze_support()
    main()
