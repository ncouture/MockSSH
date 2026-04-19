import hy  # noqa: F401
import pytest

from twisted.internet import reactor
from threading import Thread
import time


def pytest_collect_file(file_path, parent):
    if file_path.suffix == ".hy" and file_path.name.startswith("test_"):
        return pytest.Module.from_parent(parent, path=file_path)


@pytest.fixture(scope="session", autouse=True)
def twisted_reactor():
    """
    Ensures the Twisted reactor is running in a background thread for the duration of the test session.
    """
    if not reactor.running:
        t = Thread(target=reactor.run, args=(False,))
        t.daemon = True
        t.start()
        # Give the reactor a moment to start
        time.sleep(0.5)

    yield reactor

    # We don't necessarily need to stop it here as the process will exit,
    # but let's be clean. Note: once stopped, it can't be restarted.
    if reactor.running:
        reactor.callFromThread(reactor.stop)
