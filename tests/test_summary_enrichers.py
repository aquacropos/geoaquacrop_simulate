"""Tests for summary_enrichers.py."""
import numpy as np
import pandas as pd
import pytest

import geoaquacrop_simulate.summary_enrichers as se


class _Logger:
    """Minimal logger capturing warnings."""
    def __init__(self):
        self.warnings = []
    def warning(self, msg, *a, **k):
        self.warnings.append(str(msg))


class _Crop:
    """Stand-in crop exposing only MaturityCD."""
    def __init__(self, maturity=10):
        self.MaturityCD = maturity


def _daily(n=10):
    return pd.DataFrame({
        "dap": range(1, n + 1),
        "season_counter": [0] * n,
        "Tr": [2.0] * n,
        "Es": [1.0] * n,
    })


def _context(summary_irrigation="rainfed", area=10.0, maturity=10, n_days=10):
    wf = _daily(n_days)
    return {
        "crop_area_ha": area,
        "crop_obj": _Crop(maturity),
        "daily": {"water_flux": wf, "crop_growth": pd.DataFrame({"dap": range(1, n_days + 1)})},
        "weather_df": pd.DataFrame({"Precipitation": [3.0] * n_days}),
        "config": {"irrigation": summary_irrigation},
        "logger": _Logger(),
    }


def _summary(**extra):
    base = {"Season": 0, "Dry yield (tonne/ha)": 5.0, "Seasonal irrigation (mm)": 200.0}
    base.update(extra)
    return pd.DataFrame([base])


# ---------------------------------------------------------------------------
# Registry / decorator
# ---------------------------------------------------------------------------
class TestRegistry:
    def test_registry_is_populated(self):
        assert len(se._REGISTRY) >= 8

    def test_decorator_registers_and_returns_function(self):
        before = len(se._REGISTRY)

        @se.enricher
        def _dummy(summary, context):
            return summary

        assert se._REGISTRY[-1] is _dummy
        assert len(se._REGISTRY) == before + 1
        se._REGISTRY.pop()  # clean up so other tests are unaffected

    def test_apply_all_swallows_and_logs_failures(self):
        ctx = _context()
        # add an enricher that raises
        @se.enricher
        def _boom(summary, context):
            raise RuntimeError("kaboom")
        try:
            out = se.apply_all(_summary(), ctx)
            assert isinstance(out, pd.DataFrame)  # did not propagate
            assert any("kaboom" in w for w in ctx["logger"].warnings)
        finally:
            se._REGISTRY.pop()


# ---------------------------------------------------------------------------
# _sum_during_season
# ---------------------------------------------------------------------------
class TestSumDuringSeason:
    def test_masks_to_maturity(self):
        df = pd.DataFrame({"dap": range(1, 21), "season_counter": [0] * 20, "Tr": [1.0] * 20})
        # maturity 10 → only first 10 days counted
        out = se._sum_during_season(df, "Tr", _Crop(10), _summary())
        assert out[0] == pytest.approx(10.0)

    def test_one_total_per_season(self):
        # two seasons of 10 days each; Tr = 1 in the first, 2 in the second
        df = pd.DataFrame({
            "dap": list(range(1, 11)) * 2,
            "season_counter": [0] * 10 + [1] * 10,
            "Tr": [1.0] * 10 + [2.0] * 10,
        })
        summary = pd.DataFrame({"Season": [0, 1], "Dry yield (tonne/ha)": [5.0, 5.0]})
        out = se._sum_during_season(df, "Tr", _Crop(10), summary)
        assert list(out) == pytest.approx([10.0, 20.0])

    def test_missing_column_returns_nan(self):
        df = pd.DataFrame({"dap": range(1, 11), "season_counter": [0] * 10})
        assert np.isnan(se._sum_during_season(df, "Tr", _Crop(10), _summary()))

    def test_no_dap_returns_nan(self):
        df = pd.DataFrame({"Tr": [2.0] * 5})
        assert np.isnan(se._sum_during_season(df, "Tr", _Crop(10), _summary()))


