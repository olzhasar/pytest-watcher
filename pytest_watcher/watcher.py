from __future__ import annotations

import logging
import os
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

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    if _is_debug_mode():
        log_format = "[ptw] %(levelname)s %(threadName)s %(name)s: %(message)s"
        level = logging.DEBUG
    else:
        log_format = "[ptw] %(message)s"
        level = logging.INFO

    logging.basicConfig(level=level, format=log_format)


def main_loop(trigger: Trigger, config: Config, term: Terminal) -> None:
    if trigger.check():
        logger.debug(
            "Trigger fired; running %s %s", config.runner, " ".join(config.runner_args)
        )
        term.reset()

        if config.clear:
            term.clear()

        try:
            subprocess.run([config.runner, *config.runner_args], check=True)
        except subprocess.CalledProcessError as exc:
            logger.debug("Test run failed with exit code %s", exc.returncode)
            if config.notify_on_failure:
                term.print_bell()
        finally:
            term.enter_capturing_mode()

        term.print_short_menu(config.runner_args)

        trigger.release()

    key = term.capture_keystroke()
    if key:
        commands.Manager.run_command(key, trigger, term, config)

    time.sleep(LOOP_DELAY)


def run():
    configure_logging()
    logger.debug("Starting pytest-watcher")

    term = get_terminal()
    trigger = Trigger()

    namespace, runner_args = parse_arguments(sys.argv[1:])
    logger.debug("CLI arguments parsed: %s", namespace)
    logger.debug("Extra runner arguments: %s", runner_args)

    config = Config.create(namespace=namespace, extra_args=runner_args)

    event_handler = EventHandler(
        trigger, patterns=config.patterns, ignore_patterns=config.ignore_patterns
    )
    logger.debug(
        "Watching path %s with patterns=%s ignore_patterns=%s",
        config.path,
        config.patterns,
        config.ignore_patterns,
    )

    observer = Observer()
    observer.schedule(event_handler, config.path, recursive=True)
    observer.start()
    logger.debug("Observer started")

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
        logger.debug("Shutting down observer")
        observer.stop()
        observer.join()

        term.reset()


def _print_intro(config: Config) -> None:
    sys.stdout.write(f"pytest-watcher version {VERSION}\n")
    sys.stdout.write(f"Runner command: {config.runner}\n")
    sys.stdout.write(f"Waiting for file changes in {config.path.absolute()}\n")


def _is_debug_mode() -> bool:
    debug_value = os.getenv("PTW_DEBUG", "")

    normalized = debug_value.lower().strip()
    return normalized not in {"", "0", "false", "no", "off"}
