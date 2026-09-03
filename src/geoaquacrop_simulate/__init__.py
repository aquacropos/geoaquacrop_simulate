"""Gridded FAO AquaCrop simulation.

The simulation stage of the GeoAquaCrop toolchain. Usable on its own::

    import geoaquacrop_simulate as sim

    config = sim.example_config()
    config['crop'] = 'Wheat_winter'
    summary_file, daily_file = sim.run(config)

or through the unified toolchain façade, which re-exports exactly these
names::

    import geoaquacrop as gac

    gac.simulate.run(config)

Everything a user needs is exported here; the module layout underneath is an
implementation detail.
"""
from importlib import import_module as _import_module

__all__ = [
    "run",
    "example_config",
    "input_requirements",
    "build_reference",
    "correct",
    "compare",
    "load_results",
]

try:                                    # single source of truth: the metadata
    from importlib.metadata import version as _version
    __version__ = _version("geoaquacrop_simulate")
except Exception:                       # not installed (e.g. running from source)
    __version__ = "0.0.0.dev0"

# Submodules are imported on first use so that `import geoaquacrop_simulate`
# stays cheap and the optional correction dependencies (geopandas, matplotlib)
# are only needed by the calls that actually use them.
_LOOKUP = {
    "run": ("run_aquacrop", "run"),
    "input_requirements": ("run_aquacrop", "print_input_requirements"),
    "build_reference": ("build_reference", "build"),
    "compare": ("compare_corrections", "main"),
}


def __getattr__(name):
    if name in _LOOKUP:
        module_name, attr = _LOOKUP[name]
        value = getattr(_import_module(f"{__name__}.{module_name}"), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(list(globals()) + __all__))


def example_config():
    """Return an editable copy of the example simulation configuration."""
    import copy
    return copy.deepcopy(_import_module(f"{__name__}.run_aquacrop").EXAMPLE_CONFIG)


def correct(config, logger=None):
    """Bias-correct or calibrate an already-saved run, without re-simulating.

    Requires ``config['correction']['reuse_results']`` to be set.
    """
    correction = _import_module(f"{__name__}.correction")
    return correction.correct_saved_run(config, logger=logger)


def load_results(path, value_col="Dry yield (tonne/ha)", start_year=None):
    """Load a saved ``summary_results_*.pkl`` as tidy per-year points
    ``[year, y, x, val]``."""
    import pickle
    correction = _import_module(f"{__name__}.correction")
    with open(path, "rb") as fh:
        summary_results = pickle.load(fh)
    return correction.summary_to_points(summary_results, value_col, start_year)
