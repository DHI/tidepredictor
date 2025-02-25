import mikeio
import polars as pl
from datetime import datetime, timedelta

import tidepredictor as tp


def predict_from_pfs(specs: mikeio.PfsDocument) -> None:
    start = datetime(*specs.start_date)
    end = datetime(*specs.end_date)
    timestep = timedelta(hours=specs.timestep)

    outfilename = specs.File_1.file_name

    points = pl.from_pandas(specs.File_1.to_dataframe("Point")).to_dicts()

    fp = tp.get_default_constituent_path(tp.PredictionType.level)
    repo = tp.NetCDFConstituentRepository(fp)
    predictor = tp.LevelPredictor(repo)
    dfs_list = [
        predictor.predict(
            lon=p["x"], lat=p["y"], start=start, end=end, interval=timestep
        ).with_columns(pl.lit(p["description"]).alias("description"))
        for p in points
    ]
    long_df = pl.concat(dfs_list)

    wide_df = long_df.pivot(values="level", index="time", on="description")

    mikeio.from_polars(
        wide_df, items=mikeio.ItemInfo(mikeio.EUMType.Water_Level)
    ).to_dfs(outfilename)


if __name__ == "__main__":
    filename = "scripts/test_A.pfs"
    specs = mikeio.read_pfs(filename)["TidePredictor"]

    predict_from_pfs(specs)
