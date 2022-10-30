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
    return mocker.patch("pytest_watcher.watcher.emit_trigger", autospec=True)


@pytest.fixture
def mock_observer(mocker: MockerFixture):
    return mocker.patch("pytest_watcher.watcher.Observer", autospec=True)


@pytest.fixture
def mock_run_main_loop(mocker: MockerFixture):
    mock = mocker.patch("pytest_watcher.watcher._run_main_loop", autospec=True)
    mock.side_effect = InterruptedError
    return mock
