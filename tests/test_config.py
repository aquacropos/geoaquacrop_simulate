"""Tests for config.py: SimulationConfig and InputValidator."""
import warnings
from pathlib import Path

import pytest

from geoaquacrop_sim.config import SimulationConfig, InputValidator, InputRequirements


# ---------------------------------------------------------------------------
# SimulationConfig._validate_config
# ---------------------------------------------------------------------------
class TestSimulationConfig:
    def test_valid_config_converts_paths_and_makes_output_dir(self, valid_config_dict):
        sc = SimulationConfig(valid_config_dict)
        for key in ["weather_path", "soil_path", "pheno_path", "spam_path", "output_dir"]:
            assert isinstance(sc.config[key], Path)
        assert sc.config["output_dir"].exists()

    def test_missing_key_raises(self, valid_config_dict):
        del valid_config_dict["crop"]
        with pytest.raises(ValueError, match="Missing configuration keys"):
            SimulationConfig(valid_config_dict)

    @pytest.mark.parametrize("bad_date", ["2008-01-01", "2008/01", "01/01/2008/00"])
    def test_bad_date_format_raises(self, valid_config_dict, bad_date):
        valid_config_dict["start_date"] = bad_date
        with pytest.raises(ValueError, match="date"):
            SimulationConfig(valid_config_dict)

    def test_impossible_date_raises(self, valid_config_dict):
        valid_config_dict["start_date"] = "2008/13/45"
        with pytest.raises(ValueError, match="date"):
            SimulationConfig(valid_config_dict)

    def test_invalid_crop_raises(self, valid_config_dict):
        valid_config_dict["crop"] = "Banana"
        with pytest.raises(ValueError, match="Invalid crop"):
            SimulationConfig(valid_config_dict)

    def test_crop_is_case_sensitive(self, valid_config_dict):
        valid_config_dict["crop"] = "maize"  # lower-case not in CROPS
        with pytest.raises(ValueError, match="Invalid crop"):
            SimulationConfig(valid_config_dict)

    def test_invalid_irrigation_raises(self, valid_config_dict):
        valid_config_dict["irrigation"] = "drip"
        with pytest.raises(ValueError, match="Invalid irrigation"):
            SimulationConfig(valid_config_dict)

    @pytest.mark.parametrize("irr", ["Rainfed", "RAINFED", "Irrigated", "irrigated"])
    def test_irrigation_is_case_insensitive(self, valid_config_dict, irr):
        valid_config_dict["irrigation"] = irr
        sc = SimulationConfig(valid_config_dict)  # should not raise
        assert sc.config["irrigation"] == irr


# ---------------------------------------------------------------------------
# SimulationConfig.validate_all_inputs / coordinate extraction
# ---------------------------------------------------------------------------
class TestValidateAllInputs:
    def test_happy_path_returns_all_sections(self, valid_config_dict):
        sc = SimulationConfig(valid_config_dict)
        out = sc.validate_all_inputs()
        assert set(out) == {"coords", "weather", "soil", "phenology", "spam"}

    def test_coords_exclude_masked_cell(self, valid_config_dict, grid):
        # 6 cells, 1 masked → 5 valid coordinates
        sc = SimulationConfig(valid_config_dict)
        out = sc.validate_all_inputs()
        n_total = len(grid["y"]) * len(grid["x"])
        assert len(out["coords"]) == n_total - 1
        assert {"y", "x"}.issubset(out["coords"].columns)


# ---------------------------------------------------------------------------
# InputValidator.validate_weather_data
# ---------------------------------------------------------------------------
class TestValidateWeather:
    def test_all_files_present(self, processed_dir, grid):
        files = InputValidator.validate_weather_data(
            processed_dir, grid["start_year"], grid["end_year"])
        assert set(files) == set(InputRequirements.WEATHER_VARS)

    def test_missing_file_raises(self, processed_dir, grid):
        (processed_dir / f"MinTemp{grid['start_year']}{grid['end_year']}.nc").unlink()
        with pytest.raises(ValueError, match="Missing weather file"):
            InputValidator.validate_weather_data(
                processed_dir, grid["start_year"], grid["end_year"])

    def test_missing_variable_raises(self, tmp_path, writers, grid):
        d = tmp_path / "w"; d.mkdir()
        writers["weather"](d, drop_var=True)
        with pytest.raises(ValueError, match="must contain variable"):
            InputValidator.validate_weather_data(d, grid["start_year"], grid["end_year"])

    def test_missing_dimension_raises(self, tmp_path, writers, grid):
        d = tmp_path / "w"; d.mkdir()
        writers["weather"](d, drop_dim=True)
        with pytest.raises(ValueError, match="missing dimensions"):
            InputValidator.validate_weather_data(d, grid["start_year"], grid["end_year"])


