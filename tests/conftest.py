from pathlib import Path

import pytest
from pytest_mock import MockerFixture


@pytest.fixture()
def mock_subprocess_run(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.subprocess.run", autospec=True)


@pytest.fixture(autouse=True)
def mock_time_sleep(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.time.sleep", autospec=True)


@pytest.fixture
def mock_emit_trigger(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.trigger.emit", autospec=True)


@pytest.fixture
def mock_observer(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.Observer", autospec=True)


@pytest.fixture
def mock_main_loop(mocker: MockerFixture):
    mock = mocker.patch("pytest_watcher.watcher.main_loop", autospec=True)
    mock.side_effect = InterruptedError
    return mock


@pytest.fixture(scope="session")
def tmp_path() -> Path:
    return Path("tests/tmp")


@pytest.fixture(scope="session", autouse=True)
def create_tmp_dir(tmp_path: Path):
    tmp_path.mkdir(exist_ok=True)


@pytest.fixture
def pyproject_toml_path(tmp_path: Path):
    path = tmp_path.joinpath("pyproject.toml")
    path.touch()

    yield path

    path.unlink()
