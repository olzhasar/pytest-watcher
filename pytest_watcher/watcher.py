import argparse
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import inotify.adapters
import inotify.constants

EVENTS_TO_WATCH = (
    inotify.constants.IN_CLOSE_WRITE
    | inotify.constants.IN_CREATE
    | inotify.constants.IN_DELETE
)


trigger_lock = threading.Lock()
trigger = None


def _is_ignored_by_git(filepath: str):
    """Check if file is ignored by git"""
    result = subprocess.run(["git", "check-ignore", filepath])
    return result.returncode == 1


def _triggers_run(filename: str, filepath: str):
    """
    Check if file should trigger pytest run
    """
    return filename.endswith(".py")


def _run_pytest(args):
    subprocess.run(["pytest", *args])


def _background_watch(path_to_watch: Path):
    global trigger
    adapter = inotify.adapters.InotifyTree(path_to_watch, mask=EVENTS_TO_WATCH)

    for event in adapter.event_gen(yield_nones=False):
        (_, type_names, filepath, filename) = event

        if _triggers_run(filename, filepath):

            with trigger_lock:
                trigger = datetime.now()


def run():
    parser = argparse.ArgumentParser(
        usage="pytest_watcher <path> <pytest_args>",
        description="Watch directory for changes in python files and run pytest if change detected",
    )
    parser.add_argument("path", type=Path, help="path to watch")

    known_args, pytest_args = parser.parse_known_args()
    path_to_watch = str(known_args.path)

    thread = threading.Thread(
        target=_background_watch, args=(path_to_watch,), daemon=True
    )
    thread.start()

    global trigger

    while True:
        now = datetime.now()
        if trigger and now - trigger > timedelta(milliseconds=500):
            _run_pytest(pytest_args)

            with trigger_lock:
                trigger = None

        time.sleep(0.5)
