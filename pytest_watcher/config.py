from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Optional

from .constants import DEFAULT_DELAY

try:
    import tomllib
except ImportError:
    import tomli as tomllib


CONFIG_SECTION_NAME = "pytest-watcher"
CLI_FIELDS = {"now", "clear", "delay", "runner", "patterns", "ignore_patterns"}
CONFIG_FIELDS = CLI_FIELDS | {"runner_args"}


@dataclass
class Config:
    path: Path
    now: bool = False
    clear: bool = False
    delay: float = DEFAULT_DELAY
    runner: str = "pytest"
    runner_args: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls, namespace: Namespace, extra_args: Optional[List[str]] = None
    ) -> "Config":
        instance = cls(path=namespace.path)

        config_path = find_config(namespace.path)
        if config_path:
            parsed = parse_config(config_path)
            instance._update_from_mapping(parsed)

        instance._update_from_namespace(namespace, extra_args or [])
        return instance

    def _update_from_mapping(self, data: Mapping):
        for key, val in data.items():
            setattr(self, key, val)

    def _update_from_namespace(
        self, namespace: Namespace, runner_args: Optional[List[str]]
    ):
        self.path = namespace.path

        for f in CLI_FIELDS:
            val = getattr(namespace, f)
            if val:
                setattr(self, f, val)

        if runner_args:
            self.runner_args = runner_args


def find_config(cwd: Path) -> Optional[Path]:
    filename = "pyproject.toml"

    for path in (cwd, *cwd.parents):
        config_path = path.joinpath(filename)

        if config_path.exists():
            return config_path

    return None


def parse_config(path: Path) -> Mapping:
    with open(path, "rb") as f:
        try:
            data = tomllib.load(f)
        except Exception as exc:
            raise SystemExit(f"Error parsing pyproject.toml\n{exc}")

    try:
        data = data["tool"][CONFIG_SECTION_NAME]
    except KeyError:
        return {}

    for key in data.keys():
        if key not in CONFIG_FIELDS:
            raise SystemExit(
                f"Error parsing pyproject.toml.\nUnrecognized option: {key}"
            )
    return data
