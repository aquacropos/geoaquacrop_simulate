"""
Configuration file for AquaCrop gridded simulations.
Defines input requirements and validation functions.
"""

import os
import xarray as xr
import rasterio
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class InputRequirements:
    """Define standardized input file requirements."""
    
    # Required weather variables in NetCDF files
    WEATHER_VARS = {
        'tasmin': {'units': '°C', 'description': 'Minimum daily temperature'},
        'tasmax': {'units': '°C', 'description': 'Maximum daily temperature'},
        'pr': {'units': 'mm/day', 'description': 'Daily precipitation'},
        'referenceET': {'units': 'mm/day', 'description': 'Reference evapotranspiration'}
    }
    
    # Required dimensions for weather NetCDF
    WEATHER_DIMS = ['time', 'lat', 'lon']
    
    # Required soil raster files (% values)
    SOIL_FILES = {
        'sand_0_30cm.tif': 'Sand content 0-30cm (%)',
        'sand_30_200cm.tif': 'Sand content 30-200cm (%)',
        'clay_0_30cm.tif': 'Clay content 0-30cm (%)',
        'clay_30_200cm.tif': 'Clay content 30-200cm (%)',
        'orgmat_0_30cm.tif': 'Organic matter 0-30cm (%)',
        'orgmat_30_200cm.tif': 'Organic matter 30-200cm (%)'
    }
    
    # Required phenology raster files per crop
    PHENO_PATTERNS = {
        'planting_day': '_planting_day.tif',
        'growing_season_length': '_growing_season_length.tif'
    }
    
    # Supported crops
    CROPS = ['maize', 'wheat', 'soybean', 'rice']
    
    # Irrigation types
    IRRIGATION_TYPES = ['irrigated', 'rainfed']


class InputValidator:
    """Validate input files meet requirements."""

    @staticmethod
    def validate_weather_data(weather_path: Path) -> Dict[str, str]:
        """
        Validate weather NetCDF files.
        Returns dict of variable: filepath or raises ValueError.
        """
        validated_files = {}
        errors = []
        
        for var, info in InputRequirements.WEATHER_VARS.items():
            filepath = weather_path / f"{var}.nc"
            
            if not filepath.exists():
                errors.append(f"Missing weather file: {filepath}")
                continue
            
            try:
                with xr.open_dataset(filepath) as ds:
                    # Check dimensions
                    missing_dims = set(InputRequirements.WEATHER_DIMS) - set(ds.dims)
                    if missing_dims:
                        errors.append(f"{var}.nc missing dimensions: {missing_dims}")
                    
                    # Check variable exists
                    if var not in ds.variables:
                        errors.append(f"{var}.nc must contain variable '{var}'")
                    
                    validated_files[var] = str(filepath)
                    
            except Exception as e:
                errors.append(f"Error reading {var}.nc: {str(e)}")
        
        if errors:
            raise ValueError("Weather data validation failed:\n" + "\n".join(errors))
        
        return validated_files

    @staticmethod
    def _check_spatial_alignment(ref_coords: pd.DataFrame, raster_file: Path, label: str):
        """Ensure raster grid aligns with reference coords_df from precipitation file."""
        with rasterio.open(raster_file) as src:
            
            # Extract 1D arrays of lat/lon
            lats = [src.xy(row, 0)[1] for row in range(src.height)]
            lons = [src.xy(0, col)[0] for col in range(src.width)]

            raster_coords = {(round(lat, 6), round(lon, 6)) for lat in lats for lon in lons}
            ref_set = {(round(lat, 6), round(lon, 6)) for lat, lon in zip(ref_coords['lat'], ref_coords['lon'])}

            if not raster_coords.issubset(ref_set):
                raise ValueError(f"{label} grid does not align with precipitation grid")
    
    @staticmethod
    def validate_soil_data(soil_path: Path, ref_coords: pd.DataFrame) -> Dict[str, str]:
        """
        Validate soil raster files.
        Returns dict of soil_type: filepath or raises ValueError.
        """
        validated_files = {}
        errors = []
        
        for filename, description in InputRequirements.SOIL_FILES.items():
            filepath = soil_path / filename
            
            if not filepath.exists():
                errors.append(f"Missing soil file: {filepath} ({description})")
                continue
            
            try:
                with rasterio.open(filepath) as src:
                    # Check if raster has data
                    if src.count < 1:
                        errors.append(f"{filename} has no bands")
                    
                    # Check CRS exists
                    if src.crs is None:
                        errors.append(f"{filename} missing CRS")
                    
                    # Check spatial grid aligns with climate data
                    InputValidator._check_spatial_alignment(ref_coords, filepath, f"Soil ({filename})")

                    # Store as a validated file
                    validated_files[filename.replace('.tif', '')] = str(filepath)
                    
            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")
        
        if errors:
            raise ValueError("Soil data validation failed:\n" + "\n".join(errors))
        
        return validated_files
    
    @staticmethod
    def validate_phenology_data(pheno_path: Path, crop: str, irrigation: str, ref_coords: pd.DataFrame) -> Dict[str, str]:
        """
        Validate phenology raster files for specific crop and irrigation type.
        Returns dict of pheno_type: filepath or raises ValueError.
        """
        validated_files = {}
        errors = []
        
        crop_lower = crop.lower()
        irr_suffix = 'ir' if irrigation.lower() == 'irrigated' else 'rf'
        
        if crop_lower not in InputRequirements.CROPS:
            raise ValueError(f"Unsupported crop: {crop}. Supported: {InputRequirements.CROPS}")
        
        for pheno_type, pattern in InputRequirements.PHENO_PATTERNS.items():
            # Expected filename format: {crop}_{irrigation}_{pheno_type}.tif
            filename = f"{crop_lower}_{irr_suffix}{pattern}"
            filepath = pheno_path / filename
            
            if not filepath.exists():
                errors.append(f"Missing phenology file: {filepath}")
                continue
            
            try:
                with rasterio.open(filepath) as src:
                    if src.count < 1:
                        errors.append(f"{filename} has no bands")

                    # Check spatial alignment against climate data
                    InputValidator._check_spatial_alignment(ref_coords, filepath, f"Phenology ({filename})")
                    
                    # Store validated file
                    validated_files[pheno_type] = str(filepath)
                    
            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")
        
        if errors:
            raise ValueError(f"Phenology data validation failed for {crop} ({irrigation}):\n" + "\n".join(errors))
        
        return validated_files


