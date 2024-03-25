import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

from .constants import DEFAULT_DELAY, VERSION


def parse_arguments(args: Sequence[str]) -> Tuple[argparse.Namespace, List[str]]:
    def _parse_patterns(arg: str):
        return arg.split(",")

    parser = argparse.ArgumentParser(
        prog="pytest_watcher",
        description="""
            Watch the <path> for file changes and trigger the test runner (pytest).\n
            Additional arguments are passed directly to the test runner.
        """,
        allow_abbrev=False,
    )
    parser.add_argument("path", type=Path, help="The path to watch for file changes.")
    parser.add_argument(
        "--now", action="store_true", help="Trigger the test run immediately"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the terminal screen before test run",
    )
    parser.add_argument(
        "--delay",
        type=float,
        required=False,
        help="The delay (in seconds) before triggering "
        f"the test run (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "--runner",
        type=str,
        required=False,
        help="Specify the executable for running the tests (default: pytest)",
    )
    parser.add_argument(
        "--patterns",
        type=_parse_patterns,
        required=False,
        help="File patterns to watch, specified as comma-separated "
        "Unix-style patterns (default: '*.py')",
    )
    parser.add_argument(
        "--ignore-patterns",
        type=_parse_patterns,
        required=False,
        help="File patterns to ignore, specified as comma-separated "
        "Unix-style patterns (default: '')",
    )
    parser.add_argument("--version", action="version", version=VERSION)

    return parser.parse_known_args(args)
