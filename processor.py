"""
Main processing module for AquaCrop gridded simulations.
Handles data loading, model execution, and parallelization.
"""

import pandas as pd
import xarray as xr
import numpy as np
import rasterio
import datetime as dt
import logging
import pickle
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement


class DataLoader:
    """Handle loading of standardized input data."""
    
    @staticmethod
    def load_weather_for_point(weather_files: Dict[str, str], lat: float, lon: float, 
                              start_date: str, end_date: str) -> pd.DataFrame:
        """Load weather data for a specific point."""
        weather_data = {}
        
        for var, filepath in weather_files.items():
            with xr.open_dataset(filepath) as ds:
                # Select nearest point
                point_data = ds.sel(lat=lat, lon=lon, method='nearest')
                
                # Filter time range
                point_data = point_data.sel(time=slice(start_date, end_date))
                
                # Convert to dataframe
                df = point_data[var].to_dataframe().reset_index()
                weather_data[var] = df[['time', var]].set_index('time')
        
        # Combine all weather variables
        weather_df = pd.concat(weather_data.values(), axis=1)
        weather_df.reset_index(inplace=True)
        
        # Rename columns to match AquaCrop requirements
        weather_df = weather_df.rename(columns={
            'time': 'Date',
            'tasmin': 'MinTemp',
            'tasmax': 'MaxTemp',
            'pr': 'Precipitation',
            'referenceET': 'ReferenceET'
        })
        
        # Ensure correct column order
        weather_df = weather_df[['MinTemp', 'MaxTemp', 'Precipitation', 'ReferenceET', 'Date']]
        
        return weather_df
    
    @staticmethod
    def extract_raster_value(raster_file: str, lon: float, lat: float) -> float:
        """Extract value from raster at given coordinates."""
        with rasterio.open(raster_file) as src:
            # Check if point is within bounds
            bounds = src.bounds
            if not (bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top):
                return np.nan
            
            # Sample the raster at coordinates
            value = list(src.sample([(lon, lat)]))[0][0]
            return value
    
    @staticmethod
    def load_soil_for_point(soil_files: Dict[str, str], lon: float, lat: float) -> Optional[Soil]:
        """Load soil data for a specific point and create Soil object."""
        soil_data = {}
        
        # Extract values from each soil raster
        for soil_type, filepath in soil_files.items():
            value = DataLoader.extract_raster_value(filepath, lon, lat)
            soil_data[soil_type] = value
        
        # Check for missing data
        if any(np.isnan(v) for v in soil_data.values()):
            return None
        
        # Create custom soil with two layers
        custom_soil = Soil('custom', cn=46, rew=7)
        
        # Add top layer (0-30cm)
        custom_soil.add_layer_from_texture(
            thickness=0.3,
            Sand=soil_data['sand_0_30cm'],
            Clay=soil_data['clay_0_30cm'],
            OrgMat=soil_data['orgmat_0_30cm'],
            penetrability=100
        )
        
        # Add bottom layer (30-200cm)
        custom_soil.add_layer_from_texture(
            thickness=1.7,
            Sand=soil_data['sand_30_200cm'],
            Clay=soil_data['clay_30_200cm'],
            OrgMat=soil_data['orgmat_30_200cm'],
            penetrability=100
        )
        
        return custom_soil
    
    @staticmethod
    def load_phenology_for_point(pheno_files: Dict[str, str], lon: float, lat: float) -> Dict[str, float]:
        """Load phenology data for a specific point."""
        pheno_data = {}
        
        for pheno_type, filepath in pheno_files.items():
            value = DataLoader.extract_raster_value(filepath, lon, lat)
            pheno_data[pheno_type] = value
        
        return pheno_data


class CropAdjuster:
    """Handle crop phenology adjustments."""
    
    @staticmethod
    def adjust_crop_phenology(crop_obj: Crop, pheno_data: Dict[str, float]) -> Crop:
        """Adjust crop phenology based on gridded data."""
        if any(np.isnan(v) for v in pheno_data.values()):
            return None
        
        # Extract phenology parameters
        planting_day = int(pheno_data['planting_day'])
        season_length = pheno_data['growing_season_length']
        
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
        lat = coords_row['lat']
        lon = coords_row['lon']
        
        logger.info(f"Processing cell {i}: lat={lat}, lon={lon}")
        
        # Load soil data
        soil = DataLoader.load_soil_for_point(validated_inputs['soil'], lon, lat)
        if soil is None:
            logger.warning(f"Cell {i}: No soil data available")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'lat': lat, 'lon': lon,
                    'error': 'Missing soil data'
                }]),
                "daily": None
            }
        
        # Load weather data
        weather_df = DataLoader.load_weather_for_point(
            validated_inputs['weather'],
            lat, lon,
            config['start_date'],
            config['end_date']
        )
        
        if weather_df.empty or weather_df.isnull().any().any():
            logger.warning(f"Cell {i}: Invalid weather data")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'lat': lat, 'lon': lon,
                    'error': 'Invalid weather data'
                }]),
                "daily": None
            }
        
        # Load phenology data
        pheno_data = DataLoader.load_phenology_for_point(
            validated_inputs['phenology'], lon, lat
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
        
        # Adjust crop phenology
        crop_obj = CropAdjuster.adjust_crop_phenology(crop_obj, pheno_data)
        if crop_obj is None:
            logger.warning(f"Cell {i}: Invalid phenology data")
            return {
                "summary": pd.DataFrame([{
                    'cell_id': i, 'lat': lat, 'lon': lon,
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
        initial_wc = InitialWaterContent(
            wc_type='Pct',
            method='Layer',
            depth_layer=[1, 2],
            value=config['initial_water_content']
        )
        
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
        final_stats['lat'] = lat
        final_stats['lon'] = lon
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
                'lat': coords_row.get('lat', np.nan),
                'lon': coords_row.get('lon', np.nan),
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