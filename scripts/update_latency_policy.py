"""Apply the current latency rule to a complete, unchanged recorded snapshot."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from generalgamebench.latency import policy
from generalgamebench.ranking import summarize

TRACKS = ("local", "local_previous", "exhibition", "exhibition_previous", "official")
MUTABLE = {"latency_eligible", "latency_policy", "misses"}


def identity(row):
    return tuple(row[k] for k in ("agent", "mode", "hardware", "version", "max_steps"))


def update(snapshot, episodes):
    result = copy.deepcopy(snapshot)
    changes = []
    for track in TRACKS:
        for row in result.get(track, []):
            selected = [
                ep
                for ep in episodes
                if identity(ep) == identity(row)
                and ep["game"] in row["games"]
                and ep["seed"] in row["seed_ids"]
            ]
            calculated = summarize(selected, row["games"], row["seed_ids"])
            if len(calculated) != 1:
                raise ValueError(f"Missing episode set: {track}/{row['agent']}")
            # Check every existing value. Do not rewrite scores or trust claims.
            for key, value in row.items():
                if key not in MUTABLE and calculated[0].get(key) != value:
                    raise ValueError(f"Recorded result differs: {track}/{row['agent']}/{key}")
            before = row["latency_eligible"]
            for key in MUTABLE:
                row[key] = calculated[0][key]
            changes.append(
                {
                    "track": track,
                    "agent": row["agent"],
                    "previous_pass": before,
                    "current_pass": row["latency_eligible"],
                    "suite_p95_ms": row["p95_ms"],
                }
            )
    result["latency_policy"] = policy()
    return result, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a new output directory. Keep the previous update.")
    snapshot, changes = update(
        json.loads(args.snapshot.read_text()),
        [row for file in args.episodes for row in json.loads(file.read_text())],
    )
    report = {
        "latency_policy": policy(),
        "source_sha256": {
            str(file): hashlib.sha256(file.read_bytes()).hexdigest()
            for file in (args.snapshot, *args.episodes)
        },
        "scores_unchanged": True,
        "evidence_unchanged": True,
        "changes": changes,
    }
    args.output.mkdir(parents=True)
    for name, data in (("snapshot.json", snapshot), ("validation.json", report)):
        (args.output / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"rows": len(changes), "output": str(args.output)}))


if __name__ == "__main__":
    main()
