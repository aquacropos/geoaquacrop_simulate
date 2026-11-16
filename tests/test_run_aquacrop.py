"""Tests for run_aquacrop.py helper functions.

These tests pin down known issues in the driver script. ``print_input_requirements``
currently raises because it calls ``.items()`` on ``InputRequirements.SOIL_FILES``,
which is a list, not a dict (and its printed text still describes GeoTIFF inputs
even though the validators now expect NetCDF). The test below is marked ``xfail``
so the suite stays green while clearly flagging the defect; once the function is
fixed it will turn into an XPASS and you can drop the marker.
"""
import pytest

import geoaquacrop_simulate.run_aquacrop as run_aquacrop


def test_print_input_requirements_runs(capsys):
    run_aquacrop.print_input_requirements()
    out = capsys.readouterr().out
    assert "WEATHER DATA" in out
    assert "SOIL DATA" in out
    assert "PHENOLOGY DATA" in out


def test_all_cells_failed_raises():
    import pandas as pd
    import pytest
    from geoaquacrop_simulate.run_aquacrop import _require_some_cells_ran

    failed = [pd.DataFrame([{"cell_id": i, "error": "bad weather"}]) for i in range(3)]
    with pytest.raises(RuntimeError, match="All 3 cells failed.*bad weather"):
        _require_some_cells_ran(failed, "summary.pkl")


def test_some_cells_ran_passes():
    import pandas as pd
    from geoaquacrop_simulate.run_aquacrop import _require_some_cells_ran

    mixed = [pd.DataFrame([{"cell_id": 0, "error": "bad weather"}]),
             pd.DataFrame([{"cell_id": 1, "Dry yield (tonne/ha)": 5.0}])]
    _require_some_cells_ran(mixed, "summary.pkl")
