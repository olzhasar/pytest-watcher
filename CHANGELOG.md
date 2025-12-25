## [v0.6.1](https://github.com/olzhasar/pytest-watcher/releases/tag/v0.6.1) - 2025-12-26

### Bugfixes

- Trigger tests in interactive mode for carriage return character

### Improved Documentation

- Add contributing guide

### Misc

- Integrate [towncrier](https://towncrier.readthedocs.io/en/stable/index.html) into the development process


## [0.6.0] - 2025-12-22

### Features
- Add notify-on-failure flag (and config option) to emit BEL symbol on test suite failure.

### Infrastructure
- Migrate from `poetry` to `uv`.
- Remove `tox`.

## [0.5.0] - 2025-12-21

### Fixes
- Merge arguments passed to the runner from config and CLI instead of overriding.

### Changes
- Drop support for Python 3.7 & 3.8.


## [0.4.3] - 2024-08-28

### Fixes

- Fix watchdog 5.x compatibility issue

## [0.4.2] - 2024-04-01

### Fixes

- Fix bug with consuming abbreviated command line arguments

## [0.4.1] - 2024-02-06

### Fixes

- Fix termios, tty import issue on Windows

## [0.4.0] - 2024-02-06

### Features

- Implement interactive mode with keyboard shortcuts for common operations

## [0.3.5] - 2024-01-28

### Features

- Add `--clear` flag to clear the terminal screen before each test run

## [0.3.4] - 2023-06-24

### Changes

- Fix `tomllib` import bug

## [0.3.3] - 2023-06-11

### Features

- Configuring `pytest-watcher` via `pyproject.toml` file

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
