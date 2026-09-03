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

from geoaquacrop_sim.config import SimulationConfig
from geoaquacrop_sim.processor import DataLoader, ParallelProcessor, worker_run


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

    def test_run_parallel_aggregates_all_cells(self, validated, logger):
        config, inputs = validated
        proc = ParallelProcessor(config, inputs, logger)
        summary, daily = proc.run_parallel(inputs["coords"], max_workers=1)
        assert len(summary) == len(inputs["coords"])
        assert len(daily) == len(inputs["coords"])
