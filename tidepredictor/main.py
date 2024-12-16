from enum import Enum
from typing import Annotated, Optional
import typer
from datetime import datetime, timedelta

from tidepredictor.adapters.protocol import PredictionType
from tidepredictor.adapters.utide import UtideAdapter

# Create a Typer application
app = typer.Typer()


class Format(str, Enum):
    csv = "csv"
    json = "json"


@app.command()
def main(
    lon: Annotated[float, typer.Option(help="Longitude")],
    lat: Annotated[float, typer.Option(help="Latitude")],
    start: Annotated[datetime, typer.Option(help="Start date")],
    end: Annotated[datetime, typer.Option(help="End date")],
    interval: Annotated[int, typer.Option(help="Interval in minutes")] = 30,
    format: Annotated[Format, typer.Option(help="Output format")] = Format.csv,
    stdout: Annotated[bool, typer.Option(help="Write to stdout")] = True,
):
    """
    Predict the tides for a given location.
    """
    # TODO configure engine
    # TODO configure elevation vs u,
    predictor = UtideAdapter(consituents=None, type=PredictionType.current)

    df = predictor.predict(
        start=start,
        end=end,
        interval=timedelta(minutes=interval),
    )

    if stdout:
        match format:
            case Format.json:
                typer.echo(df.write_json())
            case Format.csv:
                typer.echo(df.write_csv(datetime_format="%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    app()