class SimulationConfig:
    """Store and validate simulation configuration."""
    
    def __init__(self, config_dict: Dict):
        """Initialize and validate configuration."""
        self.config = config_dict
        self._validate_config()
        
    def _validate_config(self):
        """Validate all configuration parameters."""
        required_keys = [
            'coord_file', 'weather_path', 'soil_path', 'pheno_path',
            'start_date', 'end_date', 'crop', 'irrigation',
            'initial_water_content', 'output_dir'
        ]
        
        missing_keys = set(required_keys) - set(self.config.keys())
        if missing_keys:
            raise ValueError(f"Missing configuration keys: {missing_keys}")
        
        # Convert paths to Path objects
        for key in ['coord_file', 'weather_path', 'soil_path', 'pheno_path', 'output_dir']:
            self.config[key] = Path(self.config[key])
        
        # Validate dates
        try:
            pd.to_datetime(self.config['start_date'])
            pd.to_datetime(self.config['end_date'])
        except:
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD'")
        
        # Validate crop
        if self.config['crop'].lower() not in InputRequirements.CROPS:
            raise ValueError(f"Invalid crop: {self.config['crop']}")
        
        # Validate irrigation
        if self.config['irrigation'].lower() not in InputRequirements.IRRIGATION_TYPES:
            raise ValueError(f"Invalid irrigation type: {self.config['irrigation']}")
        
        # Create output directory if it doesn't exist
        self.config['output_dir'].mkdir(parents=True, exist_ok=True)

    def _get_coordinates_from_weather(self, pr_file: Path) -> pd.DataFrame:
        with xr.open_dataset(pr_file) as ds:
            lats = ds['lat'].values
            lons = ds['lon'].values
            coords = [(lat, lon) for lat in lats for lon in lons]
        return pd.DataFrame(coords, columns=['lat', 'lon'])
    
    def validate_all_inputs(self) -> Dict:
        """Validate all input files and return paths."""
        print("Validating input files...")
        
        # Validate coordinates
        # print("  Checking coordinates...")
        # coords_df = InputValidator.validate_coordinates(self.config['coord_file'])
        
        # Validate weather data
        print("  Checking weather data...")
        weather_files = InputValidator.validate_weather_data(self.config['weather_path'])

        # Build coords from pr.nc
        print("  Extracting coordinates from precipitation grid...")
        coords_df = self._get_coordinates_from_weather(Path(weather_files['pr']))
        
        # Validate soil data
        print("  Checking soil data...")
        soil_files = InputValidator.validate_soil_data(self.config['soil_path'], coords_df)
        
        # Validate phenology data
        print("  Checking phenology data...")
        pheno_files = InputValidator.validate_phenology_data(
            self.config['pheno_path'], 
            self.config['crop'], 
            self.config['irrigation'],
            coords_df
        )
        
        print("All input files validated successfully!")
        
        return {
            'coords': coords_df,
            'weather': weather_files,
            'soil': soil_files,
            'phenology': pheno_files
        }