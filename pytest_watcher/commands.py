from __future__ import annotations

import abc
import sys
from typing import Dict, Optional, Type

from .config import Config
from .terminal import Terminal
from .trigger import Trigger


class Manager:
    _registry: Dict[str, Command] = {}

    @classmethod
    def list_commands(cls):
        return cls._registry.values()

    @classmethod
    def get_command(cls, character: str) -> Optional[Command]:
        return cls._registry.get(character)

    @classmethod
    def register(cls, command: Type[Command]):
        if command.character in cls._registry:
            raise ValueError(f"Duplicate character {repr(command.character)}")

        cls._registry[command.character] = command()

    @classmethod
    def run_command(
        cls, character: str, trigger: Trigger, term: Terminal, config: Config
    ) -> None:
        command = cls.get_command(character)
        if command:
            command.run(trigger, term, config)


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
        Manager.register(cls)

    @abc.abstractmethod
    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        """
        Modify runner_args in-place if needed and return a bool indicating whether
        tests should be triggered instantly
        """


class OpenMenuCommand(Command):
    character = "w"
    caption = "w"
    description = "show menu"
    show_in_menu = False

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        term.clear()
        term.print_menu(config.runner_args)


class InvokeCommand(Command):
    character = "\n"
    caption = "Enter"
    description = "Invoke test runner"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        trigger.emit_now()


class ResetRunnerArgsCommand(Command):
    character = "r"
    caption = "r"
    description = "reset all runner args"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        config.runner_args.clear()
        trigger.emit_now()


class ChangeRunnerArgsCommand(Command):
    character = "c"
    caption = "c"
    description = "change runner args"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        term.reset()
        raw = input("\nEnter new runner args: ")
        new_args = raw.strip().split()
        config.runner_args.clear()
        config.runner_args.extend(new_args)
        trigger.emit_now()


class OnlyFailedCommand(Command):
    character = "f"
    caption = "f"
    description = "run only failed tests (--lf)"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        if "--lf" not in config.runner_args:
            config.runner_args.append("--lf")
        trigger.emit_now()


class PDBCommand(Command):
    character = "p"
    caption = "p"
    description = "drop to pdb on fail (--pdb)"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        if "--pdb" not in config.runner_args:
            config.runner_args.append("--pdb")
        trigger.emit_now()


class VerboseCommand(Command):
    character = "v"
    caption = "v"
    description = "increase verbosity (-v)"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        if "-v" not in config.runner_args:
            config.runner_args.append("-v")
        trigger.emit_now()


class EraseScreenCommand(Command):
    character = "e"
    caption = "e"
    description = "Erase terminal screen"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        term.clear()
        term.print_short_menu(config.runner_args)


class QuitCommand(Command):
    character = "q"
    caption = "q"
    description = "quit pytest-watcher"

    def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
        sys.exit(0)
