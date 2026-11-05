"""Re-score active leaderboard rows without replaying or altering measurements."""

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from generalgamebench.weighted_score import policy, rank_rows

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TRACKS = ("exhibition", "official")
REMOVED = {"latency_eligible", "latency_policy", "misses"}
ADDED = {
    "quality_score",
    "speed_score",
    "weighted_score",
    "weighted_per_game",
    "scoring_policy_id",
    "recording_latency_policy",
}


def transform(snapshot):
    result = copy.deepcopy(snapshot)
    changes = []
    for track in ACTIVE_TRACKS:
        original = {row["agent"]: row for row in snapshot.get(track, [])}
        result[track] = rank_rows(snapshot.get(track, []))
        for rank, row in enumerate(result[track], 1):
            previous = original[row["agent"]]
            for key, value in previous.items():
                if key not in REMOVED | ADDED and row[key] != value:
                    raise ValueError("A measured value changed")
            changes.append(
                {
                    "track": track,
                    "agent": row["agent"],
                    "position": rank,
                    "quality": row["quality_score"],
                    "p95_ms": row["p95_ms"],
                    "speed": row["speed_score"],
                    "weighted_score": row["weighted_score"],
                }
            )
    result["scoring_policy"] = policy()
    result.pop("latency_policy", None)
    return result, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "site/dist/data.json")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    if report.exists():
        raise FileExistsError("Preserve prior reports. Choose a new directory.")
    previous = args.snapshot.read_bytes()
    source = json.loads(previous)
    result, changes = transform(source)
    report.mkdir(parents=True)
    (report / "previous-snapshot.json").write_bytes(previous)
    report_path = str(report.relative_to(ROOT))
    source_hash = hashlib.sha256(previous).hexdigest()
    result.setdefault("archives", []).append(
        {
            "snapshot": report_path + "/previous-snapshot.json",
            "sha256": source_hash,
            "season": source.get("season"),
            "note": "Previous quality-only ranking and historical latency rule. Measurements remain unchanged.",
        }
    )
    result["scoring_report"] = report_path
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    report_data = {
        "policy": policy(),
        "source_snapshot_sha256": source_hash,
        "measurements_unchanged": True,
        "evidence_unchanged": True,
        "new_model_calls": 0,
        "active_tracks": list(ACTIVE_TRACKS),
        "changes": changes,
    }
    (report / "validation.json").write_text(json.dumps(report_data, indent=2) + "\n")
    payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
    (report / "snapshot.json").write_text(payload)
    if args.snapshot.read_bytes() != previous:
        raise ValueError("The source table changed during analysis")
    args.snapshot.write_text(payload)
    print(json.dumps(changes, indent=2))


if __name__ == "__main__":
    main()
