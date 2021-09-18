# A simple watcher for pytest

![PyPI](https://img.shields.io/pypi/v/pytest-watcher)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-watcher)
![GitHub](https://img.shields.io/github/license/olzhasar/pytest-watcher)

## Overview

**pytest-watcher** is a tool to automatically rerun `pytest` when your code changes.
It looks for `*.py` files changes in a directory that you specify. `pytest` will be automatically invoked when you create new files and modify or delete existing.

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

Any additional arguments will be forwarded to `pytest`:
```
ptw . -x --lf --nf
```

## Compatibility

The utility is OS independent and should work on any platform.

Code is tested for Python versions 3.6+
