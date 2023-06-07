import argparse
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from watchdog import events
from watchdog.observers import Observer
from watchdog.utils.patterns import match_any_paths

VERSION = "0.3.2"
DEFAULT_DELAY = 0.2
LOOP_DELAY = 0.1

trigger_lock = threading.Lock()
trigger = None


logging.basicConfig(level=logging.INFO, format="[ptw] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Config:
    path: Path = Path.cwd()
    now: bool = False
    delay: float = DEFAULT_DELAY
    runner: str = "pytest"
    patterns: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=list)
    runner_args: List[str] = field(default_factory=list)

    @property
    def namespace_fields(self):
        return ("now", "delay", "runner", "patterns", "ignore_patterns")

    def update_from_command_line(
        self, namespace: argparse.Namespace, runner_args: Optional[List[str]]
    ):
        self.path = namespace.path

        for f in self.namespace_fields:
            val = getattr(namespace, f)
            if val:
                setattr(self, f, val)

        if runner_args:
            self.runner_args = runner_args


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

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
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
            logger.info(f"{event.src_path} {event.event_type}")
        else:
            logger.debug(f"IGNORED event: {event.event_type} src: {event.src_path}")


def _invoke_runner(runner: str, args: Sequence[str]) -> None:
    subprocess.run([runner, *args])


def parse_arguments(args: Sequence[str]) -> Tuple[argparse.Namespace, List[str]]:
    def _parse_patterns(arg: str):
        return arg.split(",")

    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch the <path> for file changes and trigger the test runner (pytest).\n
            Additional arguments are passed directly to the test runner.
        """,
    )
    parser.add_argument("path", type=Path, help="The path to watch for file changes.")
    parser.add_argument(
        "--now", action="store_true", help="Trigger the test run immediately"
    )
    parser.add_argument(
        "--delay",
        type=float,
        required=False,
        help=f"The delay (in seconds) before triggering the test run (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "--runner",
        type=str,
        required=False,
        help="Specify the executable for running the tests (default: pytest)",
    )
    parser.add_argument(
        "--patterns",
        type=_parse_patterns,
        required=False,
        help="File patterns to watch, specified as comma-separated Unix-style patterns (default: '*.py')",
    )
    parser.add_argument(
        "--ignore-patterns",
        type=_parse_patterns,
        required=False,
        help="File patterns to ignore, specified as comma-separated Unix-style patterns (default: '')",
    )
    parser.add_argument("--version", action="version", version=VERSION)

    return parser.parse_known_args(args)


def main_loop(*, runner: str, runner_args: Sequence[str], delay: float) -> None:
    global trigger

    now = datetime.now()
    if trigger and now - trigger > timedelta(seconds=delay):
        _invoke_runner(runner, runner_args)

        with trigger_lock:
            trigger = None

    time.sleep(LOOP_DELAY)


def run():
    config = Config()

    namespace, runner_args = parse_arguments(sys.argv[1:])
    config.update_from_command_line(namespace, runner_args)

    event_handler = EventHandler(
        patterns=config.patterns, ignore_patterns=config.ignore_patterns
    )

    observer = Observer()

    observer.schedule(event_handler, config.path, recursive=True)
    observer.start()

    sys.stdout.write(f"pytest-watcher version {VERSION}\n")
    sys.stdout.write(f"Runner command: {config.runner} {' '.join(config.runner_args)}\n")
    sys.stdout.write(f"Waiting for file changes in {config.path.absolute()}\n")

    if config.now:
        emit_trigger()

    try:
        while True:
            main_loop(
                runner=config.runner, runner_args=config.runner_args, delay=config.delay
            )
    finally:
        observer.stop()
        observer.join()
