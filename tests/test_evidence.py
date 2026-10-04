import json

import pytest

from generalgamebench.evidence import Ledger, read_ledger, verify_episode
from generalgamebench.runner import run_episode


class Agent:
    def act(self, obs, timeout):
        assert set(obs) == {"protocol", "nonce", "image_png", "actions", "instructions"}
        return {"nonce": obs["nonce"], "action": 0}


def test_end_to_end_and_replay(tmp_path):
    out = tmp_path / "episode"
    result = run_episode(Agent(), "test", "coin-run", 42, out, 4)
    assert result["steps"] == 4
    assert verify_episode(out)["valid"]


def test_frame_tampering_detected(tmp_path):
    out = tmp_path / "episode"
    run_episode(Agent(), "test", "coin-run", 42, out, 4)
    (out / "frames/0000.png").write_bytes(b"forged")
    with pytest.raises(ValueError, match="digest"):
        verify_episode(out)


def test_chain_tampering_and_truncation(tmp_path):
    out = tmp_path / "episode"
    run_episode(Agent(), "test", "coin-run", 42, out, 4)
    p = out / "events.jsonl"
    lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[:-1]))
    with pytest.raises(ValueError, match="Incomplete"):
        read_ledger(p)
    row = json.loads(lines[1])
    row["payload"]["applied_action"] = 4
    lines[1] = json.dumps(row)
    p.write_text("\n".join(lines))
    with pytest.raises(ValueError, match="chain"):
        read_ledger(p)


@pytest.mark.parametrize(
    "field,value",
    [("score", 1.0), ("latencies_ms", [0.01] * 4), ("aborted", True), ("raw_score", 999)],
)
def test_rehashed_lies_still_fail_semantic_verification(tmp_path, field, value):
    out = tmp_path / "episode"
    run_episode(Agent(), "test", "coin-run", 42, out, 4)
    path = out / "events.jsonl"
    rows = read_ledger(path)
    rows[-1][field] = value
    path.unlink()
    ledger = Ledger(path)
    for row in rows:
        ledger.append(row)
    ledger.close()
    with pytest.raises(ValueError):
        verify_episode(out)


def test_timeout_zeroes_score_and_aborts(tmp_path):
    class Slow:
        def act(self, obs, timeout):
            raise TimeoutError("late")

    out = tmp_path / "episode"
    r = run_episode(Slow(), "slow", "dodge-lanes", 42, out, 4)
    assert r["score"] == 0 and r["aborted"] and not r["latency_eligible"]
    assert verify_episode(out)["valid"]


def test_exactly_100ms_is_ineligible_and_waits(tmp_path, monkeypatch):
    times = iter([0, 0, 100_000_000])
    monkeypatch.setattr("generalgamebench.runner.time.perf_counter_ns", lambda: next(times))

    class Move:
        def act(self, obs, timeout):
            return {"nonce": obs["nonce"], "action": 1}

    r = run_episode(Move(), "edge", "coin-run", 42, tmp_path / "episode", 1)
    assert r["latencies_ms"] == [100.0]
    assert not r["latency_eligible"]
    assert read_ledger(tmp_path / "episode/events.jsonl")[1]["applied_action"] == 0
