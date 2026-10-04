import copy

import pytest

from generalgamebench.ranking import summarize


def rows():
    return [
        {
            "agent": "a",
            "mode": "realtime",
            "hardware": "test",
            "version": "1",
            "max_steps": 80,
            "game": g,
            "seed": s,
            "score": v,
            "latencies_ms": [1, 2],
            "errors": [],
            "aborted": False,
        }
        for g, v in [("one", 0.2), ("two", 0.8)]
        for s in [1, 2, 3]
    ]


def test_balanced_aggregate_and_no_self_certification():
    result = summarize(rows(), ["one", "two"], [1, 2, 3])[0]
    assert result["score"] == 50
    assert result["ci95"] == pytest.approx([50, 50])
    assert result["official_rank"] is None
    assert result["latency_eligible"]


@pytest.mark.parametrize(
    "change", ["duplicate", "missing", "nan", "negative_time", "mixed_hardware"]
)
def test_invalid_or_unbalanced_data_rejected(change):
    data = rows()
    if change == "duplicate":
        data.append(copy.deepcopy(data[0]))
    if change == "missing":
        data.pop()
    if change == "nan":
        data[0]["score"] = float("nan")
    if change == "negative_time":
        data[0]["latencies_ms"] = [-1]
    if change == "mixed_hardware":
        data[0]["hardware"] = "other"
    with pytest.raises(ValueError):
        summarize(data, ["one", "two"], [1, 2, 3])


def test_strict_deadline_and_single_seed_uncertainty():
    data = rows()[:1]
    data[0]["latencies_ms"] = [100]
    result = summarize(data, ["one"], [1])[0]
    assert not result["latency_eligible"] and result["misses"] == 1 and result["ci95"] is None


@pytest.mark.parametrize("change", ["model", "revision", "prompt", "engine"])
def test_mixed_identity_or_engine_rejected(change):
    data = rows()
    if change == "model":
        data[0]["model"] = "different-model"
    elif change == "engine":
        data[0]["game_metadata"] = {"engine_version": "different"}
    else:
        key = "revision" if change == "revision" else "prompt_version"
        data[0]["provider_metadata"] = {key: "different"}
    with pytest.raises(ValueError):
        summarize(data, ["one", "two"], [1, 2, 3])
