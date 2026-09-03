"""Tests for processor.CropAdjuster.adjust_crop_phenology."""
import numpy as np
import pytest

from aquacrop import Crop
from geoaquacrop_simulate.processor import CropAdjuster


def _fresh_maize():
    c = Crop("Maize", planting_date="01/01")
    c.CalendarType = 1  # calendar-day mode, as the worker sets it
    return c


class TestAdjustPhenology:
    def test_sets_planting_date_and_maturity(self):
        crop = CropAdjuster.adjust_crop_phenology(
            _fresh_maize(), {"planting_day": 120, "growing_season_length": 130})
        assert crop is not None
        # planting day 120 of a non-leap reference year (2000 is leap, day 120 = 29 Apr)
        assert crop.planting_date == "04/30"
        # MaturityCD is scaled to the requested season length
        assert crop.MaturityCD == 130

    @pytest.mark.parametrize("pheno", [
        {"planting_day": np.nan, "growing_season_length": 130},
        {"planting_day": 120, "growing_season_length": np.nan},
        {"planting_day": np.nan, "growing_season_length": np.nan},
    ])
    def test_nan_inputs_return_none(self, pheno):
        assert CropAdjuster.adjust_crop_phenology(_fresh_maize(), pheno) is None

    def test_missing_keys_return_none(self):
        assert CropAdjuster.adjust_crop_phenology(_fresh_maize(), {}) is None

    def test_non_numeric_returns_none(self):
        result = CropAdjuster.adjust_crop_phenology(
            _fresh_maize(), {"planting_day": "oops", "growing_season_length": 130})
        assert result is None

    def test_longer_season_scales_phenology_up(self):
        base_maturity = _fresh_maize().MaturityCD
        short = CropAdjuster.adjust_crop_phenology(
            _fresh_maize(), {"planting_day": 100, "growing_season_length": base_maturity})
        long = CropAdjuster.adjust_crop_phenology(
            _fresh_maize(), {"planting_day": 100, "growing_season_length": base_maturity * 2})
        # Emergence should grow with the scaling factor
        assert long.EmergenceCD > short.EmergenceCD
        assert long.SenescenceCD > short.SenescenceCD

    def test_scaling_factor_of_one_is_near_identity(self):
        crop = _fresh_maize()
        original_emergence = crop.EmergenceCD
        adjusted = CropAdjuster.adjust_crop_phenology(
            crop, {"planting_day": 100, "growing_season_length": crop.MaturityCD})
        # sf == 1 → emergence unchanged (rounded)
        assert adjusted.EmergenceCD == round(original_emergence)
