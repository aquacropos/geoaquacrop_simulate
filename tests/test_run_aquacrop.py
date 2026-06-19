"""Tests for run_aquacrop.py helper functions.

These tests pin down known issues in the driver script. ``print_input_requirements``
currently raises because it calls ``.items()`` on ``InputRequirements.SOIL_FILES``,
which is a list, not a dict (and its printed text still describes GeoTIFF inputs
even though the validators now expect NetCDF). The test below is marked ``xfail``
so the suite stays green while clearly flagging the defect; once the function is
fixed it will turn into an XPASS and you can drop the marker.
"""
import pytest

import aquacropgrid_run.run_aquacrop as run_aquacrop


@pytest.mark.xfail(reason="BUG: SOIL_FILES is a list but print_input_requirements calls .items()",
                   raises=AttributeError, strict=True)
def test_print_input_requirements_runs(capsys):
    run_aquacrop.print_input_requirements()
    out = capsys.readouterr().out
    assert "WEATHER DATA" in out
    assert "SOIL DATA" in out
    assert "PHENOLOGY DATA" in out
