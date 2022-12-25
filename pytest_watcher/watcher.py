import argparse
import fnmatch
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

from watchdog import events
from watchdog.observers import Observer

trigger_lock = threading.Lock()
trigger = None


logger = logging.getLogger(__name__)


@dataclass
class ParsedArguments:
    path: Path
    now: bool
    delay: float
    runner: str
    include_filter: str
    ignore_filter: str
    runner_args: Sequence[str]


def emit_trigger():
    """
    Emits trigger to run pytest
    """

    global trigger

    with trigger_lock:
        trigger = datetime.now()


class FileFilter:
    def __init__(
        self, *, include: Optional[list[str]] = None, ignore: Optional[list[str]] = None
    ):
        self._include = include or []
        self._ignore = ignore or []

    def is_filtered(self, filepath: str) -> bool:
        """
        Check if file passes filters.
        """
        for ignore_item in self._ignore:
            ignore_result = fnmatch.fnmatch(filepath, ignore_item)
            logger.debug(
                "[filter] File: `%s` rule `%s` -> ignored: %s",
                filepath,
                ignore_item,
                ignore_result,
            )
            if ignore_result:
                return False

        for include_item in self._include:
            include_result = fnmatch.fnmatch(filepath, include_item)
            logger.debug(
                "[filter] File: `%s` rule `%s` -> included: %s",
                filepath,
                include_item,
                include_result,
            )
            if include_result:
                return True

        logger.debug("[filter] File: `%s` no rule -> ignored: True", filepath)
        return False


class EventHandler(events.FileSystemEventHandler):
    EVENTS_WATCHED = (
        events.EVENT_TYPE_CREATED,
        events.EVENT_TYPE_DELETED,
        events.EVENT_TYPE_MODIFIED,
        events.EVENT_TYPE_MOVED,
    )

    def __init__(self, file_filter: Optional[FileFilter] = None):
        self._file_filter = file_filter or FileFilter(include=["*.py"])

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if event.event_type in self.EVENTS_WATCHED:
            self.process_event(event)

    def process_event(self, event: events.FileSystemEvent) -> None:
        if self._file_filter.is_filtered(event.src_path):
            emit_trigger()
        elif isinstance(
            event, events.FileSystemMovedEvent
        ) and self._file_filter.is_filtered(event.dest_path):
            emit_trigger()


def _invoke_runner(runner: str, args: Sequence[str]) -> None:
    subprocess.run([runner, *args])


def _parse_arguments(args: Sequence[str]) -> ParsedArguments:
    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch <path> for changes in Python projects and run pytest
            if such change is detected.\n
            Any additional arguments will be passed to pytest directly
        """,
    )
    parser.add_argument("path", type=Path, help="path to watch")
    parser.add_argument("--now", action="store_true", help="Run pytest instantly")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Watcher delay in seconds (default 0.5)",
    )
    parser.add_argument(
        "--runner",
        type=str,
        default="pytest",
        help="Use another executable to run the tests.",
    )
    parser.add_argument(
        "--include-filter",
        default=["*.py"],
        type=lambda f: f.split(","),
        help="Comma-separated Unix shell-style wildcard include list (default: '*.py')",
    )
    parser.add_argument(
        "--ignore-filter",
        default=[],
        type=lambda f: f.split(","),
        help="Comma-separated Unix shell-style wildcard ignore list (default: '')",
    )

    namespace, runner_args = parser.parse_known_args(args)

    return ParsedArguments(
        path=namespace.path,
        now=namespace.now,
        delay=namespace.delay,
        runner=namespace.runner,
        include_filter=namespace.include_filter,
        ignore_filter=namespace.ignore_filter,
        runner_args=runner_args,
    )


def _run_main_loop(*, runner: str, runner_args: Sequence[str], delay: float) -> None:
    global trigger

    now = datetime.now()
    if trigger and now - trigger > timedelta(seconds=delay):
        _invoke_runner(runner, runner_args)

        with trigger_lock:
            trigger = None

    time.sleep(delay)


def run():
    args = _parse_arguments(sys.argv[1:])

    file_filter = FileFilter(include=args.include_filter, ignore=args.ignore_filter)
    event_handler = EventHandler(file_filter)

    observer = Observer()

    observer.schedule(event_handler, args.path, recursive=True)
    observer.start()

    if args.now:
        emit_trigger()

    try:
        while True:
            _run_main_loop(
                runner=args.runner, runner_args=args.runner_args, delay=args.delay
            )
    finally:
        observer.stop()
        observer.join()
