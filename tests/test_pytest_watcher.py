from datetime import datetime
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from pytest_watcher import __version__, watcher


def test_version():
    assert __version__ == "0.1.1"


@pytest.fixture()
def mock_subprocess_run(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.subprocess.run")


@pytest.fixture(autouse=True)
def mock_time_sleep(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.time.sleep")


@pytest.fixture(autouse=True)
def _release_trigger():
    try:
        yield
    finally:
        watcher.trigger = None


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("test.py", True),
        ("test.pyc", False),
        ("image.jpg", False),
    ],
)
def test_triggers_run(filename, expected):
    assert watcher._triggers_run(filename, "") == expected


@freeze_time("2020-01-01")
def test_process_event_trigger():
    assert watcher.trigger is None

    event = (None, [], "/home/code", "file.py")
    watcher._process_event(event)

    assert watcher.trigger == datetime(2020, 1, 1)


@freeze_time("2020-01-01")
def test_process_event_no_trigger():
    assert watcher.trigger is None

    event = (None, [], "/home/code", "README.md")
    watcher._process_event(event)

    assert watcher.trigger is None


# fmt: off

@pytest.mark.parametrize(
    ("sys_args", "path_to_watch", "interval", "pytest_args"),
    [
        (["/home/"], "/home", 0.5, []),
        (["/home/", "--lf", "--nf", "-x"], "/home", 0.5, ["--lf", "--nf", "-x"]),
        ([".", "--lf", "--nf", "-x"], ".", 0.5, ["--lf", "--nf", "-x"]),
        ([".", "--interval=0.2", "--lf", "--nf", "-x"], ".", 0.2, ["--lf", "--nf", "-x"]),
        ([".", "--lf", "--nf", "--interval=0.3", "-x"], ".", 0.3, ["--lf", "--nf", "-x"]),
    ],
)
def test_parse_arguments(sys_args, path_to_watch, interval, pytest_args):
    _path, _interval, _pytest_args = watcher._parse_arguments(sys_args)

    assert str(_path) == path_to_watch
    assert _interval == interval
    assert _pytest_args == pytest_args

# fmt: on


def test_run_main_loop_no_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = None

    watcher._run_main_loop(5, ["--lf"])

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger_fresh(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:04"):
        watcher._run_main_loop(5, ["--lf"])

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger == datetime(2020, 1, 1, 0, 0, 0)


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:06"):
        watcher._run_main_loop(5, ["--lf"])

    mock_subprocess_run.assert_called_once_with(["pytest", "--lf"])
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None
