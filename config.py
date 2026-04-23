"""
Configuration file for AquaCrop gridded simulations.
Defines input requirements and validation functions.
"""

import os
import warnings
import xarray as xr
#import rasterio
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


class InputRequirements:
    """Define standardized input file requirements."""
    
    # Required weather variables in NetCDF files
    # CHANGED: use actual variable names MinTemp, MaxTemp, Precipitation, ReferenceET
    WEATHER_VARS = {
        'MinTemp': {
            'units': '°C',
            'description': 'Minimum daily temperature'
        },
        'MaxTemp': {
            'units': '°C',
            'description': 'Maximum daily temperature'
        },
        'Precipitation': {
            'units': 'mm/day',
            'description': 'Daily precipitation'
        },
        'ReferenceET': {
            'units': 'mm/day',
            'description': 'Reference evapotranspiration'
        }
    }
    
    # Required dimensions for weather NetCDF
    WEATHER_DIMS = ['time', 'x', 'y']
    
    # Required soil NetCDF files 
    SOIL_FILES = [
        'soil_0-5.nc',
        'soil_5-15.nc',
        'soil_15-30.nc',
        'soil_30-60.nc',
        'soil_60-100.nc',
        'soil_100-200.nc'
    ]
    
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
    # CHANGED: now takes start_year, end_year
    def validate_weather_data(weather_path: Path, start_year: int, end_year: int) -> Dict[str, str]:
        """
        Validate weather NetCDF files.
        Expects filenames like {var}{start_year}{end_year}.nc,
        where var ∈ {MinTemp, MaxTemp, Precipitation, ReferenceET}.
        
        Returns dict of variable_name: filepath or raises ValueError.
        """
        validated_files = {}
        errors = []
        
        for var, info in InputRequirements.WEATHER_VARS.items():
            filename = f"{var}{start_year}{end_year}.nc"
            filepath = weather_path / filename
            
            if not filepath.exists():
                errors.append(f"Missing weather file: {filepath}")
                continue
            
            try:
                with xr.open_dataset(filepath) as ds:
                    # Check dimensions
                    missing_dims = set(InputRequirements.WEATHER_DIMS) - set(ds.dims)
                    if missing_dims:
                        errors.append(f"{filename} missing dimensions: {missing_dims}")
                    
                    # Check variable exists (assume variable name == var string)
                    if var not in ds.variables:
                        errors.append(f"{filename} must contain variable '{var}'")
                    
                    validated_files[var] = str(filepath)
                    
            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")
        
        if errors:
            raise ValueError("Weather data validation failed:\n" + "\n".join(errors))
        
        return validated_files

    # @staticmethod
    # def _check_spatial_alignment(ref_coords: pd.DataFrame, raster_file: Path, label: str):
    #     """Ensure raster grid aligns with reference coords_df from precipitation file."""
    #     with rasterio.open(raster_file) as src:
            
    #         # Extract 1D arrays of lat/lon
    #         lats = [src.xy(row, 0)[1] for row in range(src.height)]
    #         lons = [src.xy(0, col)[0] for col in range(src.width)]

    #         raster_coords = {(round(lat, 6), round(lon, 6)) for lat in lats for lon in lons}
    #         ref_set = {(round(lat, 6), round(lon, 6)) for lat, lon in zip(ref_coords['lat'], ref_coords['lon'])}

    #         if not raster_coords.issubset(ref_set):
    #             raise ValueError(f"{label} grid does not align with precipitation grid")
    
    @staticmethod
    def validate_soil_data(soil_path: Path, ref_coords: pd.DataFrame) -> Dict[str, str]:
        """
        Validate soil NetCDF files (soil_0-5.nc, soil_5-15.nc, ...).
        Returns dict mapping depth keys used by the model (e.g. '0_5cm')
        to file paths.
        """
        validated_files = {}
        errors = []
    
        # Map filenames -> keys used in DataLoader.load_soil_for_point
        depth_key_map = {
            'soil_0-5.nc': '0_5cm',
            'soil_5-15.nc': '5_15cm',
            'soil_15-30.nc': '15_30cm',
            'soil_30-60.nc': '30_60cm',
            'soil_60-100.nc': '60_100cm',
            'soil_100-200.nc': '100_200cm',
        }
    
        # Build 1D reference coord sets once for alignment checks.
        # ref_coords only contains cells inside the domain mask, so we compare
        # the unique y and x values (grid alignment) rather than every cell pair.
        ref_y = set(np.round(np.unique(ref_coords['y'].values), 6))
        ref_x = set(np.round(np.unique(ref_coords['x'].values), 6))
    
        for filename in InputRequirements.SOIL_FILES:
            filepath = soil_path / filename
    
            if not filepath.exists():
                errors.append(f"Missing soil file: {filepath}")
                continue
    
            try:
                with xr.open_dataset(filepath) as ds:
                    # Check required dimensions
                    missing_dims = {'y', 'x'} - set(ds.dims)
                    if missing_dims:
                        errors.append(f"{filename} missing dimensions: {missing_dims}")
    
                    # Check required variables
                    required_vars = {'Clay', 'Sand', 'Silt', 'Som'}
                    missing_vars = required_vars - set(ds.data_vars)
                    if missing_vars:
                        errors.append(f"{filename} missing variables: {missing_vars}")
    
                    # Check spatial alignment against climate grid.
                    # The soil file retains the full bounding box (NaN outside mask),
                    # so we check whether every ref coordinate is present in the soil grid.
                    soil_y = set(np.round(ds['y'].values, 6))
                    soil_x = set(np.round(ds['x'].values, 6))
    
                    if not (ref_y.issubset(soil_y) and ref_x.issubset(soil_x)):
                        warnings.warn(
                            f"Soil ({filename}) grid not exactly aligned with precipitation grid. "
                            f"Nearest-neighbour selection will be used at runtime."
                        )
    
                    # Store validated file under the depth key expected by DataLoader
                    key = depth_key_map.get(filename, filename.replace('.nc', ''))
                    validated_files[key] = str(filepath)
    
            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")
    
        if errors:
            raise ValueError("Soil data validation failed:\n" + "\n".join(errors))
    
        return validated_files

    
    @staticmethod
    def validate_phenology_data(
        pheno_path: Path,
        crop: str,
        irrigation: str,
        ref_coords: pd.DataFrame
    ) -> Dict[str, str]:
        """
        Validate phenology NetCDF for a specific crop and irrigation type.
        Uses a single 'cropcalendar.nc' file which contains variables like:
        e.g. Maize_rf_planting, Maize_rf_growing_season_length, etc.
        
        Returns dict of pheno_type -> filepath or raises ValueError.
        """
        validated_files = {}
        errors = []

        crop_lower = crop.lower()
        if crop_lower not in InputRequirements.CROPS:
            raise ValueError(
                f"Unsupported crop: {crop}. Supported: {InputRequirements.CROPS}"
            )

        # Map irrigation type to suffix used in variable names
        irr_tag = "ir" if irrigation.lower() == "irrigated" else "rf"

        # We now always use a single NetCDF
        filename = "cropcalendar.nc"
        filepath = pheno_path / filename

        if not filepath.exists():
            errors.append(f"Missing phenology file: {filepath}")
        else:
            try:
                with xr.open_dataset(filepath) as ds:
                    # ---- 1) Spatial alignment check (x/y vs lat/lon) ----
                    # x = lon, y = lat in your example file
                    if "x" not in ds.coords or "y" not in ds.coords:
                        errors.append(f"{filename} missing x/y coordinates")
                    else:
                        # Compare 1D coordinate axes rather than every cell pair.
                        # ref_coords only contains cells inside the domain mask, while the
                        # phenology file retains the full bounding box (NaN outside mask),
                        # so we check whether every ref coordinate is present in the pheno grid.
                        ref_y = set(np.round(np.unique(ref_coords["y"].values), 6))
                        ref_x = set(np.round(np.unique(ref_coords["x"].values), 6))
                        pheno_y = set(np.round(ds["y"].values, 6))
                        pheno_x = set(np.round(ds["x"].values, 6))
                
                        if not (ref_y.issubset(pheno_y) and ref_x.issubset(pheno_x)):
                            warnings.warn(
                                f"Phenology ({filename}) grid not exactly aligned with precipitation grid. "
                                f"Nearest-neighbour selection will be used at runtime."
                            )
        
                    # ---- 2) Check that the appropriate variables exist ----
                    # Variables look like:
                    #   Maize_rf_planting
                    #   Maize_rf_growing_season_length
                    crop_title = crop_lower.capitalize()  # maize -> Maize, wheat -> Wheat

                    planting_suffix = f"_{irr_tag}_planting"

                    # Find the first planting variable that matches this crop + irrigation
                    planting_var = None
                    for v in ds.data_vars:
                        if v.startswith(f"{crop_title}_") and v.endswith(planting_suffix):
                            planting_var = v
                            break

                    if planting_var is None:
                        errors.append(
                            f"No planting variable found in {filename} for crop={crop}, irrigation={irrigation}"
                        )
                    else:
                        # Derive corresponding growing-season-length variable
                        prefix = planting_var[: -len(planting_suffix)]
                        gsl_var = f"{prefix}_{irr_tag}_growing_season_length"

                        if gsl_var not in ds.data_vars:
                            errors.append(
                                f"In {filename}, missing growing season variable '{gsl_var}' "
                                f"for crop={crop}, irrigation={irrigation}"
                            )
                        else:
                            # Both planting_day and growing_season_length come from the same file
                            validated_files["planting_day"] = str(filepath)
                            validated_files["growing_season_length"] = str(filepath)

            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")

        if errors:
            raise ValueError(
                f"Phenology data validation failed for {crop} ({irrigation}):\n"
                + "\n".join(errors)
            )

        return validated_files




