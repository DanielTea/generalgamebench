"""Export a declared hosted-model cohort without replacing historical evidence."""

import argparse
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from run_campaign import model_id

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]


def verify_source(campaign):
    recorded = campaign["source_hashes"]
    replay = campaign.get("replay_source_hashes", recorded)
    if replay.keys() != recorded.keys():
        raise ValueError("Replay source must cover exactly the recorded source files")
    if replay != recorded and not campaign.get("source_change_note"):
        raise ValueError("Document source changes before replaying recorded evidence")
    for source, expected in replay.items():
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Scored/replay source changed: {source}")


def export(report, workers=4):
    if workers < 1:
        raise ValueError("Workers must be positive")
    campaign = json.loads((report / "campaign.json").read_text())
    inventory = json.loads((report / "model-inventory.json").read_text())
    if (report / "snapshot.json").exists():
        raise FileExistsError("Preserve published snapshots; choose a new campaign")
    verify_source(campaign)

    rows, attempts, roots, checks, statuses = [], [], {}, {}, []
    ranked_paths, incomplete_paths = [], []

    def verify(path):
        relative = str(path.relative_to(ROOT))
        check = verify_episode(path)
        rows_in_ledger = read_ledger(path / "events.jsonl")
        row = rows_in_ledger[-1]
        if (row["version"], row["mode"], row["max_steps"]) != (
            campaign["version"],
            campaign["mode"],
            campaign["max_steps"],
        ):
            raise ValueError(f"Episode differs from campaign: {relative}")
        head = json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]
        return row, relative, check, head

    def paths(folder):
        return [
            folder / f"{game}-{seed}" for game in campaign["games"] for seed in campaign["seeds"]
        ]

    for relative, model_names in campaign["assignments"].items():
        for model in model_names:
            entry = next(m for m in inventory["models"] if m["model"] == model)
            folder = ROOT / relative / model_id(entry)
            status = json.loads((folder / "status.json").read_text())
            statuses.append(status)
            if status["status"] == "complete":
                ranked_paths.extend(paths(folder))
            elif status["status"] == "provider-unavailable":
                # Retain failed/incomplete evidence, but never fabricate a suite score.
                incomplete_paths.extend(p.parent for p in sorted(folder.glob("*/result.json")))
            elif status["status"] == "blocked":
                raise ValueError(f"Resolve blocked campaign before publishing: {model}")
            else:
                raise ValueError(f"Campaign still running: {model}")
    for name in campaign["controls"]:
        ranked_paths.extend(paths(ROOT / campaign["control_root"] / name))
    for selection, destination in ((ranked_paths, rows), (incomplete_paths, attempts)):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for index, (row, relative, check, head) in enumerate(pool.map(verify, selection), 1):
                destination.append(row)
                roots[relative], checks[relative] = head, check
                if index % 25 == 0:
                    print(f"Replayed {index}/{len(selection)} episodes", flush=True)
    verify_source(campaign)
    board = summarize(rows, campaign["games"], campaign["seeds"])
    previous = json.loads((ROOT / "results/season-0.2/snapshot.json").read_text())
    snapshot = json.loads((ROOT / "site/dist/data.json").read_text())
    snapshot.update(
        season=campaign["id"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        exhibition=board,
        exhibition_previous=previous["exhibition"],
        model_status=statuses,
        hardware_details=campaign["concurrency_note"],
        track_metadata={
            "local": {"season": "0.2.0", "hardware_details": previous["hardware_details"]},
            "exhibition_previous": {
                "season": "0.2.0",
                "hardware_details": previous["hardware_details"],
            },
            "exhibition": {
                "season": campaign["id"],
                "hardware_details": campaign["concurrency_note"],
            },
        },
        current_campaign=str(report.relative_to(ROOT) / "campaign.json"),
        suite_files=[
            "benchmarks/mac-hosted-exhibition-2026-10-05.json",
            "benchmarks/mac-exhibition-v1.json",
            "benchmarks/mac-baselines-v1.json",
        ],
    )
    snapshot["coverage"]["task_count"] = len(campaign["games"])

    def save(path, value):
        path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

    save(report / "episodes.json", rows)
    save(report / "incomplete-episodes.json", attempts)
    save(report / "evidence-roots.json", roots)
    save(report / "replay-validation.json", checks)
    save(report / "model-status.json", statuses)
    save(report / "snapshot.json", snapshot)
    save(ROOT / "site/dist/data.json", snapshot)
    print(
        json.dumps(
            {
                "ranked_models": sum(bool(r["model"]) for r in board),
                "ranked_episodes": len(rows),
                "incomplete_episodes": len(attempts),
                "verified_episodes": len(roots),
                "decisions": sum(r["decisions"] for r in board),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    export(args.report.resolve(), args.workers)
