import marimo

__generated_with = "0.10.12"
app = marimo.App(width="medium")


@app.cell
def _():
    from tidepredictor.data import ConstituentRepository, LevelConstituent

    class FakeConstituentRepository(ConstituentRepository):
        def get_level_constituents(self, lon, lat):
            return {
                "MM": LevelConstituent(amplitude=0.009100, phase=353.7),
                "MF": LevelConstituent(amplitude=0.01800, phase=0.00010),
                "Q1": LevelConstituent(amplitude=0.005000, phase=126.9),
                "O1": LevelConstituent(amplitude=0.01610, phase=299.7),
                "P1": LevelConstituent(amplitude=0.03100, phase=345.1),
                "K1": LevelConstituent(amplitude=0.1064, phase=350.8),
                "N2": LevelConstituent(amplitude=0.09610, phase=102.0),
                "M2": LevelConstituent(amplitude=0.4350, phase=105.6),
                "S2": LevelConstituent(amplitude=0.1543, phase=132.9),
                "K2": LevelConstituent(amplitude=0.04190, phase=130.2),
                "MN4": LevelConstituent(amplitude=0.002000, phase=270.0),
                "M4": LevelConstituent(amplitude=0.005700, phase=315.0),
                "MS4": LevelConstituent(amplitude=0.001000, phase=0.00060),
            }

        def get_current_constituents(self, lon, lat):
            return NotImplementedError()

    return (
        ConstituentRepository,
        FakeConstituentRepository,
        LevelConstituent,
    )


@app.cell
def _(FakeConstituentRepository):
    from datetime import datetime, timedelta
    from tidepredictor import UtideAdapter, PredictionType

    repo = FakeConstituentRepository()

    predictor = UtideAdapter(
        constituent_repo=repo,
        type=PredictionType.level,
    )

    df = predictor.predict(
        lon=-118,
        lat=34,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 15),
        interval=timedelta(hours=1),
    )
    return (
        PredictionType,
        UtideAdapter,
        datetime,
        df,
        predictor,
        repo,
        timedelta,
    )


@app.cell
def _(df):
    import plotly.express as px

    px.line(df, x="time", y="level")
    return (px,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
