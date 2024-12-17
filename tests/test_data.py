import pytest
from pathlib import Path
from tidepredictor.data import ConstituentReader


@pytest.fixture
def level_constituent_file_path() -> Path:
    p = Path("tests/data/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase_test.nc")
    assert p.exists()
    return p


def test_read_constituents(level_constituent_file_path) -> None:
    reader = ConstituentReader(level_constituent_file_path)

    const = reader.read_constituents(lat=0.0, lon=0.0)
    assert const["M2"].amplitude == pytest.approx(0.44190001487731934)
    assert const["M2"].phase == pytest.approx(103.89859771728516)

    expected_keys = "Q1 MF P1 K1 MM O1 M2 S2 M4 MN4 MS4 N2 K2".split()

    assert set(const.keys()) == set(expected_keys)
