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


logger = logging.getLogger(__name__)


def run_test_suite(runner: str, runner_args: list[str]) -> subprocess.Popen:
    return subprocess.Popen([runner, *runner_args])


def poll_test_suite(
    *, process: subprocess.Popen, interrupt=False
) -> subprocess.Popen | None:
    ret = process.poll()
    if ret is not None:
        return None

    if interrupt:
        logger.info(f"Interrupting process: {process}")
        process.terminate()

        logger.info(f"Waiting for process: {process}")
        ret = process.wait()
        logger.info(f"Process exited with code: {ret}")

        return None

    return process


def main_loop(
    trigger: Trigger,
    config: Config,
    term: Terminal,
    current_process: subprocess.Popen | None = None,
) -> subprocess.Popen | None:
    new_process: subprocess.Popen | None = None

    if trigger.check():
        term.reset()

        if config.clear:
            term.clear()

        if current_process:
            current_process = poll_test_suite(
                process=current_process, interrupt=config.interrupt
            )

        new_process = run_test_suite(config.runner, config.runner_args)
        if config.notify_on_failure:
            term.print_bell()

        term.enter_capturing_mode()

        term.print_short_menu(config.runner_args)

        trigger.release()

    key = term.capture_keystroke()
    if key:
        commands.Manager.run_command(key, trigger, term, config)

    time.sleep(LOOP_DELAY)

    return new_process or current_process


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
        current_process = None

        while True:
            current_process = main_loop(trigger, config, term, current_process)
    finally:
        observer.stop()
        observer.join()

        term.reset()


def _print_intro(config: Config) -> None:
    sys.stdout.write(f"pytest-watcher version {VERSION}\n")
    sys.stdout.write(f"Runner command: {config.runner}\n")
    sys.stdout.write(f"Waiting for file changes in {config.path.absolute()}\n")
