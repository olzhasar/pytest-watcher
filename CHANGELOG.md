## [0.3.2] - 2023-06-08

### Features

- Add `--version` cli command

### Changes

- Fix main loop delay

## [0.3.1] - 2023-06-03

### Features

- Print information about current version, runner command and watched path on startup
- Log all triggered events

### Changes

- Fix typo in `delay` argument help message

## [0.3.0] - 2023-06-03

### Features

- Allow specifying custom file patterns and ignoring specific patterns via corresponding flags (`--patterns`, `--ignore-patterns`). Special thanks to @[@aptakhin](https://github.com/aptakhin) for the contribution

### Changes

- Reduce default invocation delay form 0.5 to 0.2

## [0.2.6] - 2022-12-11

### Features

- New `--runner` flag for specifying alternative runner command (e.g. `tox`, `make`, etc.)

### Changes

- Drop support for Python 3.6

## [0.2.5] - 2022-10-30

### Features

- New `--now` flag for triggering `pytest` instantly
- Support for Python 3.11

## [0.2.4] - 2022-10-30

### Features

- Support for file move events from not watched path to a watched one (e.g. renaming `test.txt` to `test.py`)

## [0.2.3] - 2021-12-31

### Fixes

- Fix python classifiers on Pypi

## [0.2.2] - 2021-12-31

### Features

- Support for Python 3.10

## [0.2.1] - 2021-09-18

### Features

- Added short command version `ptw` alongside `pytest-watcher`

## [0.2.0] - 2021-09-18

### Changes

- Migrate from `inotify` to `watchdog` for events monitoring

## [0.1.1] - 2021-09-18

### Initial release
