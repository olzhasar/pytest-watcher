import argparse
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence

from watchdog import events
from watchdog.observers import Observer
from watchdog.utils.patterns import match_any_paths

DEFAULT_DELAY = 0.2

trigger_lock = threading.Lock()
trigger = None


logger = logging.getLogger(__name__)


@dataclass
class ParsedArguments:
    path: Path
    now: bool
    delay: float
    runner: str
    patterns: str
    ignore_patterns: str
    runner_args: Sequence[str]


def emit_trigger():
    """
    Emits trigger to run pytest
    """

    global trigger

    with trigger_lock:
        trigger = datetime.now()


class EventHandler:
    EVENTS_WATCHED = {
        events.EVENT_TYPE_CREATED,
        events.EVENT_TYPE_DELETED,
        events.EVENT_TYPE_MODIFIED,
        events.EVENT_TYPE_MOVED,
    }

    def __init__(self, patterns: List[str] = None, ignore_patterns: List[str] = None):
        self._patterns = patterns or ["*.py"]
        self._ignore_patterns = ignore_patterns or []

    @property
    def patterns(self) -> List[str]:
        return self._patterns

    @property
    def ignore_patterns(self) -> List[str]:
        return self._ignore_patterns

    def _is_event_watched(self, event: events.FileSystemEvent) -> bool:
        if event.event_type not in self.EVENTS_WATCHED:
            return False

        paths = [event.src_path]
        if hasattr(event, "dest_path"):
            # For file moved type events we are also interested in the destination
            paths.append(event.dest_path)

        return match_any_paths(paths, self.patterns, self.ignore_patterns)

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if self._is_event_watched(event):
            emit_trigger()
            logger.debug(f"TRIGGERED event: {event.event_type} src: {event.src_path}")
        else:
            logger.debug(f"IGNORED event: {event.event_type} src: {event.src_path}")


def _invoke_runner(runner: str, args: Sequence[str]) -> None:
    subprocess.run([runner, *args])


def _parse_patterns(arg: str):
    return arg.split(",")


def _parse_arguments(args: Sequence[str]) -> ParsedArguments:
    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch <path> for file changes in Python projects and run pytest
            if such change is detected.\n
            Any additional arguments will be passed to pytest directly
        """,
    )
    parser.add_argument("path", type=Path, help="path to watch")
    parser.add_argument("--now", action="store_true", help="Run pytest instantly")
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Watcher delay in seconds (default DEFAULT_DELAY)",
    )
    parser.add_argument(
        "--runner",
        type=str,
        default="pytest",
        help="Use another executable to run the tests.",
    )
    parser.add_argument(
        "--patterns",
        default=["*.py"],
        type=_parse_patterns,
        help="Comma-separated Unix shell-style wildcard patterns list (default: '*.py')",
    )
    parser.add_argument(
        "--ignore-patterns",
        default=[],
        type=_parse_patterns,
        help="Comma-separated Unix shell-style wildcard ignore patterns list (default: '')",
    )

    namespace, runner_args = parser.parse_known_args(args)

    return ParsedArguments(
        path=namespace.path,
        now=namespace.now,
        delay=namespace.delay,
        runner=namespace.runner,
        patterns=namespace.patterns,
        ignore_patterns=namespace.ignore_patterns,
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

    event_handler = EventHandler(
        patterns=args.patterns, ignore_patterns=args.ignore_patterns
    )

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
