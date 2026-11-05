import copy
import importlib.util
from pathlib import Path

import pytest

from generalgamebench.weighted_score import (
    add_weighted_score,
    policy,
    rank_rows,
    speed_score,
    weighted_score,
)


def example():
    return {
        "agent": "model",
        "score": 80,
        "p95_ms": 1000,
        "per_game": {"maze": 60},
        "ci95": [70, 90],
        "latency_eligible": False,
        "misses": 5,
        "latency_policy": {"id": "suite-p95-200-v1", "limit_ms": 200},
        "trust": "local-unattested",
        "errors": 2,
    }


def test_quality_and_latency_each_have_the_expected_direction():
    assert weighted_score(80, 100) > weighted_score(60, 100)
    assert weighted_score(80, 100) > weighted_score(80, 1000) > weighted_score(80, 10000)
    assert weighted_score(80, 10000) > weighted_score(20, 100)
    assert weighted_score(0, 0) == weighted_score(0, 10000) == 0
    assert weighted_score(100, 0) == 100


def test_fixed_speed_scale_and_no_latency_cliff():
    assert speed_score(0) == 100
    assert speed_score(1000) == 50
    assert speed_score(100) == pytest.approx(90.9090909)
    assert abs(weighted_score(80, 199.999) - weighted_score(80, 200.001)) < 0.001
    assert policy()["hard_latency_limit_ms"] is None
    for latency in (200, 1000, 10000, 1e6):
        assert 0 < weighted_score(80, latency) <= 100


@pytest.mark.parametrize(
    "quality,latency",
    [
        (-1, 1),
        (101, 1),
        (True, 1),
        (float("nan"), 1),
        (80, -1),
        (80, float("inf")),
        (80, True),
        (80, "1000"),
    ],
)
def test_invalid_measurements_are_rejected(quality, latency):
    with pytest.raises(ValueError):
        weighted_score(quality, latency)


def test_components_evidence_and_quality_interval_remain_intact():
    original = example()
    saved = copy.deepcopy(original)
    result = add_weighted_score(original)
    assert original == saved
    assert result["quality_score"] == result["score"] == 80
    assert result["p95_ms"] == 1000 and result["ci95"] == [70, 90]
    assert result["errors"] == 2 and result["trust"] == "local-unattested"
    assert result["recording_latency_policy"] == original["latency_policy"]
    assert not {"latency_eligible", "latency_policy", "misses"} & result.keys()
    assert result["weighted_per_game"]["maze"] == weighted_score(60, 1000)
    assert add_weighted_score(result) == result


def test_adding_a_model_does_not_change_an_existing_models_score():
    first = {**example(), "agent": "first"}
    second = {**example(), "agent": "second", "score": 10, "p95_ms": 1}
    alone = rank_rows([first])[0]
    together = next(row for row in rank_rows([first, second]) if row["agent"] == "first")
    assert alone == together


def test_migration_changes_only_the_active_derived_view():
    spec = importlib.util.spec_from_file_location(
        "weighted_migration", Path(__file__).parents[1] / "scripts/apply_weighted_score.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot = {"exhibition": [example()], "official": [], "local_previous": [example()]}
    saved = copy.deepcopy(snapshot)
    migrated, changes = module.transform(snapshot)
    assert snapshot == saved
    assert migrated["local_previous"] == saved["local_previous"]
    assert migrated["official"] == []
    assert changes[0]["quality"] == 80 and changes[0]["p95_ms"] == 1000
