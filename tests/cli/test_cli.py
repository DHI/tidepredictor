import json
from typer.testing import CliRunner
from tidepredictor.main import app


def test_success_basic():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "-s",
            "2020-01-01",
            "-e",
            "2020-01-02",
            "--lon",
            "0",
            "--lat",
            "0",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.startswith("time,level\n")


def test_success_json_output():
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["-x", 0.0, "-y", 0.0, "--format", "json"],
    )
    assert result.exit_code == 0

    # check that the output is valid json
    data = json.loads(result.stdout)
    assert "time" in data[0]
    assert "level" in data[0]


def test_success_json_file(tmp_path) -> None:
    path = tmp_path / "foo.json"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["-x", 0.0, "-y", 0.0, "-o", str(path)],
    )
    assert result.exit_code == 0
    assert path.exists()
    with open(path, "r") as f:
        data = json.load(f)
    assert "time" in data[0]
    assert "level" in data[0]


def test_output_file(tmp_path) -> None:
    path = tmp_path / "foo.csv"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "-s",
            "2020-01-01",
            "-e",
            "2020-01-02",
            "--lon",
            "0",
            "--lat",
            "0",
            "-o",
            str(path),
        ],
    )
    assert result.exit_code == 0
    assert result.stdout == ""
    assert path.exists()


def test_invalid_output_file_format(tmp_path) -> None:
    path = tmp_path / "foo.docx"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "-s",
            "2020-01-01",
            "-e",
            "2020-01-02",
            "--lon",
            "0",
            "--lat",
            "0",
            "-o",
            str(path),
        ],
    )
    assert result.exit_code != 0
    assert not path.exists()


def test_no_args():
    runner = CliRunner()
    result = runner.invoke(
        app,
    )
    assert result.exit_code != 0
