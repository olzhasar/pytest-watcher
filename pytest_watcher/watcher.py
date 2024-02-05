from __future__ import annotations

import logging
import subprocess
import sys
import time
from typing import List

from watchdog.observers import Observer

from . import commands, term_utils
from .config import Config
from .constants import LOOP_DELAY, VERSION
from .event_handler import EventHandler
from .parse import parse_arguments
from .trigger import Trigger

logging.basicConfig(level=logging.INFO, format="[ptw] %(message)s")

trigger = Trigger()


def _invoke_runner(runner: str, args: List[str], clear: bool) -> None:
    if clear:
        term_utils.clear_screen()
    subprocess.run([runner, *args])


def main_loop(config: Config) -> None:
    if trigger.check(config.delay):
        term_utils.reset_terminal()

        try:
            _invoke_runner(config.runner, config.runner_args, clear=config.clear)

        finally:
            term_utils.enter_cbreak()

        clear_stdin()
        print_short_menu(config.runner_args)

        trigger.release()

    key = term_utils.capture_keystroke()

    should_trigger = commands.Manager.run_command(key, config.runner_args)
    if should_trigger:
        trigger.emit()

    clear_stdin()

    time.sleep(LOOP_DELAY)


@term_utils.posix_only
def print_header(runner_args):
    sys.stdout.write(f"[pytest-watcher]\nCurrent runner args: [{' '.join(runner_args)}]")


@term_utils.posix_only
def print_short_menu(runner_args: List[str]):
    print_header(runner_args)
    sys.stdout.write("\nPress w to show menu")


@term_utils.posix_only
def print_menu(runner_args: List[str]):
    print_header(runner_args)

    sys.stdout.write("\n\nControls:\n")

    for command in commands.Manager.get_commands():
        if command.show_in_menu:
            sys.stdout.write(f"> {command.caption.ljust(5)} : {command.description}\n")


@term_utils.posix_only
def clear_stdin():
    sys.stdin.flush()


def run():
    namespace, runner_args = parse_arguments(sys.argv[1:])

    config = Config.create(namespace=namespace, extra_args=runner_args)

    event_handler = EventHandler(
        trigger, patterns=config.patterns, ignore_patterns=config.ignore_patterns
    )

    observer = Observer()

    observer.schedule(event_handler, config.path, recursive=True)
    observer.start()

    sys.stdout.write(f"pytest-watcher version {VERSION}\n")
    sys.stdout.write(f"Runner command: {config.runner}\n")
    sys.stdout.write(f"Waiting for file changes in {config.path.absolute()}\n")

    term_utils.enter_cbreak()

    if config.now:
        trigger.emit()
    else:
        print_menu(config.runner_args)

    try:
        while True:
            main_loop(config)
    finally:
        observer.stop()
        observer.join()

        term_utils.reset_terminal()
