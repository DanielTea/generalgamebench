"""A policy update must keep measured scores and refuse incomplete evidence."""

import importlib.util
from pathlib import Path

import pytest

from generalgamebench.ranking import summarize

spec = importlib.util.spec_from_file_location(
    "update_latency_policy",
    Path(__file__).parents[1] / "scripts/update_latency_policy.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    episodes = [
        {
            "agent": "a",
            "game": "one",
            "seed": 1,
            "mode": "realtime",
            "version": "0.4.0",
            "hardware": "test",
            "max_steps": 20,
            "score": 0.3,
            "latencies_ms": [10] * 19 + [1000],
            "errors": [],
            "aborted": False,
        }
    ]
    row = summarize(episodes, ["one"], [1])[0]
    row.update(latency_eligible=False, misses=1)
    row.pop("latency_policy")
    return {"exhibition": [row], "official": []}, episodes


def test_policy_update_preserves_scores_and_source():
    source, episodes = fixture()
    result, changes = module.update(source, episodes)
    assert not source["exhibition"][0]["latency_eligible"]
    assert result["exhibition"][0]["latency_eligible"]
    assert result["exhibition"][0]["score"] == 30
    assert result["official"] == []
    assert result["exhibition"][0]["official_rank"] is None
    assert len(changes) == 1


@pytest.mark.parametrize("change", ["missing", "duplicate", "score", "timing"])
def test_policy_update_rejects_changed_or_missing_evidence(change):
    source, episodes = fixture()
    if change == "missing":
        episodes.clear()
    elif change == "duplicate":
        episodes.append(episodes[0])
    elif change == "score":
        episodes[0]["score"] = 1
    else:
        episodes[0]["latencies_ms"] = [1] * 20
    with pytest.raises(ValueError):
        module.update(source, episodes)
