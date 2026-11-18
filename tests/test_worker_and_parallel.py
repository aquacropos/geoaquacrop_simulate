"""Tests for processor.worker_run and processor.ParallelProcessor.

The successful single-cell run and the full parallel run actually execute
AquaCrop, so they are marked ``slow`` and ``integration``. Run the fast suite
with ``pytest -m 'not slow'``.
"""
import logging
import pickle
import re

import numpy as np
import pandas as pd
import pytest

from geoaquacrop_simulate.config import SimulationConfig
from geoaquacrop_simulate.processor import DataLoader, ParallelProcessor, worker_run, co2_record


@pytest.fixture
def logger():
    lg = logging.getLogger("test_aquacrop")
    lg.addHandler(logging.NullHandler())
    return lg


@pytest.fixture
def validated(valid_config_dict):
    sc = SimulationConfig(valid_config_dict)
    return sc.config, sc.validate_all_inputs()


def _first_row(coords):
    row = coords.iloc[0].copy()
    return row


class TestWorkerErrorPaths:
    def test_missing_soil_returns_error_summary(self, validated, logger, monkeypatch):
        config, inputs = validated
        monkeypatch.setattr(DataLoader, "load_soil_for_point", staticmethod(lambda *a, **k: None))
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        assert res["daily"] is None
        assert res["summary"]["error"].iloc[0] == "Missing soil data"

    def test_invalid_phenology_returns_error_summary(self, validated, logger, monkeypatch):
        config, inputs = validated
        monkeypatch.setattr(
            DataLoader, "load_phenology_for_point",
            staticmethod(lambda *a, **k: {"planting_day": np.nan, "growing_season_length": np.nan}))
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        assert res["summary"]["error"].iloc[0] == "Invalid phenology data"

    def test_empty_weather_returns_error_summary(self, validated, logger, monkeypatch):
        config, inputs = validated
        monkeypatch.setattr(
            DataLoader, "load_weather_for_point",
            staticmethod(lambda *a, **k: pd.DataFrame(
                columns=["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"])))
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        assert res["summary"]["error"].iloc[0] == "Invalid weather data"
        assert res["daily"] is None

    def test_unexpected_exception_is_caught(self, validated, logger, monkeypatch):
        config, inputs = validated

        def _boom(*a, **k):
            raise RuntimeError("weather blew up")

        monkeypatch.setattr(DataLoader, "load_weather_for_point", staticmethod(_boom))
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        assert "weather blew up" in res["summary"]["error"].iloc[0]
        assert res["daily"] is None


class TestSaveResults:
    def test_pickle_roundtrip(self, validated, logger, tmp_path):
        config, inputs = validated
        proc = ParallelProcessor(config, inputs, logger)
        summary = [pd.DataFrame([{"cell_id": 0, "x": 1.0, "y": 2.0}])]
        daily = [{"water_flux": pd.DataFrame({"dap": [1, 2]})}]
        s_file, d_file = proc.save_results(summary, daily, tmp_path)

        assert s_file.exists() and d_file.exists()
        assert re.search(r"summary_results_\d{8}_\d{6}\.pkl", s_file.name)
        assert re.search(r"daily_results_\d{8}_\d{6}\.pkl", d_file.name)

        with open(s_file, "rb") as f:
            loaded = pickle.load(f)
        pd.testing.assert_frame_equal(loaded[0], summary[0])


    def test_save_daily_false_skips_daily_file(self, validated, logger, tmp_path):
        config, inputs = validated
        proc = ParallelProcessor({**config, "save_daily": False}, inputs, logger)
        summary = [pd.DataFrame([{"cell_id": 0, "x": 1.0, "y": 2.0}])]
        daily = [{"water_flux": pd.DataFrame({"dap": [1, 2]})}]
        s_file, d_file = proc.save_results(summary, daily, tmp_path)

        assert s_file.exists()
        assert d_file is None
        assert not list(tmp_path.glob("daily_results_*.pkl"))


class TestCO2Record:
    def _ppm(self, scenario):
        from aquacrop.entities.co2 import CO2
        return CO2(scenario=scenario).co2_data.set_index("year")["ppm"]

    def test_observed_then_default_pathway(self):
        from aquacrop.entities.co2 import CO2
        record = co2_record(None).set_index("year")["ppm"]
        observed = CO2().co2_data.set_index("year")["ppm"]
        assert record.loc[:2025].equals(observed.loc[:2025])
        assert record.loc[2026:].equals(self._ppm("ssp245").loc[2026:])

    def test_named_pathway_after_observations(self):
        record = co2_record("ssp585").set_index("year")["ppm"]
        assert record.loc[2026:].equals(self._ppm("ssp585").loc[2026:])
        assert record.index.is_monotonic_increasing


