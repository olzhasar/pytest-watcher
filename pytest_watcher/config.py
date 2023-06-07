from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .constants import DEFAULT_DELAY


@dataclass
class Config:
    path: Path = Path.cwd()
    now: bool = False
    delay: float = DEFAULT_DELAY
    runner: str = "pytest"
    patterns: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=list)
    runner_args: List[str] = field(default_factory=list)

    @property
    def namespace_fields(self):
        return ("now", "delay", "runner", "patterns", "ignore_patterns")

    def update_from_command_line(
        self, namespace: Namespace, runner_args: Optional[List[str]]
    ):
        self.path = namespace.path

        for f in self.namespace_fields:
            val = getattr(namespace, f)
            if val:
                setattr(self, f, val)

        if runner_args:
            self.runner_args = runner_args
