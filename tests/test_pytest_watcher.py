from datetime import datetime
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from pytest_watcher import __version__, watcher
from watchdog import events


def test_version():
    assert __version__ == "0.2.1"


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
    @pytest.fixture
    def mock_emit_trigger(self, mocker: MockerFixture):
        return mocker.patch("pytest_watcher.watcher.emit_trigger")

    @pytest.mark.parametrize("event_type", watcher.EventHandler.EVENTS_WATCHED)
    def test_ok(self, event_type, mock_emit_trigger: MagicMock):
        event = events.FileSystemEvent("main.py")
        event.event_type = event_type

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_called_once_with()

    def test_wrong_event_type(self, mock_emit_trigger: MagicMock):
        event = events.FileClosedEvent("main.py")

        handler = watcher.EventHandler()
        handler.dispatch(event)

        mock_emit_trigger.assert_not_called()

    def test_file_not_watched(self, mock_emit_trigger: MagicMock):
        event = events.FileCreatedEvent("main.pyc")

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
    ("sys_args", "path_to_watch", "delay", "pytest_args"),
    [
        (["/home/"], "/home", 0.5, []),
        (["/home/", "--lf", "--nf", "-x"], "/home", 0.5, ["--lf", "--nf", "-x"]),
        ([".", "--lf", "--nf", "-x"], ".", 0.5, ["--lf", "--nf", "-x"]),
        ([".", "--delay=0.2", "--lf", "--nf", "-x"], ".", 0.2, ["--lf", "--nf", "-x"]),
        ([".", "--lf", "--nf", "--delay=0.3", "-x"], ".", 0.3, ["--lf", "--nf", "-x"]),
    ],
)
def test_parse_arguments(sys_args, path_to_watch, delay, pytest_args):
    _path, _delay, _pytest_args = watcher._parse_arguments(sys_args)

    assert str(_path) == path_to_watch
    assert _delay == delay
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
