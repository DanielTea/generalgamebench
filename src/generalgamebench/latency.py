"""The current suite limit and the fixed rules for recorded evidence."""

import numpy as np

POLICY_ID = "suite-p95-200-v1"
LIMIT_MS = 200.0
LEGACY_VERSIONS = {"0.1.0", "0.2.0", "0.3.0", "0.4.0"}


def policy() -> dict:
    return {
        "id": POLICY_ID,
        "metric": "suite_p95_ms",
        "limit_ms": LIMIT_MS,
        "comparison": "strictly_less_than",
        "quantile_method": "linear",
        "sample_scope": "all_recorded_decisions_in_complete_suite",
    }


def passes(times) -> bool:
    return bool(len(times) and np.quantile(times, 0.95, method="linear") < LIMIT_MS)


def legacy_evidence(manifest) -> bool:
    if manifest.get("version") in LEGACY_VERSIONS and "latency_policy" not in manifest:
        return True
    if manifest.get("latency_policy") != POLICY_ID:
        raise ValueError("Unknown or missing latency policy")
    return False
