from __future__ import annotations

import logging
import subprocess
import sys
import time

from watchdog.observers import Observer

from . import commands
from .config import Config
from .constants import LOOP_DELAY, VERSION
from .event_handler import EventHandler
from .parse import parse_arguments
from .terminal import Terminal, get_terminal
from .trigger import Trigger

logging.basicConfig(level=logging.INFO, format="[ptw] %(message)s")


def main_loop(trigger: Trigger, config: Config, term: Terminal) -> None:
    if trigger.check():
        term.reset()

        if config.clear:
            term.clear()

        try:
            subprocess.run([config.runner, *config.runner_args])

        finally:
            term.enter_capturing_mode()

        term.print_short_menu(config.runner_args)

        trigger.release()

    key = term.capture_keystroke()
    if key:
        commands.Manager.run_command(key, trigger, term, config)

    time.sleep(LOOP_DELAY)


def run():
    term = get_terminal()
    trigger = Trigger()

    namespace, runner_args = parse_arguments(sys.argv[1:])

    config = Config.create(namespace=namespace, extra_args=runner_args)

    event_handler = EventHandler(
        trigger, patterns=config.patterns, ignore_patterns=config.ignore_patterns
    )

    observer = Observer()
    observer.schedule(event_handler, config.path, recursive=True)
    observer.start()

    _print_intro(config)

    term.enter_capturing_mode()

    if config.now:
        trigger.emit()
    else:
        term.print_menu(config.runner_args)

    try:
        while True:
            main_loop(trigger, config, term)
    finally:
        observer.stop()
        observer.join()

        term.reset()


def _print_intro(config: Config) -> None:
    sys.stdout.write(f"pytest-watcher version {VERSION}\n")
    sys.stdout.write(f"Runner command: {config.runner}\n")
    sys.stdout.write(f"Waiting for file changes in {config.path.absolute()}\n")
