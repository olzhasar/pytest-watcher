from argparse import Namespace
from pathlib import Path

import pytest

from pytest_watcher.watcher import Config


@pytest.fixture
def config():
    return Config()


class TestUpdateFromCommandLine:
    def test_values_are_updated(self, config: Config):
        namespace = Namespace(
            path="custom",
            now=True,
            delay=20,
            runner="tox",
            patterns=["*.py", ".env"],
            ignore_patterns=["main.py"],
        )
        runner_args = ["--lf", "--nf"]

        config.update_from_command_line(namespace, runner_args)

        for f in config.namespace_fields:
            assert getattr(config, f) == getattr(namespace, f)

        assert config.runner_args == runner_args

    def test_none_values_are_not_updated(self, config: Config):
        namespace = Namespace(
            path="custom",
            now=None,
            delay=None,
            runner=None,
            patterns=None,
            ignore_patterns=None,
        )
        runner_args = None

        config.update_from_command_line(namespace, runner_args)

        for f in config.namespace_fields:
            assert getattr(config, f) is not None

        assert config.runner_args == []


class TestUpdateFromConfigDict:
    def test_values_are_updated(self, tmp_path: Path, config: Config):
        data = {
            "now": True,
            "delay": 20,
            "runner": "tox",
            "patterns": ["*.py", ".env"],
            "ignore_patterns": ["main.py"],
        }

        config.update_from_mapping(data)

        for key, value in data.items():
            assert getattr(config, key) == value

    def test_path_is_not_updated(self, tmp_path: Path, config: Config):
        data = {
            "path": "custom",
        }

        config.update_from_mapping(data)

        assert config.path != data["path"]
