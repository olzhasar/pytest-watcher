from argparse import Namespace

import pytest

from pytest_watcher.watcher import Config


@pytest.fixture
def config():
    return Config()


def test_values_are_being_updated_from_command_line(config: Config):
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


def test_none_values_are_not_updated(config: Config):
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
