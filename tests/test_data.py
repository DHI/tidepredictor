import pytest
from pathlib import Path
from tidepredictor import PredictionType, get_default_constituent_path
from tidepredictor.data import ConstituentReader


@pytest.fixture
def level_constituent_file_path() -> Path:
    p = Path("tests/data/level.nc")
    assert p.exists()
    return p


@pytest.fixture
def current_constituent_file_path() -> Path:
    p = Path("tests/data/currents.nc")
    assert p.exists()
    return p


def test_read_level_onstituents(level_constituent_file_path) -> None:
    reader = ConstituentReader(level_constituent_file_path)

    const = reader.get_level_constituents(lat=0.0, lon=0.0)
    assert const["M2"].amplitude == pytest.approx(0.44190001487731934)
    assert const["M2"].phase == pytest.approx(103.89859771728516)

    expected_keys = "Q1 MF P1 K1 MM O1 M2 S2 M4 MN4 MS4 N2 K2".split()

    assert set(const.keys()) == set(expected_keys)


def test_read_current_constituents(current_constituent_file_path) -> None:
    reader = ConstituentReader(current_constituent_file_path)

    const = reader.get_current_constituents(lat=0.0, lon=0.0)

    # TODO assert correct values
    expected_keys = "Q1 MF P1 K1 MM O1 M2 S2 M4 MN4 MS4 N2 K2".split()

    assert set(const.keys()) == set(expected_keys)


def test_get_default_constiutent_path() -> None:
    import xarray as xr

    path = get_default_constituent_path(PredictionType.level)
    with xr.open_dataset(path) as ds:
        assert "amplitude" in ds.variables
        assert "phase" in ds.variables

    path = get_default_constituent_path(PredictionType.current)
    with xr.open_dataset(path) as ds:
        assert "major_axis" in ds.variables
        assert "minor_axis" in ds.variables
        assert "inclination" in ds.variables
        assert "phase" in ds.variables
