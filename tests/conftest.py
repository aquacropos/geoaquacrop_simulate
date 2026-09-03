"""
Shared pytest fixtures for the geoaquacrop_simulate test suite.

The package is imported as ``geoaquacrop_simulate.*``. Install it in editable mode
before running the tests: ``pip install -e ".[dev]"``.
"""
import sys

# --- work around an aquacrop import quirk ------------------------------------
# This aquacrop version's __init__ only binds AquaCropModel/Soil/Crop/etc. when
# "-m" is NOT present in sys.argv. Running "pytest -m 'not slow'" puts "-m" in
# sys.argv, which would leave aquacrop half-imported and break "from aquacrop
# import AquaCropModel". We import aquacrop once here with a sanitized argv so
# the names are bound and cached before any test (or the package code) needs it.
_orig_argv = sys.argv
try:
    sys.argv = [sys.argv[0]]
    import aquacrop  # noqa: F401  (populates aquacrop.AquaCropModel, .Soil, ...)
finally:
    sys.argv = _orig_argv

import numpy as np
import pandas as pd
import xarray as xr
import pytest
from pathlib import Path


# --- grid definition shared by all synthetic inputs --------------------------
# A tiny 3 x 2 grid. The bottom-right cell (y=10.10, x=8.05) is deliberately
# left as NaN in the weather data so we can test the domain mask and the
# "missing soil/weather" code paths.
GRID_Y = np.array([10.00, 10.05, 10.10], dtype="float64")
GRID_X = np.array([8.00, 8.05], dtype="float64")
MASKED_CELL = (2, 1)  # (y index, x index) that is NaN in weather
START_DATE = "2008/01/01"
END_DATE = "2010/12/31"
START_YEAR = 2008
END_YEAR = 2010


def _write_weather(directory: Path, sy: int = START_YEAR, ey: int = END_YEAR,
                   drop_dim: bool = False, drop_var: bool = False):
    """Write the four weather NetCDF files named ``{var}{sy}{ey}.nc``."""
    times = pd.date_range(f"{sy}-01-01", f"{ey}-12-31", freq="D")
    fills = {"MinTemp": 12.0, "MaxTemp": 28.0,
             "Precipitation": 3.0, "ReferenceET": 5.0}
    for var, fill in fills.items():
        data = np.full((len(times), len(GRID_Y), len(GRID_X)), fill, dtype="float32")
        data[:, MASKED_CELL[0], MASKED_CELL[1]] = np.nan
        if drop_var and var == "ReferenceET":
            # write under a wrong variable name to trigger the "missing variable" path
            ds = xr.Dataset({"WRONG": (("time", "y", "x"), data)},
                            coords={"time": times, "y": GRID_Y, "x": GRID_X})
        elif drop_dim and var == "ReferenceET":
            # collapse the time dimension to trigger the "missing dimension" path
            ds = xr.Dataset({var: (("y", "x"), data[0])},
                            coords={"y": GRID_Y, "x": GRID_X})
        else:
            ds = xr.Dataset({var: (("time", "y", "x"), data)},
                            coords={"time": times, "y": GRID_Y, "x": GRID_X})
        ds.to_netcdf(directory / f"{var}{sy}{ey}.nc")


def _write_soil(directory: Path, missing_var: bool = False):
    """Write the six soil NetCDF files with Clay/Sand/Silt/Som."""
    from geoaquacrop_simulate.config import InputRequirements
    for fn in InputRequirements.SOIL_FILES:
        variables = {
            "Clay": np.full((len(GRID_Y), len(GRID_X)), 25.0, dtype="float32"),
            "Sand": np.full((len(GRID_Y), len(GRID_X)), 40.0, dtype="float32"),
            "Silt": np.full((len(GRID_Y), len(GRID_X)), 35.0, dtype="float32"),
            "Som": np.full((len(GRID_Y), len(GRID_X)), 2.0, dtype="float32"),
        }
        if missing_var:
            variables.pop("Som")
        ds = xr.Dataset({k: (("y", "x"), v) for k, v in variables.items()},
                        coords={"y": GRID_Y, "x": GRID_X})
        ds.to_netcdf(directory / fn)


def _write_phenology(directory: Path, crop_prefix: str = "Maize",
                     as_timedelta: bool = True, include_gsl: bool = True):
    """Write cropcalendar.nc with planting + growing-season-length variables."""
    plant = np.full((len(GRID_Y), len(GRID_X)), 120, dtype="float32")
    if as_timedelta:
        gsl = np.full((len(GRID_Y), len(GRID_X)), 130, dtype="timedelta64[D]")
    else:
        gsl = np.full((len(GRID_Y), len(GRID_X)), 130, dtype="float32")
    data_vars = {f"{crop_prefix}_rf_planting": (("y", "x"), plant)}
    if include_gsl:
        data_vars[f"{crop_prefix}_rf_growing_season_length"] = (("y", "x"), gsl)
    ds = xr.Dataset(data_vars, coords={"y": GRID_Y, "x": GRID_X})
    ds.to_netcdf(directory / "cropcalendar.nc")


def _write_spam(directory: Path, refyear: int = 2010, var_name: str = "Maize_rf_physical_area",
                area: float = 50.0):
    """Write spam{refyear}_physical_area.nc."""
    ds = xr.Dataset(
        {var_name: (("y", "x"), np.full((len(GRID_Y), len(GRID_X)), area, dtype="float32"))},
        coords={"y": GRID_Y, "x": GRID_X},
    )
    ds.to_netcdf(directory / f"spam{refyear}_physical_area.nc")


@pytest.fixture(scope="session")
def grid():
    """Expose grid constants to tests."""
    return {"y": GRID_Y, "x": GRID_X, "masked_cell": MASKED_CELL,
            "start_date": START_DATE, "end_date": END_DATE,
            "start_year": START_YEAR, "end_year": END_YEAR}


@pytest.fixture
def processed_dir(tmp_path):
    """A directory populated with a complete, valid set of synthetic inputs."""
    d = tmp_path / "processed"
    d.mkdir()
    _write_weather(d)
    _write_soil(d)
    _write_phenology(d)
    _write_spam(d, refyear=2010)
    return d


@pytest.fixture
def valid_config_dict(processed_dir, tmp_path):
    """A valid config dict pointing at the synthetic inputs."""
    from aquacrop import InitialWaterContent
    return {
        "weather_path": str(processed_dir),
        "soil_path": str(processed_dir),
        "pheno_path": str(processed_dir),
        "spam_path": str(processed_dir),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "crop": "Maize",
        "irrigation": "rainfed",
        "initial_water_content": InitialWaterContent(),
        "output_dir": str(tmp_path / "outputs"),
    }


# expose the writer helpers for tests that need to build broken inputs
@pytest.fixture
def writers():
    return {
        "weather": _write_weather,
        "soil": _write_soil,
        "phenology": _write_phenology,
        "spam": _write_spam,
    }