# ---------------------------------------------------------------------------
# individual enrichers
# ---------------------------------------------------------------------------
class TestEnrichers:
    def test_seasonal_precip(self):
        out = se.add_seasonal_precip(_summary(), _context(n_days=10, maturity=10))
        assert out["seasonal_precip_mm"].iloc[0] == pytest.approx(30.0)

    def test_seasonal_precip_missing_inputs_nan(self):
        ctx = _context()
        ctx["weather_df"] = None
        out = se.add_seasonal_precip(_summary(), ctx)
        assert np.isnan(out["seasonal_precip_mm"].iloc[0])

    def test_seasonal_et(self):
        out = se.add_seasonal_et(_summary(), _context(maturity=10, n_days=10))
        assert out["seasonal_et_mm"].iloc[0] == pytest.approx(30.0)   # 10*(2+1)
        assert out["seasonal_transpiration_mm"].iloc[0] == pytest.approx(20.0)

    def test_metrics_are_per_season(self):
        # two 10-day seasons: rain 3 mm/day then 1 mm/day, Tr+Es 3 then 6 mm/day
        n = 10
        wf = pd.DataFrame({
            "dap": list(range(1, n + 1)) * 2,
            "season_counter": [0] * n + [1] * n,
            "Tr": [2.0] * n + [4.0] * n,
            "Es": [1.0] * n + [2.0] * n,
        })
        ctx = _context(summary_irrigation="irrigated")
        ctx["daily"]["water_flux"] = wf
        ctx["weather_df"] = pd.DataFrame({"Precipitation": [3.0] * n + [1.0] * n})
        summary = pd.DataFrame({
            "Season": [0, 1],
            "Dry yield (tonne/ha)": [6.0, 6.0],
            "Seasonal irrigation (mm)": [100.0, 200.0],
        })
        out = se.apply_all(summary, ctx)
        assert list(out["seasonal_precip_mm"]) == pytest.approx([30.0, 10.0])
        assert list(out["seasonal_et_mm"]) == pytest.approx([30.0, 60.0])
        assert list(out["total_water_input_mm"]) == pytest.approx([130.0, 210.0])
        assert list(out["wp_et_kg_per_m3"]) == pytest.approx([20.0, 10.0])
        assert list(out["wp_irrigation_kg_per_m3"]) == pytest.approx([6.0, 3.0])

    def test_total_water_input(self):
        summ = _summary(seasonal_precip_mm=30.0)
        out = se.add_total_water_input(summ, _context())
        assert out["total_water_input_mm"].iloc[0] == pytest.approx(230.0)  # 30 + 200

    def test_production_with_area(self):
        out = se.add_production(_summary(), _context(area=10.0))
        assert out["production_tonnes"].iloc[0] == pytest.approx(50.0)  # 5 t/ha * 10 ha

    def test_production_nan_area(self):
        out = se.add_production(_summary(), _context(area=np.nan))
        assert np.isnan(out["production_tonnes"].iloc[0])

    def test_season_length(self):
        out = se.add_season_length(_summary(), _context(maturity=137))
        assert out["season_length_days"].iloc[0] == 137

    def test_water_productivity_et(self):
        summ = _summary(seasonal_et_mm=100.0)
        out = se.add_water_productivity_et(summ, _context())
        assert out["wp_et_kg_per_m3"].iloc[0] == pytest.approx(5.0)  # 5*100/100

    def test_water_productivity_et_zero_nan(self):
        summ = _summary(seasonal_et_mm=0.0)
        out = se.add_water_productivity_et(summ, _context())
        assert np.isnan(out["wp_et_kg_per_m3"].iloc[0])

    def test_rainfall_use_efficiency(self):
        summ = _summary(seasonal_precip_mm=250.0)
        out = se.add_rainfall_use_efficiency(summ, _context())
        assert out["rainfall_use_efficiency_kg_per_m3"].iloc[0] == pytest.approx(2.0)

    def test_irrigation_wp_only_for_irrigated(self):
        # rainfed → column not added
        out = se.add_irrigation_wp(_summary(), _context(summary_irrigation="rainfed"))
        assert "wp_irrigation_kg_per_m3" not in out.columns

    def test_irrigation_wp_for_irrigated(self):
        out = se.add_irrigation_wp(_summary(), _context(summary_irrigation="irrigated"))
        assert out["wp_irrigation_kg_per_m3"].iloc[0] == pytest.approx(2.5)  # 5*100/200

    def test_full_pipeline_adds_all_expected_columns(self):
        out = se.apply_all(_summary(), _context(summary_irrigation="irrigated"))
        expected = {
            "seasonal_precip_mm", "seasonal_et_mm", "seasonal_transpiration_mm",
            "total_water_input_mm", "production_tonnes", "season_length_days",
            "wp_et_kg_per_m3", "rainfall_use_efficiency_kg_per_m3",
            "wp_irrigation_kg_per_m3",
        }
        assert expected.issubset(set(out.columns))
