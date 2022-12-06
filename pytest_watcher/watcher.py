import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence
from dataclasses import dataclass

from watchdog import events
from watchdog.observers import Observer

trigger_lock = threading.Lock()
trigger = None

@dataclass
class ParsedArguments:
    path: Path
    now: bool
    delay: float
    entrypoint: str
    pytest_args: Sequence[str]


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


def _run_entrypoint(entrypoint, *args) -> None:
    subprocess.run([entrypoint, *args])


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
        "--entrypoint",
        type=str,
        default=None,
        help="Use another executable to run the tests.",
    )


    namespace, pytest_args = parser.parse_known_args(args)

    return ParsedArguments(
        path=namespace.path,
        now=namespace.now,
        delay=namespace.delay,
        entrypoint=namespace.entrypoint,
        pytest_args=pytest_args
    )
  

def _run_main_loop(delay, pytest_args, entrypoint) -> None:
    global trigger

    now = datetime.now()
    if trigger and now - trigger > timedelta(seconds=delay):
        if not entrypoint:
            _run_pytest(pytest_args)
        else:
            _run_entrypoint(entrypoint, pytest_args)

        with trigger_lock:
            trigger = None

    time.sleep(delay)


def run():
    args = _parse_arguments(sys.argv[1:])
    path_to_watch = args.path
    now = args.now

    event_handler = EventHandler()

    observer = Observer()

    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    if now:
        emit_trigger()

    try:
        while True:
            _run_main_loop(args.delay, args.pytest_args, args.entrypoint)
    finally:
        observer.stop()
        observer.join()
