from pytest_watcher import commands
from pytest_watcher.config import Config
from pytest_watcher.terminal import Terminal
from pytest_watcher.trigger import Trigger


def test_run_command(trigger: Trigger, config: Config, mock_terminal: Terminal):
    class DummyCommand(commands.Command):
        character = "0"
        caption = "0"
        description = "test"
        show_in_menu = False

        def __init__(self):
            self.invoked = False

        def run(self, trigger: Trigger, term: Terminal, config: Config) -> None:
            self.invoked = True

    command = commands.Manager.get_command("0")

    assert isinstance(command, DummyCommand)
    assert command.invoked is False

    commands.Manager.run_command("0", trigger, mock_terminal, config)

    assert command.invoked is True

    commands.Manager._registry.pop(DummyCommand.character)
