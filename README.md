# A simple watcher for pytest

![PyPI](https://img.shields.io/pypi/v/pytest-watcher)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-watcher)
![GitHub](https://img.shields.io/github/license/olzhasar/pytest-watcher)

## Overview

**pytest-watcher** is a tool to automatically rerun `pytest` whenever any `.py` file changes in your project.
It uses Linux [inotify API](https://man7.org/linux/man-pages/man7/inotify.7.html) for event monitoring via python [inotify library](https://pypi.org/project/inotify/).

`pytest` invocation will be triggered when you change, delete or create new python files in watched directory.

## Install pytest-watcher

```
pip install pytest-watcher
```

## Usage

Specify the path that you want to watch:

```
pytest-watcher .
```
or 
```
pytest-watcher /home/repos/project
```

Any additional arguments will be forwarded to `pytest`:
```
pytest-watcher . -x --lf --nf
```

## Compatibility

This utility should be compatible with any Linux-based Operating System.
Because it relies on `inotify` API, using on MacOS or Windows is not currently possible.

Library code is tested for Python versions 3.6+
