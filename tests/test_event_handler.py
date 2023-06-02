from typing import List
from unittest.mock import MagicMock

import pytest
from watchdog import events

from pytest_watcher import watcher


@pytest.mark.parametrize("event_type", watcher.EventHandler.EVENTS_WATCHED)
def test_event_types_watched(event_type, mock_emit_trigger: MagicMock):
    event = events.FileSystemEvent("main.py")
    event.event_type = event_type

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_called_once_with()


def test_event_types_not_watched(mock_emit_trigger: MagicMock):
    event = events.FileClosedEvent("main.py")

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_not_called()


@pytest.mark.parametrize(
    "event_class", [events.FileSystemMovedEvent, events.FileMovedEvent]
)
def test_file_moved_dest_watched(event_class, mock_emit_trigger: MagicMock):
    event = event_class("main.tmp", "main.py")

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_called_once_with()


@pytest.mark.parametrize(
    "event_class", [events.FileSystemMovedEvent, events.FileMovedEvent]
)
def test_file_moved_dest_not_watched(event_class, mock_emit_trigger: MagicMock):
    event = event_class("main.tmp", "main.temp")

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_not_called()


@pytest.mark.parametrize("path", ["main.py", "./main.py", "/home/project/main.py"])
def test_patterns_default_watched(mock_emit_trigger: MagicMock, path: str):
    event = events.FileCreatedEvent(path)

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_called_once_with()


@pytest.mark.parametrize("path", ["main.pyc", "sqlite.db", "/home/project/file.txt"])
def test_patterns_default_not_watched(mock_emit_trigger: MagicMock, path: str):
    event = events.FileCreatedEvent(path)

    handler = watcher.EventHandler()
    handler.dispatch(event)

    mock_emit_trigger.assert_not_called()


@pytest.mark.parametrize(
    ("patterns", "path"),
    [
        (["*.txt"], "file.txt"),
        (["main.pyc"], "main.pyc"),
        (["/home/path/example.txt"], "/home/path/example.txt"),
        (["*some*.txt"], "/home/path/something.txt"),
    ],
)
def test_patterns_custom_watched(
    mock_emit_trigger: MagicMock, patterns: List[str], path: str
):
    event = events.FileCreatedEvent(path)

    handler = watcher.EventHandler(patterns=patterns)
    handler.dispatch(event)

    mock_emit_trigger.assert_called_once_with()


@pytest.mark.parametrize(
    ("patterns", "path"),
    [
        (["*.txt"], "file.txtf"),
        (["*.pyi", "*.pdb"], "wrong.pdf"),
        (["/home/path/example.txt"], "/home/path/wrong.txt"),
    ],
)
def test_patterns_custom_not_watched(
    mock_emit_trigger: MagicMock, patterns: List[str], path: str
):
    event = events.FileCreatedEvent(path)

    handler = watcher.EventHandler(patterns=patterns)
    handler.dispatch(event)

    mock_emit_trigger.assert_not_called()


@pytest.mark.parametrize(
    ("ignore_patterns", "path"),
    [
        (["ignore/*.py"], "ignore/myfile.py"),
        (["ignore/**"], "ignore/main.py"),
        (["*pytest*"], "/home/project/pytest.yaml"),
    ],
)
def test_patterns_ignore_not_watched(
    mock_emit_trigger: MagicMock, ignore_patterns: List[str], path: str
):
    event = events.FileCreatedEvent(path)

    handler = watcher.EventHandler(ignore_patterns=ignore_patterns)
    handler.dispatch(event)

    mock_emit_trigger.assert_not_called()
