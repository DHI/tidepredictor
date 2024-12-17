# tidepredictor: Predict tides with Python

![](logo.png)

## Dependencies

* [Utide](https://github.com/wesleybowman/UTide)

Predict the tides for a given location.

**Usage**:

```console
$ tidepredictor [OPTIONS]
```

**Options**:

* `--lon FLOAT`: Longitude  [required]
* `--lat FLOAT`: Latitude  [required]
* `-s, --start [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]`: Start date  [required]
* `-e, --end [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]`: End date  [required]
* `-i, --interval INTEGER`: Interval in minutes  [default: 30]
* `-o, --output PATH`: Output file, default is stdout
* `--format [csv|json]`: Output format  [default: csv]
* `--type [level|current]`: Type of prediction, level or u,v  [default: level]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

## Tidal constituents

<details>
<summary>Code</summary>
```python
import polars as pl
from utide._ut_constants import ut_constants

used_consts = "Q1 MF P1 K1 MM O1 M2 S2 M4 MN4 MS4 N2 K2".split()

consts = (
    pl.DataFrame(ut_constants["const"])
    .select("name", pl.col("freq").alias("freq_cph"))
    .filter(pl.col("name").is_in(used_consts))
    .with_columns((1 / pl.col("freq_cph")).alias("period_h"))
    .sort("period_h", descending=True)
)

with pl.Config(set_float_precision=4):
    print(consts.head(10))
```
</details>


┌──────┬──────────┬──────────┐
│ name ┆ freq_cph ┆ period_h │
│ ---  ┆ ---      ┆ ---      │
│ str  ┆ f64      ┆ f64      │
╞══════╪══════════╪══════════╡
│ MM   ┆ 0.0015   ┆ 661.3093 │
│ MF   ┆ 0.0031   ┆ 327.8590 │
│ Q1   ┆ 0.0372   ┆ 26.8684  │
│ O1   ┆ 0.0387   ┆ 25.8193  │
│ P1   ┆ 0.0416   ┆ 24.0659  │
│ K1   ┆ 0.0418   ┆ 23.9345  │
│ N2   ┆ 0.0790   ┆ 12.6583  │
│ M2   ┆ 0.0805   ┆ 12.4206  │
│ S2   ┆ 0.0833   ┆ 12.0000  │
│ K2   ┆ 0.0836   ┆ 11.9672  │
└──────┴──────────┴──────────┘