import argparse
import logging
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import inotify.adapters
import inotify.constants

logger = logging.getLogger("main")
handler = logging.FileHandler("watcher.log")

logger.setLevel(logging.INFO)
logger.addHandler(handler)


EVENTS_TO_WATCH = (
    inotify.constants.IN_CLOSE_WRITE
    | inotify.constants.IN_CREATE
    | inotify.constants.IN_DELETE
)


def _is_ignored_by_git(filepath: str):
    result = subprocess.run(["git", "check-ignore", filepath])
    return result.returncode == 1


def _run_pytest(args):
    subprocess.run(["pytest", *args])


trigger_lock = threading.Lock()
trigger = None


def _background_watch(path_to_watch: Path):
    i = inotify.adapters.InotifyTree(path_to_watch, mask=EVENTS_TO_WATCH)

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event

        if filename.endswith(".py"):
            global trigger

            with trigger_lock:
                trigger = datetime.now()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)

    known_args, pytest_args = parser.parse_known_args()
    path_to_watch = str(known_args.path)

    thread = threading.Thread(target=_background_watch, args=(path_to_watch,))
    thread.start()

    global trigger

    while True:
        now = datetime.now()
        if trigger and now - trigger > timedelta(milliseconds=500):
            _run_pytest(pytest_args)

            with trigger_lock:
                trigger = None

        time.sleep(0.5)
