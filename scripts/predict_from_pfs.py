import mikeio
import polars as pl
from datetime import datetime, timedelta

import tidepredictor as tp


def predict_from_pfs(specs: mikeio.PfsDocument) -> None:
    start = datetime(specs.start_date[0], specs.start_date[1], specs.start_date[2])
    end = datetime(specs.end_date[0], specs.end_date[1], specs.end_date[2])
    timestep = timedelta(hours=specs.timestep)

    outfilename = specs.File_1.file_name

    points = pl.from_pandas(specs.File_1.to_dataframe("Point")).to_dicts()

    fp = tp.get_default_constituent_path(tp.PredictionType.level)
    repo = tp.NetCDFConstituentRepository(fp)
    predictor = tp.LevelPredictor(repo)
    dfs = {}
    for point in points:
        dfs[point["description"]] = predictor.predict(
            lon=point["x"], lat=point["y"], start=start, end=end, interval=timestep
        )
    long_df = pl.concat(
        [df.with_columns(pl.lit(key).alias("description")) for key, df in dfs.items()]
    )

    wide_df = long_df.pivot(values="level", index="time", on="description")

    mikeio.from_polars(
        wide_df, items=mikeio.ItemInfo(mikeio.EUMType.Water_Level)
    ).to_dfs(outfilename)


if __name__ == "__main__":
    filename = "scripts/test_A.pfs"
    specs = mikeio.read_pfs(filename)["TidePredictor"]

    predict_from_pfs(specs)
