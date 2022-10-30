import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence, Tuple

from watchdog import events
from watchdog.observers import Observer

trigger_lock = threading.Lock()
trigger = None


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


def _run_pytest(args) -> None:
    subprocess.run(["pytest", *args])


def _parse_arguments(args: Sequence[str]) -> Tuple[Path, bool, float, Sequence[str]]:
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

    namespace, pytest_args = parser.parse_known_args(args)

    return namespace.path, namespace.now, namespace.delay, pytest_args


def _run_main_loop(delay: float, pytest_args: Sequence[str]) -> None:
    global trigger

    now = datetime.now()
    if trigger and now - trigger > timedelta(seconds=delay):
        _run_pytest(pytest_args)

        with trigger_lock:
            trigger = None

    time.sleep(delay)


def run():
    path_to_watch, now, delay, pytest_args = _parse_arguments(sys.argv[1:])

    event_handler = EventHandler()

    observer = Observer()

    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    if now:
        emit_trigger()

    try:
        while True:
            _run_main_loop(delay, pytest_args)
    finally:
        observer.stop()
        observer.join()
