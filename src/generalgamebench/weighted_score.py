"""Continuous quality and p95 score for the current leaderboard view."""

import copy
import math

POLICY_ID = "quality70-speed30-p95-v1"
QUALITY_WEIGHT = 0.7
SPEED_WEIGHT = 0.3
REFERENCE_MS = 1000.0


def policy():
    return {
        "id": POLICY_ID,
        "quality_weight": QUALITY_WEIGHT,
        "speed_weight": SPEED_WEIGHT,
        "latency_reference_ms": REFERENCE_MS,
        "speed_formula": "100 / (1 + p95_ms / 1000)",
        "score_formula": "100 * (quality / 100)^0.7 * (speed / 100)^0.3",
        "aggregation": "weighted_geometric_mean",
        "hard_latency_limit_ms": None,
        "quantile_method": "linear",
        "latency_sample_scope": "all_recorded_decisions_in_complete_suite",
        "per_game_latency": "same_observed_suite_p95",
        "ci95_metric": "quality_only",
    }


def _valid_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Invalid {name}")


def speed_score(p95_ms):
    _valid_number(p95_ms, "p95")
    if p95_ms < 0:
        raise ValueError("p95 must be nonnegative")
    return 100 / (1 + p95_ms / REFERENCE_MS)


def weighted_score(quality, p95_ms):
    _valid_number(quality, "quality")
    if not 0 <= quality <= 100:
        raise ValueError("Quality must be between 0 and 100")
    speed = speed_score(p95_ms)
    return 100 * (quality / 100) ** QUALITY_WEIGHT * (speed / 100) ** SPEED_WEIGHT


def add_weighted_score(row):
    """Keep measured quality and times; remove the former admission flags."""
    result = copy.deepcopy(row)
    quality, p95 = row["score"], row["p95_ms"]
    result.update(
        quality_score=quality,
        speed_score=speed_score(p95),
        weighted_score=weighted_score(quality, p95),
        weighted_per_game={g: weighted_score(q, p95) for g, q in row.get("per_game", {}).items()},
        scoring_policy_id=POLICY_ID,
    )
    recording_policy = result.pop("latency_policy", None)
    if recording_policy is not None:
        result.setdefault("recording_latency_policy", recording_policy)
    result.pop("latency_eligible", None)
    result.pop("misses", None)
    return result


def rank_rows(rows):
    return sorted(
        (add_weighted_score(row) for row in rows),
        key=lambda row: (
            -row["weighted_score"],
            -row["quality_score"],
            row["p95_ms"],
            row["agent"],
        ),
    )