class SimulationConfig:
    """Store and validate simulation configuration."""
    
    def __init__(self, config_dict: Dict):
        """Initialize and validate configuration."""
        self.config = config_dict
        self._validate_config()
        
    def _validate_config(self):
        """Validate all configuration parameters."""
        # coord_file is no longer required – we derive coords from the weather grid
        required_keys = [
            'weather_path', 'soil_path', 'pheno_path',
            'start_date', 'end_date', 'crop', 'irrigation',
            'initial_water_content', 'output_dir'
        ]
        
        missing_keys = set(required_keys) - set(self.config.keys())
        if missing_keys:
            raise ValueError(f"Missing configuration keys: {missing_keys}")
        
        # Convert paths to Path objects
        for key in ['weather_path', 'soil_path', 'pheno_path', 'output_dir']:
            self.config[key] = Path(self.config[key])
        
        # Validate dates
        for key in ['start_date', 'end_date']:
            parts = self.config[key].split('/')
            if len(parts) != 3:
                raise ValueError(f"Invalid date format for '{key}': '{self.config[key]}'. Use 'YYYY/MM/DD'")
            try:
                pd.to_datetime(self.config[key], format='%Y/%m/%d')
            except Exception:
                raise ValueError(f"Invalid date for '{key}': '{self.config[key]}'. Use 'YYYY/MM/DD'")
        
        # Validate crop
        if self.config['crop'].lower() not in InputRequirements.CROPS:
            raise ValueError(f"Invalid crop: {self.config['crop']}")
        
        # Validate irrigation
        if self.config['irrigation'].lower() not in InputRequirements.IRRIGATION_TYPES:
            raise ValueError(f"Invalid irrigation type: {self.config['irrigation']}")
        
        # Create output directory if it doesn't exist
        self.config['output_dir'].mkdir(parents=True, exist_ok=True)

    def _get_coordinates_from_weather(self, precip_file: Path) -> pd.DataFrame:
        with xr.open_dataset(precip_file) as ds:
            print(ds['Precipitation'])  # shows dims, shape, coords
            precip_slice = ds['Precipitation'].isel(time=0)
            print(precip_slice.dims, precip_slice.shape)
            mask = precip_slice.squeeze().notnull().values
            print("mask shape:", mask.shape)
            lats, lons = np.meshgrid(ds.y.values, ds.x.values, indexing='ij')
            print("meshgrid shape:", lats.shape)
            return pd.DataFrame({
                'y': lats[mask],
                'x': lons[mask],
            })
    
    def validate_all_inputs(self) -> Dict:
        """Validate all input files and return paths."""
        print("Validating input files...")
        
        # Derive file-year suffix from config start/end dates
        start_year = pd.to_datetime(self.config['start_date']).year
        end_year = pd.to_datetime(self.config['end_date']).year
        
        # Validate weather data
        print("  Checking weather data...")
        weather_files = InputValidator.validate_weather_data(
            self.config['weather_path'],
            start_year,
            end_year
        )

        # Build coords from Precipitation file
        print("  Extracting coordinates from precipitation grid...")
        coords_df = self._get_coordinates_from_weather(Path(weather_files['Precipitation']))
        
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
