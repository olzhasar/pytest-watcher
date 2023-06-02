import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_mock.plugin import MockerFixture

from pytest_watcher import __version__, watcher


def test_version():
    assert __version__ == "0.2.6"


@pytest.fixture(autouse=True)
def _release_trigger():
    try:
        yield
    finally:
        watcher.trigger = None


@freeze_time("2020-01-01")
def test_emit_trigger():
    assert watcher.trigger is None

    watcher.emit_trigger()

    assert watcher.trigger == datetime(2020, 1, 1)


# fmt: off

@pytest.mark.parametrize(
    ("sys_args", "path_to_watch", "now", "delay", "runner_args", "runner", "patterns", "ignore_patterns"),
    [
        (["/home/"], "/home", False, 0.5, [], "pytest", ['*.py'], []),
        (["/home/", "--lf", "--nf", "-x"], "/home", False, 0.5, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        (["/home/", "--lf", "--now", "--nf", "-x"], "/home", True, 0.5, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        (["/home/", "--now", "--lf", "--nf", "-x"], "/home", True, 0.5, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        ([".", "--lf", "--nf", "-x"], ".", False, 0.5, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        ([".", "--delay=0.2", "--lf", "--nf", "-x"], ".", False, 0.2, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        ([".", "--lf", "--nf", "--delay=0.3", "-x"], ".", False, 0.3, ["--lf", "--nf", "-x"], "pytest", ['*.py'], []),
        (["/home/", "--runner", "tox"], "/home", False, 0.5, [], "tox", ['*.py'], []),
        (["/home/", "--runner", "'make test'"], "/home", False, 0.5, [], "'make test'", ['*.py'], []),
        (["/home/", "--runner", "make", "test"], "/home", False, 0.5, ["test"], "make", ['*.py'], []),
        (["/home/", "--patterns", "*.py,*.env"], "/home", False, 0.5, [], "pytest", ['*.py', '*.env'], []),
        (["/home/", "--patterns=*.py,*.env", "--ignore-patterns", "long-long-long-path,templates/*.py"], "/home", False, 0.5, [], "pytest", ['*.py', '*.env'], ["long-long-long-path", "templates/*.py"]),
    ],
)
def test_parse_arguments(sys_args, path_to_watch, now, delay, runner_args, runner, patterns, ignore_patterns):
    _arguments = watcher._parse_arguments(sys_args)

    assert str(_arguments.path) == path_to_watch
    assert _arguments.now == now
    assert _arguments.delay == delay
    assert _arguments.runner == runner
    assert _arguments.patterns == patterns
    assert _arguments.ignore_patterns == ignore_patterns
    assert _arguments.runner_args == runner_args

# fmt: on


def test_run_main_loop_no_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = None

    watcher._run_main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger_fresh(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:04"):
        watcher._run_main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger == datetime(2020, 1, 1, 0, 0, 0)


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:06"):
        watcher._run_main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_called_once_with(["pytest", "--lf"])
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


def test_run(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_run_main_loop: MagicMock,
):
    args = ["ptw", ".", "--lf", "--nf"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()

    mock_emit_trigger.assert_not_called()

    mock_run_main_loop.assert_called_once_with(
        runner="pytest", runner_args=["--lf", "--nf"], delay=0.5
    )


def test_run_now(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_run_main_loop: MagicMock,
):
    args = ["ptw", ".", "--lf", "--nf", "--now"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()

    mock_emit_trigger.assert_called_once_with()

    mock_run_main_loop.assert_called_once_with(
        runner="pytest", runner_args=["--lf", "--nf"], delay=0.5
    )


@pytest.mark.parametrize("runner", [("tox"), ("'make test'")])
def test_invoke_runner(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_run_main_loop: MagicMock,
    runner: str,
):
    args = ["ptw", ".", "--lf", "--nf", "--now", "--runner", runner]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()

    mock_emit_trigger.assert_called_once_with()

    mock_run_main_loop.assert_called_once_with(
        runner=runner, runner_args=["--lf", "--nf"], delay=0.5
    )
