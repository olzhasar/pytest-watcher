import argparse
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

from watchdog import events
from watchdog.observers import Observer

trigger_lock = threading.Lock()
trigger = None


@dataclass
class ParsedArguments:
    path: Path
    now: bool
    delay: float
    runner: str
    runner_args: Sequence[str]


def emit_trigger():
    """
    Emits trigger to run pytest
    """

    global trigger

    with trigger_lock:
        trigger = datetime.now()


def _is_path_watched(filepath: str) -> bool:
    """
    Check if file should trigger pytest run
    """
    return filepath.endswith(".py")


class EventHandler(events.FileSystemEventHandler):
    EVENTS_WATCHED = (
        events.EVENT_TYPE_CREATED,
        events.EVENT_TYPE_DELETED,
        events.EVENT_TYPE_MODIFIED,
        events.EVENT_TYPE_MOVED,
    )

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if event.event_type in self.EVENTS_WATCHED:
            self.process_event(event)

    def process_event(self, event: events.FileSystemEvent) -> None:
        if _is_path_watched(event.src_path):
            emit_trigger()
        elif isinstance(event, events.FileSystemMovedEvent) and _is_path_watched(
            event.dest_path
        ):
            emit_trigger()


def _invoke_runner(runner: str, args: Sequence[str]) -> None:
    subprocess.run([runner, *args])


def _parse_arguments(args: Sequence[str]) -> ParsedArguments:
    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch <path> for changes in python files and run pytest
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

    namespace, runner_args = parser.parse_known_args(args)

    return ParsedArguments(
        path=namespace.path,
        now=namespace.now,
        delay=namespace.delay,
        runner=namespace.runner,
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

    event_handler = EventHandler()

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
