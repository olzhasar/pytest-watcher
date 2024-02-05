from __future__ import annotations

import abc
import logging
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Type

from watchdog import events
from watchdog.observers import Observer
from watchdog.utils.patterns import match_any_paths

from . import term_utils
from .config import Config
from .constants import LOOP_DELAY, VERSION
from .parse import parse_arguments

logging.basicConfig(level=logging.INFO, format="[ptw] %(message)s")
logger = logging.getLogger(__name__)


class Trigger:
    value: float
    lock: threading.Lock

    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0

    def emit(self):
        with self.lock:
            self.value = time.time()

    def is_empty(self):
        return self.value == 0

    def release(self):
        with self.lock:
            self.value = 0

    def check(self, delay: float):
        now = time.time()
        return self.value > 0 and now - self.value > delay


trigger = Trigger()


class EventHandler:
    EVENTS_WATCHED = {
        events.EVENT_TYPE_CREATED,
        events.EVENT_TYPE_DELETED,
        events.EVENT_TYPE_MODIFIED,
        events.EVENT_TYPE_MOVED,
    }

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
        self._patterns = patterns or ["*.py"]
        self._ignore_patterns = ignore_patterns or []

    @property
    def patterns(self) -> List[str]:
        return self._patterns

    @property
    def ignore_patterns(self) -> List[str]:
        return self._ignore_patterns

    def _is_event_watched(self, event: events.FileSystemEvent) -> bool:
        if event.event_type not in self.EVENTS_WATCHED:
            return False

        paths = [event.src_path]
        if hasattr(event, "dest_path"):
            # For file moved type events we are also interested in the destination
            paths.append(event.dest_path)

        return match_any_paths(paths, self.patterns, self.ignore_patterns)

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if self._is_event_watched(event):
            trigger.emit()
            logger.info(f"{event.src_path} {event.event_type}")
        else:
            logger.debug(f"IGNORED event: {event.event_type} src: {event.src_path}")


def _invoke_runner(runner: str, args: List[str], clear: bool) -> None:
    if clear:
        term_utils.clear_screen()
    subprocess.run([runner, *args])


class CommandManager:
    _registry: Dict[str, Command] = {}

    @classmethod
    def get_commands(cls):
        return cls._registry.values()

    @classmethod
    def register(cls, command: Type[Command]):
        if command.character in cls._registry:
            raise ValueError(f"Duplicate character {repr(command.character)}")

        cls._registry[command.character] = command()

    @classmethod
    def run_command(cls, character: str, runner_args: List[str]) -> bool:
        command = cls._registry.get(character)
        if command:
            return command.run(runner_args)
        return False


class Command(abc.ABC):
    character: str
    caption: str
    description: str
    show_in_menu: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        for field in ("character", "caption", "description"):
            if not hasattr(cls, field):
                raise NotImplementedError(f"{cls.__name__}: {field} not specified")

        super().__init_subclass__(**kwargs)
        CommandManager.register(cls)

    @abc.abstractmethod
    def run(self, runner_args: list[str]) -> bool:
        """
        Modify runner_args in-place if needed and return a bool indicating whether
        tests should be triggered instantly
        """

    def _add_to_runner_args(self, runner_args: List[str], val: str):
        if val not in runner_args:
            runner_args.append(val)


class OpenMenuCommand(Command):
    character = "w"
    caption = "w"
    description = "show menu"
    show_in_menu = False

    def run(self, runner_args: list[str]):
        term_utils.clear_screen()
        print_menu(runner_args)
        return False


class InvokeCommand(Command):
    character = "\r"
    caption = "Enter"
    description = ""

    def run(self, runner_args: list[str]) -> bool:
        return True


class ResetRunnerArgsCommand(Command):
    character = "r"
    caption = "r"
    description = "reset all runner args"

    def run(self, runner_args: list[str]):
        runner_args.clear()
        return True


class OnlyFailedCommand(Command):
    character = "l"
    caption = "l"
    description = "run only failed tests (--lf)"

    def run(self, runner_args: list[str]):
        self._add_to_runner_args(runner_args, "--lf")
        return True


class PDBCommand(Command):
    character = "p"
    caption = "p"
    description = "drop to pdb on fail (--pdb)"

    def run(self, runner_args: list[str]):
        self._add_to_runner_args(runner_args, "--pdb")
        return True


class VerboseCommand(Command):
    character = "v"
    caption = "v"
    description = "increase verbosity (-v)"

    def run(self, runner_args: list[str]):
        self._add_to_runner_args(runner_args, "-v")
        return True


class QuitCommand(Command):
    character = "q"
    caption = "q"
    description = "quit pytest-watcher"

    def run(self, runner_args: list[str]):
        sys.exit(0)


def main_loop(*, runner: str, runner_args: List[str], delay: float, clear: bool) -> None:
    if trigger.check(delay):
        term_utils.reset_terminal()

        try:
            _invoke_runner(runner, runner_args, clear=clear)

        finally:
            term_utils.enter_cbreak()

        clear_stdin()
        print_short_menu(runner_args)

        trigger.release()

    key = term_utils.capture_keystroke()

    should_trigger = CommandManager.run_command(key, runner_args)
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

    for command in CommandManager.get_commands():
        if command.show_in_menu:
            sys.stdout.write(f"> {command.caption.ljust(5)} : {command.description}\n")


@term_utils.posix_only
def clear_stdin():
    sys.stdin.flush()


def run():
    namespace, runner_args = parse_arguments(sys.argv[1:])

    config = Config.create(namespace=namespace, extra_args=runner_args)

    event_handler = EventHandler(
        patterns=config.patterns, ignore_patterns=config.ignore_patterns
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
            main_loop(
                runner=config.runner,
                runner_args=config.runner_args,
                delay=config.delay,
                clear=config.clear,
            )
    finally:
        observer.stop()
        observer.join()

        term_utils.reset_terminal()
