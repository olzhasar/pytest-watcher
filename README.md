# A simple watcher for pytest

[![PyPI](https://img.shields.io/pypi/v/pytest-watcher)](https://pypi.org/project/pytest-watcher/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-watcher)](https://pypi.org/project/pytest-watcher/)
[![GitHub](https://img.shields.io/github/license/olzhasar/pytest-watcher)](https://github.com/olzhasar/pytest-watcher/blob/master/LICENSE)

## Overview

**pytest-watcher** is a tool to automatically rerun `pytest` when your code changes.
It looks for the following events:

- New `*.py` file created
- Existing `*.py` file modified
- Existing `*.py` file deleted

## What about pytest-watch?

[pytest-watch](https://github.com/joeyespo/pytest-watch) was around for a long time and was solving exactly this problem. Sadly, `pytest-watch` is not maintained anymore and not working for many users. I wrote this tool as a substitute

## Install pytest-watcher

```
pip install pytest-watcher
```

## Usage

Specify the path that you want to watch:

```
ptw .
```

or

```
ptw /home/repos/project
```

Any arguments after `<path>` will be forwarded to `pytest`:

```
ptw . -x --lf --nf
```

You can also specify an alternative runner command with `--runner` flag:

```
ptw . --runner tox
```

## Compatibility

The utility is OS independent and should be able to work with any platform.

Code is tested for Python versions 3.7+
