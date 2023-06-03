# A simple watcher for pytest

[![PyPI](https://img.shields.io/pypi/v/pytest-watcher)](https://pypi.org/project/pytest-watcher/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-watcher)](https://pypi.org/project/pytest-watcher/)
[![GitHub](https://img.shields.io/github/license/olzhasar/pytest-watcher)](https://github.com/olzhasar/pytest-watcher/blob/master/LICENSE)

## Overview

**pytest-watcher** is a tool to automatically rerun tests (using `pytest` by default) whenever your code changes.

Works on Unix (Linux, MacOS, BSD) and Windows.

## Table of Contents

- [Motivation](#motivation)
- [File Events](#file-events)
- [Installation](#installation)
- [Usage](#usage)
- [Using a different test runner](#using-a-different-test-runner)
- [Watching different patterns](#watching-different-patterns)
- [Delay](#delay)
- [Compatibility](#compatibility)
- [License](#license)

## Motivation

### Why not general tools (e.g. `watchmedo`, `entr`)?

- Easy to use and remember
- Works for most python projects out of the box
- Minimum dependencies (`watchdog` is the only one)
- Handles post-processing properly (see [delay](#delay))

### What about pytest-watch?

[pytest-watch](https://github.com/joeyespo/pytest-watch) has been around for a long time and used to address exactly this problem. Unfortunately, pytest-watch is no longer maintained and does not work for many users. To provide a substitute, I developed this tool.

## File events

By default `pytest-watcher` looks for the following events:

- New `*.py` file created
- Existing `*.py` file modified
- Existing `*.py` file deleted
- A `*.py` file moved either from or to the watched path

You can specify alternative file patterns to watch. See [Watching different patterns](#watching-different-patterns)

## Installation

```sh
pip install pytest-watcher
```

## Usage

Specify the path that you want to monitor:

```sh
ptw .
```

or

```sh
ptw /home/repos/project
```

Any arguments after `<path>` will be passed to the test runner (which is `pytest` by default). For example:

```sh
ptw . -x --lf --nf
```

will call `pytest` with the following arguments:

```sh
pytest -x --lf --nf
```

## Using a different test runner

You can specify an alternative test runner using the `--runner` flag:

```sh
ptw . --runner tox
```

## Watching different patterns

You can use the `--patterns` flag to specify file patterns that you want to monitor. It accepts a list of Unix-style patterns separated by a comma. The default value is "\*.py".

Example:

```sh
ptw . --patterns '*.py,pyproject.toml'
```

You can also **ignore** certain patterns using the `--ignore-patterns` flag:

```sh
ptw . --ignore-patterns 'settings.py,db.py'
```

## Delay

`pytest-watcher` uses a short delay (0.2 seconds by default) before triggering the actual test run. The main motivation for this is post-processors that can run after you save the file (e.g., `black` plugin in your IDE). This ensures that tests will be run with the latest version of your code.

You can control the actual delay value with the `--delay` flag:

`ptw . --delay 0.2`

To disable the delay altogether, you can provide zero as a value:

`ptw . --delay 0`

## Compatibility

The code is tested for Python versions 3.7+

## License

This project is licensed under the [MIT License](LICENSE).
