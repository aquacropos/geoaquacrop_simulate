"""
Main processing module for AquaCrop gridded simulations.
Handles data loading, model execution, and parallelization.
"""

import pandas as pd
import xarray as xr
import numpy as np
#import rasterio
import datetime as dt
import logging
import pickle
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from aquacrop import AquaCropModel, Soil, Crop, IrrigationManagement


class DataLoader:
    """Handle loading of standardized input data."""
    
    @staticmethod
    def load_weather_for_point(weather_files: Dict[str, str], y: float, x: float, 
                              start_date: str, end_date: str) -> pd.DataFrame:
        """Load weather data for a specific point."""
        weather_data = {}
        
        for var, filepath in weather_files.items():
            with xr.open_dataset(filepath) as ds:
                # Select nearest point (dims: time, latitude, longitude)
                point_data = ds.sel(y=y, x=x, method="nearest")
                
                # Filter time range
                point_data = point_data.sel(time=slice(start_date, end_date))
                
                # Convert to dataframe
                df = point_data[var].to_dataframe().reset_index()

                # Index by time only
                weather_data[var] = df[["time", var]].set_index("time")
        
        # Combine all weather variables on common dates and drop any NaNs
        weather_df = pd.concat(weather_data.values(), axis=1, join="inner").dropna(how="any")
        weather_df.reset_index(inplace=True)

        # Rename time column only
        weather_df = weather_df.rename(columns={"time": "Date"})

        
        # Ensure correct column order
        weather_df = weather_df[["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]]
        
        return weather_df
    
    @staticmethod
    def load_soil_for_point(soil_files: Dict[str, str], x: float, y: float) -> Optional[Soil]:
        """Load soil data for a specific point and create Soil object."""
        
        def _extract_soil_vars(path: str, x: float, y: float):
            ds = xr.open_dataset(path)
            pt = ds.sel(x=x, y=y, method="nearest").isel(band=0)
            sand = float(pt["Sand"].values)
            clay = float(pt["Clay"].values)
            orgmat = float(pt["Som"].values)
            ds.close()
            return sand, clay, orgmat
    
        # Extract all layers, checking for NaN at each depth
        all_layers = []
        for key in ["0_5cm", "5_15cm", "15_30cm", "30_60cm", "60_100cm", "100_200cm"]:
            sand, clay, orgmat = _extract_soil_vars(soil_files[key], x, y)
            if any(np.isnan(v) for v in [sand, clay, orgmat]):
                return None
            all_layers.append((sand, clay, orgmat))
    
        # Build soil object — layer thicknesses in metres
        thicknesses = [0.05, 0.1, 0.15, 0.30, 0.40, 1.0]
        custom_soil = Soil('custom', cn=46, rew=7)
        for (sand, clay, orgmat), thickness in zip(all_layers, thicknesses):
            custom_soil.add_layer_from_texture(
                thickness=thickness,
                Sand=sand,
                Clay=clay,
                OrgMat=orgmat,
                penetrability=100
            )
        
        return custom_soil
    
    @staticmethod
    def load_phenology_for_point(
        pheno_files: Dict[str, str],
        x: float,
        y: float,
        crop: str,
        irrigation: str
    ) -> Dict[str, float]:
        """Load phenology data for a specific point from cropcalendar.nc."""
        # All entries in pheno_files point to the same NetCDF
        pheno_path = next(iter(pheno_files.values()))
        
        # Map irrigation type to suffix used in variable names
        irr_tag = "ir" if irrigation.lower() == "irrigated" else "rf"
        crop_lower = crop.lower()
        crop_title = crop_lower.capitalize()  # maize -> Maize
        
        planting_suffix = f"_{irr_tag}_planting"
        
        with xr.open_dataset(pheno_path, decode_timedelta=False) as ds:
            # Find planting variable for this crop + irrigation
            planting_var = None
            for v in ds.data_vars:
                if v.startswith(f"{crop_title}_") and v.endswith(planting_suffix):
                    planting_var = v
                    break
            
            if planting_var is None:
                # No data → return NaNs; CropAdjuster will skip this cell
                return {"planting_day": np.nan, "growing_season_length": np.nan}
            
            # Derive growing-season-length variable name
            prefix = planting_var[: -len(planting_suffix)]
            gsl_var = f"{prefix}_{irr_tag}_growing_season_length"
            
            if gsl_var not in ds.data_vars:
                return {"planting_day": np.nan, "growing_season_length": np.nan}
            
            # Select nearest point (dims: y(lat), x(lon))
            pt_plant = ds[planting_var].sel(y=y, x=x, method="nearest")
            pt_gsl = ds[gsl_var].sel(y=y, x=x, method="nearest")
            
            planting_day = float(pt_plant.values)
            
            # growing_season_length is timedelta64 → convert to days
            gsl_raw = pt_gsl.values
            if np.issubdtype(gsl_raw.dtype, np.timedelta64):
                season_length = float(gsl_raw / np.timedelta64(1, "D"))
            else:
                season_length = float(gsl_raw)
        
        return {
            "planting_day": planting_day,
            "growing_season_length": season_length,
        }



class CropAdjuster:
    """Handle crop phenology adjustments."""
    
    @staticmethod
    def adjust_crop_phenology(crop_obj: Crop, pheno_data: Dict[str, float]) -> Crop:
        """Adjust crop phenology based on gridded data."""
        planting_val = pheno_data.get("planting_day", np.nan)
        season_length = pheno_data.get("growing_season_length", np.nan)

        # If either is missing or non-numeric, skip this cell
        try:
            if np.isnan(float(planting_val)) or np.isnan(float(season_length)):
                return None
        except (TypeError, ValueError):
            return None

        # Now safe to convert
        try:
            planting_day = int(planting_val)
        except (TypeError, ValueError):
            return None

        
        # Now safe to convert
        planting_day = int(planting_val)
        
        # Convert planting day to date string
        planting_date = (dt.datetime(2000, 1, 1) + dt.timedelta(planting_day - 1)).strftime('%m/%d')
        crop_obj.planting_date = planting_date
        
        # Calculate scaling factor
        aq_maturity = crop_obj.MaturityCD
        sf = season_length / aq_maturity
        
        # Store original values
        emergence_old = crop_obj.EmergenceCD
        maturity_old = crop_obj.MaturityCD
        senescence_old = crop_obj.SenescenceCD
        cgc_old = crop_obj.CGC_CD
        cdc_old = crop_obj.CDC_CD
        
        # Apply scaling to phenological parameters
        crop_obj.EmergenceCD = round(crop_obj.EmergenceCD * sf)
        crop_obj.FloweringCD = round(crop_obj.FloweringCD * sf)
        crop_obj.HIstartCD = round(crop_obj.HIstartCD * sf)
        crop_obj.MaturityCD = round(crop_obj.MaturityCD * sf)
        crop_obj.MaxRootingCD = round(crop_obj.MaxRootingCD * sf)
        crop_obj.SenescenceCD = round(crop_obj.SenescenceCD * sf)
        crop_obj.YldFormCD = round(crop_obj.YldFormCD * sf)
        
        # Calculate canopy parameters
        CCo = crop_obj.PlantPop * crop_obj.SeedSize * 1e-8
        
        # Calculate old MaxCanopyCD
        max_canopy_old = emergence_old + (
            np.log((0.25 * crop_obj.CCx / CCo) / (crop_obj.CCx - 0.98 * crop_obj.CCx)) / cgc_old
        )
        max_canopy_new = max_canopy_old * sf
        
        # Calculate new CGC
        cgc_new = (
            np.log((0.25 * crop_obj.CCx / CCo) / (crop_obj.CCx - 0.98 * crop_obj.CCx)) / 
            (max_canopy_new - crop_obj.EmergenceCD)
        )
        
        # Calculate new CDC
        CCf = crop_obj.CCx * (
            1 - 0.05 * (np.exp((3.33 * cdc_old / (crop_obj.CCx + 2.29)) * 
                              (maturity_old - senescence_old)) - 1)
        )
        CCf = max(0, CCf)
        
        cdc_new = (
            (crop_obj.CCx + 2.29) * np.log((CCf / crop_obj.CCx - 1) / -0.05 + 1) / 
            (3.33 * (crop_obj.MaturityCD - crop_obj.SenescenceCD))
        )
        
        # Update crop parameters
        crop_obj.CGC_CD = cgc_new
        crop_obj.CDC_CD = cdc_new
        
        return crop_obj


def worker_run(
    i: int,
    coords_row: pd.Series,
    validated_inputs: Dict,
    config: Dict,
    logger: logging.Logger
) -> Dict:
    """
    Worker function to run AquaCrop for a single grid cell.
    """
    try:
        y = coords_row['y']
        x = coords_row['x']
        
        logger.info(f"Processing cell {i}: y={y}, x={x}")
        
        # Load soil data
        soil = DataLoader.load_soil_for_point(validated_inputs['soil'], x, y)
        if soil is None:
            logger.warning(f"Cell {i}: No soil data available")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'y': y, 'x': x,
                    'error': 'Missing soil data'
                }]),
                "daily": None
            }
        
        # Load weather data
        weather_df = DataLoader.load_weather_for_point(
            validated_inputs['weather'],
            y, x,
            config['start_date'],
            config['end_date']
        )
        
        if weather_df.empty:
            logger.warning(f"Cell {i}: Invalid weather data")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'y': y, 'x': x,
                    'error': 'Invalid weather data'
                }]),
                "daily": None
            }

        
        # Load phenology data
        pheno_data = DataLoader.load_phenology_for_point(
            validated_inputs['phenology'],
            x,
            y,
            config['crop'],
            config['irrigation']
        )
        
        # Initialize crop
        crop_mapping = {
            'maize': 'Maize',
            'wheat': 'Wheat',
            'soybean': 'Soybean',
            'rice': 'PaddyRice'
        }
        crop_name = crop_mapping[config['crop'].lower()]
        crop_obj = Crop(crop_name, planting_date='01/01')  # Default date
        crop_obj.CalendarType = (1)  # Force calendar-day mode so CD parameter adjustments take effect
        
        # Adjust crop phenology
        crop_obj = CropAdjuster.adjust_crop_phenology(crop_obj, pheno_data)
        if crop_obj is None:
            logger.warning(f"Cell {i}: Invalid phenology data")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'y': y, 'x': x,
                    'error': 'Invalid phenology data'
                }]),
                "daily": None
            }
        
        
        # Set up irrigation
        irr_method = 1 if config['irrigation'].lower() == 'irrigated' else 0
        irr_mngt = IrrigationManagement(
            irrigation_method=irr_method,
            SMT=[80, 80, 80, 0] if irr_method == 1 else None
        )
        
        # Set initial water content
        initial_wc = config['initial_water_content']
        
        # Run model
        model = AquaCropModel(
            sim_start_time=config['start_date'],
            sim_end_time=config['end_date'],
            weather_df=weather_df,
            soil=soil,
            crop=crop_obj,
            irrigation_management=irr_mngt,
            initial_water_content=initial_wc
        )
        
        model.run_model(till_termination=True)
        
        # Extract results
        final_stats = model._outputs.final_stats
        final_stats['cell_id'] = i
        final_stats['y'] = y
        final_stats['x'] = x
        final_stats['crop'] = config['crop']
        final_stats['irrigation'] = config['irrigation']
        final_stats['planting_date'] = crop_obj.planting_date
        
        # Get daily outputs
        water_flux = model._outputs.water_flux
        crop_growth = model._outputs.crop_growth
        
        logger.info(f"Cell {i}: Simulation completed successfully")
        
        return {
            "summary": final_stats,
            "daily": {
                'water_flux': water_flux,
                'crop_growth': crop_growth
            }
        }
        
    except Exception as e:
        logger.error(f"Cell {i}: Error - {str(e)}")
        return {
            "summary": pd.DataFrame([{
                'cell_id': i,
                'y': coords_row.get('y', np.nan),
                'x': coords_row.get('x', np.nan),
                'error': str(e)
            }]),
            "daily": None
        }


