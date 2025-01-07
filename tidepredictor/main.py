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
    lon: Annotated[float, typer.Option(help="Longitude")],
    lat: Annotated[float, typer.Option(help="Latitude")],
    start: Annotated[datetime, typer.Option("--start", "-s", help="Start date")],
    end: Annotated[datetime, typer.Option("--end", "-e", help="End date")],
    interval: Annotated[
        int, typer.Option("--interval", "-i", help="Interval in minutes")
    ] = 30,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file, default is stdout"),
    ] = None,
    format: Annotated[Format, typer.Option(help="Output format")] = Format.csv,
    type: Annotated[
        PredictionType, typer.Option(help="Type of prediction, level or u,v")
    ] = PredictionType.level,
):
    """
    Predict the tides for a given location.
    """
    # TODO figure out where to store constituents
    path = (
        Path(__file__).parent.parent
        / "data/constituents_2min/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase.nc"
    )
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
