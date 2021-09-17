import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence, Tuple

import inotify.adapters
import inotify.constants

EVENTS_TO_WATCH = (
    inotify.constants.IN_CLOSE_WRITE
    | inotify.constants.IN_CREATE
    | inotify.constants.IN_DELETE
)


trigger_lock = threading.Lock()
trigger = None


def _triggers_run(filename: str, filepath: str) -> bool:
    """
    Check if file should trigger pytest run
    """
    return filename.endswith(".py")


def _run_pytest(args) -> None:
    subprocess.run(["pytest", *args])


def _process_event(event: Tuple[Any, Sequence[str], str, str]) -> None:
    global trigger

    (_, type_names, filepath, filename) = event

    if _triggers_run(filename, filepath):
        with trigger_lock:
            trigger = datetime.now()


def _background_watch(path_to_watch: Path) -> None:
    global trigger

    _path = str(path_to_watch.absolute())
    adapter = inotify.adapters.InotifyTree(_path, mask=EVENTS_TO_WATCH)

    for event in adapter.event_gen(yield_nones=False):
        _process_event(event)


def _parse_arguments(args: Sequence[str]) -> Tuple[Path, float, Sequence[str]]:
    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch <path> for changes in python files and run pytest
            if such change is detected.\n
            Any additional arguments will be passed to pytest directly
        """,
    )
    parser.add_argument("path", type=Path, help="path to watch")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Watching interval in seconds (default 0.5)",
    )

    namespace, pytest_args = parser.parse_known_args(args)

    return namespace.path, namespace.interval, pytest_args


def _run_main_loop(interval: float, pytest_args: Sequence[str]) -> None:
    global trigger

    now = datetime.now()
    if trigger and now - trigger > timedelta(seconds=interval):
        _run_pytest(pytest_args)

        with trigger_lock:
            trigger = None

    time.sleep(interval)


def run():
    path_to_watch, interval, pytest_args = _parse_arguments(sys.argv[1:])

    thread = threading.Thread(
        target=_background_watch, args=(path_to_watch,), daemon=True
    )
    thread.start()

    while True:
        _run_main_loop(interval, pytest_args)