class ParallelProcessor:
    """Handle parallel processing of grid cells."""
    
    def __init__(self, config: Dict, validated_inputs: Dict, logger: logging.Logger):
        self.config = config
        self.validated_inputs = validated_inputs
        self.logger = logger
    
    def run_parallel(self, coords_df: pd.DataFrame, max_workers: Optional[int] = None) -> Tuple[List, List]:
        """Run simulations in parallel across grid cells."""
        import multiprocessing
        
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        self.logger.info(f"Starting parallel processing with {max_workers} workers")
        
        # Create partial function with fixed parameters
        partial_worker = partial(
            worker_run,
            validated_inputs=self.validated_inputs,
            config=self.config,
            logger=self.logger
        )
        
        summary_results = []
        daily_results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit jobs
            futures = []
            for i, row in coords_df.iterrows():
                future = executor.submit(partial_worker, i, row)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                summary_results.append(result['summary'])
                daily_results.append(result['daily'])
        
        self.logger.info("Parallel processing completed")
        
        return summary_results, daily_results
    
    def save_results(self, summary_results: List, daily_results: List, output_dir: Path):
        """Save results to pickle files."""
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary results
        summary_file = output_dir / f"summary_results_{timestamp}.pkl"
        with open(summary_file, 'wb') as f:
            pickle.dump(summary_results, f, pickle.HIGHEST_PROTOCOL)
        self.logger.info(f"Summary results saved to {summary_file}")
        
        # Save daily results
        daily_file = output_dir / f"daily_results_{timestamp}.pkl"
        with open(daily_file, 'wb') as f:
            pickle.dump(daily_results, f, pickle.HIGHEST_PROTOCOL)
        self.logger.info(f"Daily results saved to {daily_file}")
        
        return summary_file, daily_file