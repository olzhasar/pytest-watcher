import abc
import logging
import os
import select
import sys
from typing import List, Optional

try:
    import termios
    import tty
except ImportError:
    pass


class Terminal(abc.ABC):
    def clear(self):
        pass

    def print(self, msg: str) -> None:
        pass

    def print_header(self, runner_args: List[str]):
        self.print(f"[pytest-watcher]\nCurrent runner args: [{' '.join(runner_args)}]")

    def print_short_menu(self, runner_args: List[str]) -> None:
        self.print_header(runner_args)
        self.print("\nPress w to show menu")

    def print_menu(self, runner_args: List[str]) -> None:
        from . import commands

        self.print_header(runner_args)
        self.print("\n\nControls:\n")

        for command in commands.Manager.list_commands():
            if command.show_in_menu:
                self.print(f"> {command.caption.ljust(5)} : {command.description}\n")

    def enter_capturing_mode(self) -> None:
        pass

    def capture_keystroke(self) -> Optional[str]:
        pass

    def reset(self) -> None:
        pass


class PosixTerminal(Terminal):
    def __init__(self) -> None:
        self._initial_state = termios.tcgetattr(sys.stdin.fileno())

    def print(self, msg: str) -> None:
        sys.stdout.write(msg)

    def clear(self) -> None:
        sys.stdout.write("\033c")
        sys.stdout.flush()

    def enter_capturing_mode(self) -> None:
        sys.stdin.flush()
        tty.setcbreak(sys.stdin.fileno())

    def capture_keystroke(self) -> Optional[str]:
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    def reset(self) -> None:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._initial_state)


class DummyTerminal(Terminal):
    pass


def get_terminal() -> Terminal:
    if os.name == "posix":
        try:
            return PosixTerminal()
        except Exception:
            logging.exception(
                "Unable to initialize terminal state\nInteractive mode is disabled"
            )
    return DummyTerminal()
