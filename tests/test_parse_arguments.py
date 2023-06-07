from pathlib import Path
from typing import List

import pytest

from pytest_watcher.watcher import DEFAULT_DELAY, parse_arguments


@pytest.mark.parametrize(
    ("args", "path_to_watch"),
    [
        (["."], Path(".")),
        (["/project/"], Path("/project")),
        (["../project/"], Path("../project")),
        (["/project/", "/tests/"], Path("/project")),
    ],
)
def test_path(args: List[str], path_to_watch: str):
    parsed = parse_arguments(args)

    assert parsed.path == path_to_watch


def test_delay_default():
    parsed = parse_arguments(["."])
    assert parsed.delay == DEFAULT_DELAY


def test_delay():
    parsed = parse_arguments([".", "--delay", "999"])
    assert parsed.delay == 999


def test_now():
    parsed = parse_arguments([".", "--now"])
    assert parsed.now is True


def test_now_default():
    parsed = parse_arguments(["."])
    assert parsed.now is False


def test_runner():
    parsed = parse_arguments([".", "--runner", "tox"])
    assert parsed.runner == "tox"


@pytest.mark.parametrize(
    ("args", "patterns"),
    [
        (["."], ["*.py"]),
        ([".", "--patterns", "*.py,*.env"], ["*.py", "*.env"]),
        (
            [".", "--patterns", "*.py,*.env,project/pyproject.toml"],
            ["*.py", "*.env", "project/pyproject.toml"],
        ),
    ],
)
def test_patterns(args: List[str], patterns: List[str]):
    parsed = parse_arguments(args)
    assert parsed.patterns == patterns


@pytest.mark.parametrize(
    ("args", "ignore_patterns"),
    [
        (["."], []),
        (
            [".", "--ignore-patterns", "long-long-long-path,templates/*.py"],
            ["long-long-long-path", "templates/*.py"],
        ),
    ],
)
def test_ignore_patterns(args: List[str], ignore_patterns: List[str]):
    parsed = parse_arguments(args)
    assert parsed.ignore_patterns == ignore_patterns


@pytest.mark.parametrize(
    ("args", "runner_args"),
    [
        (["."], []),
        ([".", "--lf", "--nf", "-vv"], ["--lf", "--nf", "-vv"]),
        ([".", "--runner", "tox", "--lf", "--nf", "-vv"], ["--lf", "--nf", "-vv"]),
        ([".", "--lf", "--nf", "-vv", "--runner", "tox"], ["--lf", "--nf", "-vv"]),
    ],
)
def test_runner_args(args: List[str], runner_args: List[str]):
    parsed = parse_arguments(args)
    assert parsed.runner_args == runner_args
