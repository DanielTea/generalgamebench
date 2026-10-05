"""Replay a complete declared baseline matrix and preserve existing model cohorts."""

import argparse
import concurrent.futures
import json
from datetime import datetime, timezone
from pathlib import Path

from export_refresh import verify_source
from run_baseline_campaign import check_episode

from generalgamebench.evidence import verify_episode
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]


def export(report, workers=4):
    if workers < 1:
        raise ValueError("Workers must be positive")
    if (report / "snapshot.json").exists():
        raise FileExistsError("Preserve published snapshots; choose a new campaign")
    campaign = json.loads((report / "campaign.json").read_text())
    status = json.loads((report / "run-status.json").read_text())
    if status["status"] != "recorded-awaiting-replay":
        raise ValueError("Finish serial recording before replay or publication")
    dimensions = [campaign[key] for key in ("agents", "games", "seeds")]
    if not all(items and len(items) == len(set(items)) for items in dimensions):
        raise ValueError("Campaign dimensions must be nonempty and unique")
    selected = [
        (ROOT / campaign["run_root"] / name / f"{game}-{seed}", name, game, seed)
        for name in campaign["agents"]
        for game in campaign["games"]
        for seed in campaign["seeds"]
    ]
    if status["completed"] != len(selected) or status["expected"] != len(selected):
        raise ValueError("Recording count differs from complete matrix")
    actual = {p.parent for p in (ROOT / campaign["run_root"]).rglob("result.json")}
    if actual != {p for p, *_ in selected}:
        raise ValueError("Missing or extra episodes in declared matrix")
    verify_source(campaign)

    def audit(item):
        path, name, game, seed = item
        row = check_episode(path, campaign, name, game, seed)
        check = verify_episode(path, replay=True)
        head = json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]
        return row, str(path.relative_to(ROOT)), check, head

    rows, roots, checks = [], {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for index, (row, relative, check, head) in enumerate(pool.map(audit, selected), 1):
            rows.append(row)
            roots[relative], checks[relative] = head, check
            if index % 20 == 0 or index == len(selected):
                print(f"Replayed {index}/{len(selected)} baseline episodes", flush=True)
    verify_source(campaign)
    board = summarize(rows, campaign["games"], campaign["seeds"])
    if {r["agent"] for r in board} != set(campaign["agents"]):
        raise ValueError("Ranking differs from declared baseline set")
    snapshot = json.loads((ROOT / "site/dist/data.json").read_text())
    metadata = snapshot.setdefault("track_metadata", {})
    metadata["local_previous"] = metadata.get(
        "local",
        {"season": snapshot["season"], "hardware_details": snapshot.get("hardware_details")},
    ).copy()
    metadata["local"] = {"season": campaign["id"], "hardware_details": campaign["concurrency_note"]}
    snapshot.update(
        season=campaign["id"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        local_previous=snapshot["local"],
        local=board,
        baseline_campaign=str(report.relative_to(ROOT) / "campaign.json"),
    )
    snapshot["suite_files"] = list(
        dict.fromkeys([campaign["suite_file"], *snapshot.get("suite_files", [])])
    )

    def save(path, value):
        path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

    save(report / "episodes.json", rows)
    save(report / "evidence-roots.json", roots)
    save(report / "replay-validation.json", checks)
    save(report / "snapshot.json", snapshot)
    save(ROOT / "site/dist/data.json", snapshot)
    save(
        report / "run-status.json",
        {**status, "status": "replay-verified", "verified_episodes": len(rows)},
    )
    print(
        json.dumps(
            {
                "episodes": len(rows),
                "decisions": sum(r["decisions"] for r in board),
                "agents": len(board),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    export(args.report.resolve(), args.workers)
