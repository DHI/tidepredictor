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

    fp = tp.get_default_constituent_path(tp.PredictionType.current)
    repo = tp.NetCDFConstituentRepository(fp)
    predictor = tp.CurrentPredictor(repo)
    dfs_list = [
        predictor.predict_depth_averaged(
            lon=p["x"], lat=p["y"], start=start, end=end, interval=timestep
        ).with_columns(pl.lit(p["description"]).alias("description"))
        for p in points
    ]
    long_df = pl.concat(dfs_list)

    wide_df = long_df.pivot(values=["u", "v"], index="time", on="description")

    items = {}

    stations = [p["description"] for p in points]

    cols = [f"{item}_{stn}" for stn in stations for item in ["u", "v"]]

    cols.insert(0, "time")

    reordered = wide_df[cols]

    for col in reordered.columns:
        if col.startswith("u"):
            items[col] = mikeio.ItemInfo(col, mikeio.EUMType.u_velocity_component)
        elif col.startswith("v"):
            items[col] = mikeio.ItemInfo(col, mikeio.EUMType.v_velocity_component)

    mikeio.from_polars(reordered, items=items).to_dfs(outfilename)


if __name__ == "__main__":
    filename = "scripts/test_A.pfs"
    specs = mikeio.read_pfs(filename)["TidePredictor"]

    predict_from_pfs(specs)
