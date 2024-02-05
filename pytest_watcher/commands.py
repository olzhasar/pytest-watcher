from __future__ import annotations

import abc
import sys
from typing import Dict, List, Type

from . import term_utils


class Manager:
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
        Manager.register(cls)

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
        from .watcher import print_menu

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
