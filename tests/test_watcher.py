import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_mock.plugin import MockerFixture

from pytest_watcher import __version__, watcher
from pytest_watcher.watcher import DEFAULT_DELAY


def test_version():
    assert __version__ == "0.3.1"


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


def test_main_loop_does_not_invoke_runner_without_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = None

    watcher.main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_does_not_invoke_runner_before_delay(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:04"):
        watcher.main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger == datetime(2020, 1, 1, 0, 0, 0)


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_invokes_runner_after_delay(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:06"):
        watcher.main_loop(runner="pytest", runner_args=["--lf"], delay=5)

    mock_subprocess_run.assert_called_once_with(["pytest", "--lf"])
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


def assert_observer_started(mock_observer: MagicMock):
    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()


def test_run_starts_the_observer_and_main_loop(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_main_loop: MagicMock,
):
    args = ["ptw", ".", "--lf", "--nf"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    assert_observer_started(mock_observer)

    mock_emit_trigger.assert_not_called()

    mock_main_loop.assert_called_once_with(
        runner="pytest", runner_args=["--lf", "--nf"], delay=DEFAULT_DELAY
    )


def test_run_invokes_tests_right_away_if_now_flag_is_set(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_main_loop: MagicMock,
):
    args = ["ptw", ".", "--lf", "--nf", "--now"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    assert_observer_started(mock_observer)

    mock_emit_trigger.assert_called_once_with()

    mock_main_loop.assert_called_once_with(
        runner="pytest", runner_args=["--lf", "--nf"], delay=DEFAULT_DELAY
    )


@pytest.mark.parametrize("runner", [("tox"), ("'make test'")])
def test_custom_runner_is_passed_to_main_loop(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_main_loop: MagicMock,
    runner: str,
):
    args = ["ptw", ".", "--lf", "--nf", "--now", "--runner", runner]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    assert_observer_started(mock_observer)

    mock_emit_trigger.assert_called_once_with()

    mock_main_loop.assert_called_once_with(
        runner=runner, runner_args=["--lf", "--nf"], delay=DEFAULT_DELAY
    )