@pytest.mark.slow
@pytest.mark.integration
class TestIntegration:
    def test_single_cell_runs_end_to_end(self, validated, logger):
        config, inputs = validated
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        assert res["summary"] is not None
        # a successful run has no 'error' column and carries the cell id
        assert "error" not in res["summary"].columns
        assert res["summary"]["cell_id"].iloc[0] == 0
        assert res["daily"] is not None
        assert "water_flux" in res["daily"]

    def test_save_daily_false_returns_no_daily(self, validated, logger):
        """Workers drop daily series so the parent never holds them all."""
        config, inputs = validated
        res = worker_run(0, _first_row(inputs["coords"]), inputs,
                         {**config, "save_daily": False}, logger)
        assert "error" not in res["summary"].columns
        assert res["daily"] is None
        # metrics derived from the daily series are still computed
        assert res["summary"]["seasonal_et_mm"].notna().all()
        assert res["summary"]["deep_percolation_mm"].notna().all()

    def test_drainage_matches_daily_water_flux(self, validated, logger):
        config, inputs = validated
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        wf = res["daily"]["water_flux"]
        summary = res["summary"]
        for _, row in summary.iterrows():
            season = wf[(wf["season_counter"] == row["Season"]) & (wf["dap"] >= 1)
                        & (wf["dap"] <= row["season_length_days"])]
            assert row["deep_percolation_mm"] == pytest.approx(season["DeepPerc"].sum())
            assert row["runoff_mm"] == pytest.approx(season["Runoff"].sum())

    def test_planting_date_is_per_season(self, validated, logger):
        config, inputs = validated
        res = worker_run(0, _first_row(inputs["coords"]), inputs, config, logger)
        summary = res["summary"]
        sown = pd.to_datetime(summary["planting_date"], format="%Y/%m/%d")
        # one full date per season, in successive years
        assert sown.notna().all()
        assert sown.dt.year.is_monotonic_increasing
        assert "nominal_planting_date" in summary

    @pytest.mark.filterwarnings("ignore:spam2010_physical_area.nc missing")
    def test_irrigation_management_reaches_each_cell(self, valid_config_dict, logger):
        sc = SimulationConfig({**valid_config_dict, "irrigation": "irrigated"})
        inputs = sc.validate_all_inputs()
        row = _first_row(inputs["coords"])
        irr = lambda cfg: worker_run(0, row, inputs, cfg, logger)["summary"][
            "Seasonal irrigation (mm)"].sum()
        default = irr(sc.config)
        capped = irr({**sc.config, "irrigation_management": {"MaxIrr": 1}})
        # 1 mm/day over three 130-day seasons at most
        assert capped <= 3 * 130
        assert capped < default

    def test_co2_record_reaches_model(self, validated, logger, monkeypatch):
        import geoaquacrop_simulate.processor as proc
        config, inputs = validated
        seen = []
        real = proc.AquaCropModel

        def spy(*args, **kwargs):
            seen.append(kwargs["co2_concentration"])
            return real(*args, **kwargs)

        monkeypatch.setattr(proc, "AquaCropModel", spy)
        worker_run(0, _first_row(inputs["coords"]), inputs,
                   {**config, "co2_scenario": "ssp585"}, logger)
        ppm = seen[0].co2_data.set_index("year")["ppm"]
        assert ppm.loc[2100] > 1000   # SSP5-8.5 after the observed record

    def test_adaptive_planting_delays_sowing(self, validated, logger):
        config, inputs = validated
        row = _first_row(inputs["coords"])
        fixed = worker_run(0, row, inputs, config, logger)["summary"]
        # synthetic weather averages 20 C, so a 30 C rule never fires and
        # sowing slips by the full PlantMaxDelay
        config = {**config, "adaptive_planting": {"PlantTempThr": 30, "PlantMaxDelay": 10}}
        delayed = worker_run(0, row, inputs, config, logger)["summary"]
        first = lambda df: pd.to_datetime(df["planting_date"].iloc[0], format="%Y/%m/%d")
        assert (first(delayed) - first(fixed)).days == 10

    def test_run_parallel_aggregates_all_cells(self, validated, logger):
        config, inputs = validated
        proc = ParallelProcessor(config, inputs, logger)
        summary, daily = proc.run_parallel(inputs["coords"], max_workers=1)
        assert len(summary) == len(inputs["coords"])
        assert len(daily) == len(inputs["coords"])
