from enum import Enum
from pathlib import Path
from typing import Annotated, Optional
import typer
from datetime import datetime, timedelta

from tidepredictor.adapters.protocol import PredictionType
from tidepredictor.utide import UtideAdapter

app = typer.Typer()


class Format(str, Enum):
    csv = "csv"
    json = "json"


@app.command()
def main(
    lon: Annotated[
        float, typer.Option("--lon", "-x", help="Longitude", min=-180, max=180)
    ],
    lat: Annotated[
        float, typer.Option("--lat", "-y", help="Latitude", min=-90, max=90)
    ],
    start: Annotated[datetime, typer.Option("--start", "-s", help="Start date")],
    end: Annotated[datetime, typer.Option("--end", "-e", help="End date")],
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
):
    """
    Predict the tides for a given location.
    """
    # TODO is there a standard way to get this location?
    DATA_DIR = Path("~/.local/share/tidepredictor")
    path = (DATA_DIR / "elevation.nc").expanduser()
    predictor = UtideAdapter(consituents=path, type=type)

    df = predictor.predict(
        lon=lon,
        lat=lat,
        start=start,
        end=end,
        interval=timedelta(minutes=interval),
    )

    if output is None:
        match format:
            case Format.json:
                typer.echo(df.write_json())
            case Format.csv:
                typer.echo(df.write_csv(datetime_format="%Y-%m-%d %H:%M:%S"))
    else:
        format = Format(output.suffix[1:])
        if format == "json":
            df.write_json(output)
        elif format == "csv":
            df.write_csv(output, datetime_format="%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    app()
