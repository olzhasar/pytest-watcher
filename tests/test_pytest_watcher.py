import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_mock.plugin import MockerFixture
from watchdog import events

from pytest_watcher import __version__, watcher


def test_version():
    assert __version__ == "0.2.5"


@pytest.fixture(autouse=True)
def _release_trigger():
    try:
        yield
    finally:
        watcher.trigger = None


@pytest.mark.parametrize(
    ("filepath", "expected"),
    [
        ("test.py", True),
        ("./test.py", True),
        ("/home/project/test.py", True),
        ("test.pyc", False),
        ("image.jpg", False),
    ],
)
def test_is_path_watched(filepath, expected):
    assert watcher._is_path_watched(filepath) == expected


class TestEventHandler:
    @pytest.mark.parametrize("event_type", watcher.EventHandler.EVENTS_WATCHED)
    def test_src_watched(self, event_type, mock_emit_trigger: MagicMock):
        event = events.FileSystemEvent("main.py")
        event.event_type = event_type

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_called_once_with()

    @pytest.mark.parametrize(
        "event_class", [events.FileSystemMovedEvent, events.FileMovedEvent]
    )
    def test_file_moved_dest_watched(self, event_class, mock_emit_trigger: MagicMock):
        event = event_class("main.tmp", "main.py")

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_called_once_with()

    @pytest.mark.parametrize(
        "event_class", [events.FileSystemMovedEvent, events.FileMovedEvent]
    )
    def test_file_moved_dest_not_watched(
        self, event_class, mock_emit_trigger: MagicMock
    ):
        event = event_class("main.tmp", "main.temp")

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_not_called()

    def test_src_not_watched(self, mock_emit_trigger: MagicMock):
        event = events.FileCreatedEvent("main.pyc")

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_not_called()

    def test_wrong_event_type(self, mock_emit_trigger: MagicMock):
        event = events.FileClosedEvent("main.py")

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_not_called()


@freeze_time("2020-01-01")
def test_emit_trigger():
    assert watcher.trigger is None

    watcher.emit_trigger()

    assert watcher.trigger == datetime(2020, 1, 1)


# fmt: off

@pytest.mark.parametrize(
    ("sys_args", "path_to_watch", "now", "delay", "pytest_args", "entrypoint"),
    [
        (["/home/"], "/home", False, 0.5, [], "pytest"),
        (["/home/", "--lf", "--nf", "-x"], "/home", False, 0.5, ["--lf", "--nf", "-x"], "pytest"),
        (["/home/", "--lf", "--now", "--nf", "-x"], "/home", True, 0.5, ["--lf", "--nf", "-x"], "pytest"),
        (["/home/", "--now", "--lf", "--nf", "-x"], "/home", True, 0.5, ["--lf", "--nf", "-x"], "pytest"),
        ([".", "--lf", "--nf", "-x"], ".", False, 0.5, ["--lf", "--nf", "-x"], "pytest"),
        ([".", "--delay=0.2", "--lf", "--nf", "-x"], ".", False, 0.2, ["--lf", "--nf", "-x"], "pytest"),
        ([".", "--lf", "--nf", "--delay=0.3", "-x"], ".", False, 0.3, ["--lf", "--nf", "-x"], "pytest"),
        (["/home/", "--entrypoint", "tox"], "/home", False, 0.5, [], "tox"),
        (["/home/", "--entrypoint", "'make test'"], "/home", False, 0.5, [], "'make test'"),
        (["/home/", "--entrypoint", "make", "test"], "/home", False, 0.5, ["test"], "make"),
    ],
)
def test_parse_arguments(sys_args, path_to_watch, now, delay, pytest_args, entrypoint):
    _arguments = watcher._parse_arguments(sys_args)

    assert str(_arguments.path) == path_to_watch
    assert _arguments.now == now
    assert _arguments.delay == delay
    assert _arguments.entrypoint == entrypoint
    assert _arguments.pytest_args == pytest_args

# fmt: on


def test_run_main_loop_no_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = None

    watcher._run_main_loop(5, ["--lf"], None)

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger is None


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger_fresh(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:04"):
        watcher._run_main_loop(5, ["--lf"], "pytest")

    mock_subprocess_run.assert_not_called()
    mock_time_sleep.assert_called_once_with(5)

    assert watcher.trigger == datetime(2020, 1, 1, 0, 0, 0)


@freeze_time("2020-01-01 00:00:00")
def test_run_main_loop_trigger(
    mock_subprocess_run: MagicMock, mock_time_sleep: MagicMock
):
    watcher.trigger = datetime(2020, 1, 1, 0, 0, 0)

    with freeze_time("2020-01-01 00:00:06"):
        watcher._run_main_loop(5, ["--lf"], "pytest")

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

    mock_run_main_loop.assert_called_once_with(0.5, ["--lf", "--nf"], "pytest")


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

    mock_run_main_loop.assert_called_once_with(0.5, ["--lf", "--nf"], "pytest")


@pytest.mark.parametrize("entrypoint", [("tox"), ("'make test'")])
def test_run_entrypoint(
    mocker: MockerFixture,
    mock_observer: MagicMock,
    mock_emit_trigger: MagicMock,
    mock_run_main_loop: MagicMock,
    entrypoint: str,
):
    args = ["ptw", ".", "--lf", "--nf", "--now", "--entrypoint", entrypoint]

    mocker.patch.object(sys, "argv", args)

    with pytest.raises(InterruptedError):
        watcher.run()

    mock_observer.assert_called_once_with()
    observer_instance = mock_observer.return_value
    observer_instance.schedule.assert_called_once()
    observer_instance.start.assert_called_once()

    mock_emit_trigger.assert_called_once_with()

    mock_run_main_loop.assert_called_once_with(0.5, ["--lf", "--nf"], entrypoint)
