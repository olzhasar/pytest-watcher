from pathlib import Path

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
def test_path(args: list[str], path_to_watch: str):
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


@pytest.mark.parametrize("field", ["patterns", "ignore_patterns"])
@pytest.mark.parametrize(
    ("input_value", "result"),
    [
        ("", []),
        ("*.py,*.env", ["*.py", "*.env"]),
        (
            "*.py,*.env,project/pyproject.toml",
            ["*.py", "*.env", "project/pyproject.toml"],
        ),
        (
            "long-long-long-path,templates/*.py",
            ["long-long-long-path", "templates/*.py"],
        ),
    ],
)
def test_patterns(field: str, input_value: str, result: list[str]):
    args = [".", f"--{field.replace('_', '-')}", input_value]

    parsed, _ = parse_arguments(args)
    assert getattr(parsed, field) == result


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
def test_runner_args(args: list[str], runner_args: list[str]):
    _, parsed_args = parse_arguments(args)
    assert parsed_args == runner_args


def test_version(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit):
        parse_arguments(["--version"])

    captured = capsys.readouterr()
    assert captured.out == f"{VERSION}\n"
