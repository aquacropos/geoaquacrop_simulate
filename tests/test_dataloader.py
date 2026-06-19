"""Tests for processor.DataLoader (per-point input loading)."""
import numpy as np
import pandas as pd
import pytest

from aquacropgrid_run.config import SimulationConfig, InputValidator
from aquacropgrid_run.processor import DataLoader


@pytest.fixture
def validated(valid_config_dict):
    """Run full validation once and hand back the inputs dict + coords."""
    sc = SimulationConfig(valid_config_dict)
    return sc.validate_all_inputs()


class TestLoadWeather:
    def test_column_order_and_date(self, validated, grid):
        df = DataLoader.load_weather_for_point(
            validated["weather"], grid["y"][0], grid["x"][0],
            grid["start_date"], grid["end_date"])
        assert list(df.columns) == ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]
        assert pd.api.types.is_datetime64_any_dtype(df["Date"])

    def test_reference_et_floored(self, tmp_path, writers, grid):
        # write weather where ReferenceET is 0 everywhere → must be clipped to 0.01
        d = tmp_path / "w"; d.mkdir()
        times = pd.date_range(f"{grid['start_year']}-01-01", f"{grid['end_year']}-12-31", freq="D")
        import xarray as xr
        for var, fill in [("MinTemp", 10.0), ("MaxTemp", 25.0),
                          ("Precipitation", 2.0), ("ReferenceET", 0.0)]:
            arr = np.full((len(times), len(grid["y"]), len(grid["x"])), fill, dtype="float32")
            xr.Dataset({var: (("time", "y", "x"), arr)},
                       coords={"time": times, "y": grid["y"], "x": grid["x"]}
                       ).to_netcdf(d / f"{var}{grid['start_year']}{grid['end_year']}.nc")
        files = InputValidator.validate_weather_data(d, grid["start_year"], grid["end_year"])
        df = DataLoader.load_weather_for_point(
            files, grid["y"][0], grid["x"][0], grid["start_date"], grid["end_date"])
        assert (df["ReferenceET"] >= 0.01).all()
        assert df["ReferenceET"].min() == pytest.approx(0.01)


class TestLoadSoil:
    def test_returns_soil_object(self, validated, grid):
        soil = DataLoader.load_soil_for_point(validated["soil"], grid["x"][0], grid["y"][0])
        assert soil is not None
        assert hasattr(soil, "profile")

    def test_nan_layer_returns_none(self, tmp_path, writers, validated, grid):
        # write a soil set with NaN in the top layer at the target cell
        import xarray as xr
        d = tmp_path / "s"; d.mkdir()
        from aquacropgrid_run.config import InputRequirements
        for fn in InputRequirements.SOIL_FILES:
            clay = np.full((len(grid["y"]), len(grid["x"])), 25.0, dtype="float32")
            if fn == "soil_0-5.nc":
                clay[0, 0] = np.nan
            xr.Dataset({
                "Clay": (("y", "x"), clay),
                "Sand": (("y", "x"), np.full((len(grid["y"]), len(grid["x"])), 40.0, dtype="float32")),
                "Silt": (("y", "x"), np.full((len(grid["y"]), len(grid["x"])), 35.0, dtype="float32")),
                "Som": (("y", "x"), np.full((len(grid["y"]), len(grid["x"])), 2.0, dtype="float32")),
            }, coords={"y": grid["y"], "x": grid["x"]}).to_netcdf(d / fn)
        files = InputValidator.validate_soil_data(d, validated["coords"])
        soil = DataLoader.load_soil_for_point(files, grid["x"][0], grid["y"][0])
        assert soil is None


class TestLoadPhenology:
    def test_valid_point(self, validated, grid):
        ph = DataLoader.load_phenology_for_point(
            validated["phenology"], grid["x"][0], grid["y"][0], "Maize", "rainfed")
        assert ph["planting_day"] == pytest.approx(120.0)
        # growing_season_length written as timedelta64[D] → converted to days
        assert ph["growing_season_length"] == pytest.approx(130.0)

    def test_timedelta_conversion(self, tmp_path, writers, grid):
        d = tmp_path / "p"; d.mkdir()
        writers["phenology"](d, as_timedelta=True)
        files = {"planting_day": str(d / "cropcalendar.nc"),
                 "growing_season_length": str(d / "cropcalendar.nc")}
        ph = DataLoader.load_phenology_for_point(files, grid["x"][0], grid["y"][0], "Maize", "rainfed")
        assert ph["growing_season_length"] == pytest.approx(130.0)

    def test_plain_float_gsl(self, tmp_path, writers, grid):
        d = tmp_path / "p"; d.mkdir()
        writers["phenology"](d, as_timedelta=False)
        files = {"planting_day": str(d / "cropcalendar.nc"),
                 "growing_season_length": str(d / "cropcalendar.nc")}
        ph = DataLoader.load_phenology_for_point(files, grid["x"][0], grid["y"][0], "Maize", "rainfed")
        assert ph["growing_season_length"] == pytest.approx(130.0)

    def test_missing_crop_returns_nans(self, validated, grid):
        ph = DataLoader.load_phenology_for_point(
            validated["phenology"], grid["x"][0], grid["y"][0], "Sorghum", "rainfed")
        assert np.isnan(ph["planting_day"])
        assert np.isnan(ph["growing_season_length"])


class TestLoadSpamArea:
    def test_value_returned(self, validated, grid):
        area = DataLoader.load_spam_area_for_point(validated["spam"], grid["x"][0], grid["y"][0])
        assert area == pytest.approx(50.0)

    def test_none_variable_returns_nan(self, validated, grid):
        spam = dict(validated["spam"])
        spam["variable"] = None
        area = DataLoader.load_spam_area_for_point(spam, grid["x"][0], grid["y"][0])
        assert np.isnan(area)

    def test_band_dimension_is_collapsed(self, tmp_path, grid):
        # SPAM rasters sometimes carry a singleton 'band' dim; loader takes max over it
        import xarray as xr
        d = tmp_path / "spam"; d.mkdir()
        data = np.full((1, len(grid["y"]), len(grid["x"])), 42.0, dtype="float32")
        xr.Dataset(
            {"Maize_rf_physical_area": (("band", "y", "x"), data)},
            coords={"band": [1], "y": grid["y"], "x": grid["x"]},
        ).to_netcdf(d / "spam2010_physical_area.nc")
        spam = {"filepath": str(d / "spam2010_physical_area.nc"),
                "variable": "Maize_rf_physical_area"}
        area = DataLoader.load_spam_area_for_point(spam, grid["x"][0], grid["y"][0])
        assert area == pytest.approx(42.0)
