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
    "change", ["duplicate", "missing", "nan", "negative_time", "mixed_hardware", "timeout"]
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
    if change == "timeout":
        data[0]["response_timeout_seconds"] = 3
    with pytest.raises(ValueError):
        summarize(data, ["one", "two"], [1, 2, 3])


@pytest.mark.parametrize("latency,eligible", [(100, True), (199.999999, True), (200, False)])
def test_p95_boundary_and_single_seed_uncertainty(latency, eligible):
    data = rows()[:1]
    data[0]["latencies_ms"] = [latency]
    result = summarize(data, ["one"], [1])[0]
    assert result["latency_eligible"] is eligible
    assert result["misses"] == int(latency >= 200)
    assert result["ci95"] is None


def test_suite_p95_pools_samples_and_keeps_failed_episodes():
    data = rows()[:2]
    data[0]["latencies_ms"] = [20] * 99
    data[1].update(latencies_ms=[1000], errors=["TimeoutError"], aborted=True, score=0)
    result = summarize(data, ["one"], [1, 2])[0]
    assert result["p95_ms"] == 20
    assert result["max_ms"] == 1000
    assert result["misses"] == 1
    assert result["latency_eligible"]
    assert result["score"] == 10
    assert result["errors"] == result["aborted_episodes"] == 1
    assert result["official_rank"] is None
    assert result["latency_policy"]["quantile_method"] == "linear"


def test_p95_uses_linear_interpolation():
    data = rows()[:1]
    data[0]["latencies_ms"] = [10] * 19 + [1000]
    result = summarize(data, ["one"], [1])[0]
    assert result["p95_ms"] == pytest.approx(59.5)
    assert result["latency_eligible"]


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