# ---------------------------------------------------------------------------
# InputValidator.validate_soil_data
# ---------------------------------------------------------------------------
class TestValidateSoil:
    def test_all_layers_returned(self, processed_dir, valid_config_dict):
        sc = SimulationConfig(valid_config_dict)
        coords = sc.validate_all_inputs()["coords"]
        files = InputValidator.validate_soil_data(processed_dir, coords)
        assert set(files) == {"0_5cm", "5_15cm", "15_30cm", "30_60cm", "60_100cm", "100_200cm"}

    def test_missing_file_raises(self, processed_dir, valid_config_dict):
        sc = SimulationConfig(valid_config_dict)
        coords = sc.validate_all_inputs()["coords"]
        (processed_dir / "soil_0-5.nc").unlink()
        with pytest.raises(ValueError, match="Missing soil file"):
            InputValidator.validate_soil_data(processed_dir, coords)

    def test_missing_variable_raises(self, tmp_path, writers, valid_config_dict):
        # build a valid coord frame from the good fixture first
        sc = SimulationConfig(valid_config_dict)
        coords = sc.validate_all_inputs()["coords"]
        d = tmp_path / "s"; d.mkdir()
        writers["soil"](d, missing_var=True)
        with pytest.raises(ValueError, match="missing variables"):
            InputValidator.validate_soil_data(d, coords)


# ---------------------------------------------------------------------------
# InputValidator.validate_phenology_data
# ---------------------------------------------------------------------------
class TestValidatePhenology:
    def _coords(self, valid_config_dict):
        return SimulationConfig(valid_config_dict).validate_all_inputs()["coords"]

    def test_valid_returns_two_keys(self, processed_dir, valid_config_dict):
        coords = self._coords(valid_config_dict)
        files = InputValidator.validate_phenology_data(
            processed_dir, "Maize", "rainfed", coords)
        assert set(files) == {"planting_day", "growing_season_length"}

    def test_unsupported_crop_raises(self, processed_dir, valid_config_dict):
        coords = self._coords(valid_config_dict)
        with pytest.raises(ValueError, match="Unsupported crop"):
            InputValidator.validate_phenology_data(processed_dir, "Banana", "rainfed", coords)

    def test_missing_file_raises(self, processed_dir, valid_config_dict):
        coords = self._coords(valid_config_dict)
        (processed_dir / "cropcalendar.nc").unlink()
        with pytest.raises(ValueError, match="Missing phenology file"):
            InputValidator.validate_phenology_data(processed_dir, "Maize", "rainfed", coords)

    def test_missing_gsl_variable_raises(self, tmp_path, writers, valid_config_dict):
        coords = self._coords(valid_config_dict)
        d = tmp_path / "p"; d.mkdir()
        writers["phenology"](d, include_gsl=False)
        with pytest.raises(ValueError, match="growing season"):
            InputValidator.validate_phenology_data(d, "Maize", "rainfed", coords)

    def test_no_planting_variable_for_crop_raises(self, processed_dir, valid_config_dict):
        coords = self._coords(valid_config_dict)
        # cropcalendar only has Maize vars; ask for Sorghum
        with pytest.raises(ValueError, match="No planting variable"):
            InputValidator.validate_phenology_data(processed_dir, "Sorghum", "rainfed", coords)


# ---------------------------------------------------------------------------
# InputValidator.validate_spam_data
# ---------------------------------------------------------------------------
class TestValidateSpam:
    @pytest.mark.parametrize("sy,ey,expected", [
        (2008, 2010, 2010),   # mean 2009 -> nearer 2010
        (2000, 2005, 2010),   # mean 2002.5 ceil 2003 -> nearer 2010
        (2014, 2026, 2020),   # mean 2020 -> 2020
        (2018, 2022, 2020),   # mean 2020 -> 2020
    ])
    def test_refyear_selection(self, tmp_path, writers, sy, ey, expected):
        d = tmp_path / "spam"; d.mkdir()
        writers["spam"](d, refyear=2010)
        writers["spam"](d, refyear=2020)
        res = InputValidator.validate_spam_data(d, sy, ey, "Maize", "rainfed")
        assert f"spam{expected}_physical_area.nc" in res["filepath"]

    def test_variable_name_for_crop(self, tmp_path, writers):
        d = tmp_path / "spam"; d.mkdir()
        writers["spam"](d, refyear=2010, var_name="Maize_rf_physical_area")
        res = InputValidator.validate_spam_data(d, 2008, 2010, "Maize", "rainfed")
        assert res["variable"] == "Maize_rf_physical_area"

    def test_missing_file_raises(self, tmp_path):
        d = tmp_path / "spam"; d.mkdir()
        with pytest.raises(ValueError, match="Missing SPAM"):
            InputValidator.validate_spam_data(d, 2008, 2010, "Maize", "rainfed")

    def test_paddyrice_falls_back_to_paddyrice(self, tmp_path, writers):
        d = tmp_path / "spam"; d.mkdir()
        writers["spam"](d, refyear=2010, var_name="PaddyRice_rf_physical_area")
        res = InputValidator.validate_spam_data(d, 2008, 2010, "PaddyRice1", "rainfed")
        assert res["variable"] == "PaddyRice_rf_physical_area"

    def test_wheat_winter_falls_back_to_wheat(self, tmp_path, writers):
        d = tmp_path / "spam"; d.mkdir()
        writers["spam"](d, refyear=2010, var_name="Wheat_rf_physical_area")
        res = InputValidator.validate_spam_data(d, 2008, 2010, "Wheat_winter", "rainfed")
        assert res["variable"] == "Wheat_rf_physical_area"

    def test_missing_variable_no_fallback_warns_and_returns_none(self, tmp_path, writers):
        d = tmp_path / "spam"; d.mkdir()
        # file exists but has only an unrelated variable
        writers["spam"](d, refyear=2010, var_name="Cotton_ir_physical_area")
        with pytest.warns(UserWarning, match="production"):
            res = InputValidator.validate_spam_data(d, 2008, 2010, "Maize", "rainfed")
        assert res["variable"] is None
