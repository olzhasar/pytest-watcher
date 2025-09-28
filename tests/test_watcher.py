import sys
from pathlib import Path
from unittest.mock import MagicMock, sentinel

import pytest
from freezegun import freeze_time
from pytest_mock.plugin import MockerFixture

from pytest_watcher import watcher
from pytest_watcher.config import Config
from pytest_watcher.constants import LOOP_DELAY
from pytest_watcher.terminal import Terminal
from pytest_watcher.trigger import Trigger


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_does_not_invoke_runner_without_trigger(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    config: Config,
    mock_terminal: Terminal,
    trigger: Trigger,
):
    watcher.main_loop(trigger, config, mock_terminal)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(LOOP_DELAY)


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_does_not_invoke_runner_before_delay(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    config: Config,
    mock_terminal: MagicMock,
    trigger: Trigger,
):
    trigger = Trigger(delay=5)
    trigger.emit()

    with freeze_time("2020-01-01 00:00:04"):
        watcher.main_loop(trigger, config, mock_terminal)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(LOOP_DELAY)

    assert trigger.is_active()


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_invokes_runner_after_delay(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    config: Config,
    mock_terminal: MagicMock,
):
    trigger = Trigger(delay=5)
    trigger.emit()

    config.runner = "custom"
    config.runner_args = ["foo", "bar"]

    with freeze_time("2020-01-01 00:00:06"):
        watcher.main_loop(trigger, config, mock_terminal)

    mock_subprocess_run.assert_called_once_with(["custom", "foo", "bar"], check=True)
    mock_time_sleep.assert_called_once_with(LOOP_DELAY)

    assert not trigger.is_active()


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_clear(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    config: Config,
    mock_terminal: MagicMock,
    trigger: Trigger,
):
    config.clear = True
    trigger.emit()

    with freeze_time("2020-01-01 00:00:06"):
        watcher.main_loop(trigger, config, mock_terminal)

    mock_terminal.clear.assert_called_once_with()


@freeze_time("2020-01-01 00:00:00")
def test_main_loop_no_clear(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    config: Config,
    mock_terminal: MagicMock,
    trigger: Trigger,
):
    config.clear = False
    trigger.emit()

    with freeze_time("2020-01-01 00:00:06"):
        watcher.main_loop(trigger, config, mock_terminal)

    mock_terminal.clear.assert_not_called()


def test_main_loop_keystroke(
    mock_subprocess_run: MagicMock,
    mock_time_sleep: MagicMock,
    mock_run_command: MagicMock,
    config: Config,
    trigger: Trigger,
    mock_terminal: MagicMock,
):
    trigger.emit()
    mock_terminal.capture_keystroke.return_value = sentinel.KEYSTROKE

    watcher.main_loop(trigger, config, mock_terminal)

    mock_run_command.assert_called_once_with(
        sentinel.KEYSTROKE, trigger, mock_terminal, config
    )


def assert_observer_started(mock_observer: MagicMock, expected_path: Path):
    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()

    path = mock_observer.return_value.schedule.call_args[0][1]
    assert path == expected_path


def test_run_starts_the_observer_and_main_loop(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_main_loop: MagicMock,
):
    args = ["ptw", ".", "--lf", "--nf"]
    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    assert_observer_started(mock_observer, Path("."))
    mock_main_loop.assert_called_once()


def test_run_invokes_tests_right_away_if_now_flag_is_set(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_main_loop: MagicMock,
):
    mock_emit = mocker.patch("pytest_watcher.watcher.Trigger.emit", autospec=True)

    args = ["ptw", ".", "--lf", "--nf", "--now"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    mock_emit.assert_called_once()


def test_patterns_and_ignore_patterns_are_passed_to_event_handler(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_main_loop: MagicMock,
):
    args = ["ptw", ".", "--patterns", "*.py,.env", "--ignore-patterns", "settings.py"]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    event_handler = mock_observer.return_value.schedule.call_args[0][0]

    assert event_handler.patterns == ["*.py", ".env"]
    assert event_handler.ignore_patterns == ["settings.py"]
