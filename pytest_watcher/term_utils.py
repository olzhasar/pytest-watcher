import functools
import os
import select
import sys
import termios
import tty
from typing import Optional

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
def capture_keystroke() -> Optional[str]:
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


if os.name == "posix":
    try:
        state = termios.tcgetattr(sys.stdin.fileno())
    except Exception:  # TODO: This is mainly for tests, refactor later

        def reset_terminal():
            pass

    else:

        def reset_terminal():
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, state)

else:

    def reset_terminal():
        pass
