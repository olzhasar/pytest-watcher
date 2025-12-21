from pathlib import Path
from typing import List

import pytest

from pytest_watcher.watcher import VERSION, parse_arguments


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
    parsed, _ = parse_arguments(args)

    assert parsed.path == path_to_watch


def test_delay():
    parsed, _ = parse_arguments([".", "--delay", "999"])
    assert parsed.delay == 999


def test_now():
    parsed, _ = parse_arguments([".", "--now"])
    assert parsed.now is True


def test_runner():
    parsed, _ = parse_arguments([".", "--runner", "tox"])
    assert parsed.runner == "tox"


def test_clear():
    parsed, _ = parse_arguments([".", "--clear"])
    assert parsed.clear is True


def test_notify_on_failure():
    parsed, _ = parse_arguments([".", "--notify-on-failure"])
    assert parsed.notify_on_failure is True


@pytest.mark.parametrize(
    ("args", "patterns"),
    [
        ([".", "--patterns", "*.py,*.env"], ["*.py", "*.env"]),
        (
            [".", "--patterns", "*.py,*.env,project/pyproject.toml"],
            ["*.py", "*.env", "project/pyproject.toml"],
        ),
    ],
)
def test_patterns(args: List[str], patterns: List[str]):
    parsed, _ = parse_arguments(args)
    assert parsed.patterns == patterns


@pytest.mark.parametrize(
    ("args", "ignore_patterns"),
    [
        (
            [".", "--ignore-patterns", "long-long-long-path,templates/*.py"],
            ["long-long-long-path", "templates/*.py"],
        ),
    ],
)
def test_ignore_patterns(args: List[str], ignore_patterns: List[str]):
    parsed, _ = parse_arguments(args)
    assert parsed.ignore_patterns == ignore_patterns


@pytest.mark.parametrize(
    ("args", "runner_args"),
    [
        (["."], []),
        ([".", "--lf", "--nf", "-vv"], ["--lf", "--nf", "-vv"]),
        ([".", "--runner", "tox", "--lf", "--nf", "-vv"], ["--lf", "--nf", "-vv"]),
        ([".", "--lf", "--nf", "-vv", "--runner", "tox"], ["--lf", "--nf", "-vv"]),
        (
            [".", "--ignore", "tests/test_watcher.py"],
            ["--ignore", "tests/test_watcher.py"],
        ),
    ],
)
def test_runner_args(args: List[str], runner_args: List[str]):
    _, parsed_args = parse_arguments(args)
    assert parsed_args == runner_args


def test_version(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit):
        parse_arguments(["--version"])

    captured = capsys.readouterr()
    assert captured.out == f"{VERSION}\n"
