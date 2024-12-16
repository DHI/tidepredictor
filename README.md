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

