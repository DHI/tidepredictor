from enum import Enum
from pathlib import Path
from typing import Annotated, Optional
import typer
from datetime import datetime, time, timedelta

from tidepredictor import PredictionType, UtideAdapter, NetCDFConstituentRepository

app = typer.Typer()


class Format(str, Enum):
    csv = "csv"
    json = "json"


midnight = datetime.combine(datetime.today(), time.min)


@app.command()
def main(
    lon: Annotated[
        float, typer.Option("--lon", "-x", help="Longitude", min=-180, max=180)
    ],
    lat: Annotated[
        float, typer.Option("--lat", "-y", help="Latitude", min=-90, max=90)
    ],
    start: Annotated[
        Optional[datetime],
        typer.Option("--start", "-s", help="Start date"),
    ] = None,
    end: Annotated[
        Optional[datetime], typer.Option("--end", "-e", help="End date")
    ] = None,
    interval: Annotated[
        int, typer.Option("--interval", "-i", help="Interval in minutes", min=1)
    ] = 30,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o", help="Output file, default is stdout", writable=True
        ),
    ] = None,
    format: Annotated[Format, typer.Option(help="Output format")] = Format.csv,
    type: Annotated[
        PredictionType, typer.Option(help="Type of prediction, level or u,v")
    ] = PredictionType.level,
    precision: Annotated[
        int,
        typer.Option(
            "--precision", "-p", help="Number of decimal places. (csv only)", min=0
        ),
    ] = 3,
) -> None:
    """
    Predict the tides for a given location.
    """
    # TODO is there a standard way to get this location? Consider platformdirs.
    DATA_DIR = Path("~/.local/share/tidepredictor")

    NAME = {PredictionType.current: "currents.nc", PredictionType.level: "level.nc"}
    path = (DATA_DIR / NAME[type]).expanduser()

    repo = NetCDFConstituentRepository(path)

    predictor = UtideAdapter(constituent_repo=repo, type=type)

    prediction_start: datetime = start or midnight
    prediction_end: datetime = end or (prediction_start + timedelta(days=1))

    df = predictor.predict(
        lon=lon,
        lat=lat,
        start=prediction_start,
        end=prediction_end,
        interval=timedelta(minutes=interval),
    )

    # use iso8601 format for datetime and make sure it uses UTC
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    if output is None:
        match format:
            case Format.json:
                typer.echo(df.write_json())
            case Format.csv:
                typer.echo(
                    df.write_csv(datetime_format=DATE_FORMAT, float_precision=precision)
                )
    else:
        format = Format(output.suffix[1:])
        if format == "json":
            df.write_json(output)
        elif format == "csv":
            df.write_csv(output, datetime_format=DATE_FORMAT, float_precision=precision)


if __name__ == "__main__":
    app()
