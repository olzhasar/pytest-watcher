import functools
import os
import select
import sys
import termios
import tty
from typing import List, Optional

if os.name == "posix":

    def clear_screen():
        sys.stdout.write("\033c")
        sys.stdout.flush()

else:

    def clear_screen():
        pass


def posix_only(f):
    if os.name == "posix":
        return f

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        pass

    return wrapper


@posix_only
def enter_cbbreak():
    tty.setcbreak(sys.stdin.fileno())


@posix_only
def reset_terminal():
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))


@posix_only
def capture_keystroke() -> Optional[str]:
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


@posix_only
def print_menu(runner_args: List[str]):
    sys.stdout.write(f"\nCurrent runner args: [{' '.join(runner_args)}]\n")

    sys.stdout.write("\nControls:\n")

    def _print_control(key: str, desc: str):
        sys.stdout.write(f"> {key} : {desc}\n")

    _print_control("r", "run tests")
    _print_control("q", "quit pytest-watcher")

    sys.stdin.flush()
