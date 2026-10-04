"""Worker cleanup must not signal a process group the child no longer owns."""

import signal
from types import SimpleNamespace

from generalgamebench.worker_game import WorkerGame


def test_changed_worker_group_only_signals_the_exact_child(monkeypatch):
    sent = []
    worker = WorkerGame.__new__(WorkerGame)
    worker.process = SimpleNamespace(pid=1234, poll=lambda: None, send_signal=sent.append)
    monkeypatch.setattr("generalgamebench.worker_game.os.getpgid", lambda _: 5678)

    def reject_group(*args):
        raise AssertionError("Must not signal another process group")

    monkeypatch.setattr("generalgamebench.worker_game.os.killpg", reject_group)
    worker._signal_worker(signal.SIGTERM)
    assert sent == [signal.SIGTERM]
