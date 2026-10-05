"""Add complete, replay-checked model runs to the current exhibition."""

import argparse
import concurrent.futures
import json
from datetime import datetime, timezone
from pathlib import Path

from export_refresh import verify_source
from run_campaign import model_id

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.latency import policy
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]
COHORT_KEYS = ("games", "seed_ids", "max_steps", "mode", "hardware", "task_metadata")
EXHIBITION_VERSIONS = {"0.4.0", "0.5.0"}


def append_board(snapshot, board, statuses):
    existing = snapshot["exhibition"]
    if not existing or not board:
        raise ValueError("Both the current exhibition and the new model cohort must be present")
    old_ids = {row["agent"] for row in existing}
    new_ids = [row["agent"] for row in board]
    if len(set(new_ids)) != len(new_ids) or old_ids.intersection(new_ids):
        raise ValueError("Do not replace an existing model result")
    reference = {key: existing[0].get(key) for key in COHORT_KEYS}
    for row in [*existing, *board]:
        # Version 0.5 changes the response timeout and latency policy. Preserve
        # each version in the table; require identical native task metadata.
        if (
            row["version"] not in EXHIBITION_VERSIONS
            or row["mode"] != "exhibition"
            or row.get("latency_policy") != policy()
        ):
            raise ValueError("Unknown exhibition version or latency policy")
        if {key: row.get(key) for key in COHORT_KEYS} != reference:
            raise ValueError("The new results must use the same game suite and referee settings")
    snapshot["exhibition"] = sorted(
        [*existing, *board], key=lambda row: (-row["score"], row["agent"])
    )
    snapshot["model_status"] = [*snapshot.get("model_status", []), *statuses]
    return snapshot


def export(report, workers):
    campaign = json.loads((report / "campaign.json").read_text())
    inventory = json.loads((report / "model-inventory.json").read_text())
    if (report / "snapshot.json").exists():
        raise FileExistsError("Preserve the published snapshot. Use a new report directory.")
    verify_source(campaign)
    paths, statuses, expected = [], [], {}
    for entry in inventory["models"]:
        folder = ROOT / campaign["run_root"] / model_id(entry)
        status = json.loads((folder / "status.json").read_text())
        if status["status"] != "complete":
            raise ValueError(f"The full suite is not complete: {entry['model']}")
        statuses.append(status)
        for game in campaign["games"]:
            for seed in campaign["seeds"]:
                path = folder / f"{game}-{seed}"
                paths.append(path)
                expected[path] = entry

    def check(path):
        replay = verify_episode(path)
        ledger = read_ledger(path / "events.jsonl")
        result = ledger[-1]
        entry, metadata = expected[path], result["provider_metadata"]
        if (
            result["agent"] != model_id(entry)
            or result["model"] != entry["model"]
            or metadata.get("requested_model") != entry["model"]
            or metadata.get("revision") != entry["revision"]
            or metadata.get("warmup") != entry.get("warmup")
            or metadata.get("prompt_version") != campaign["prompt_version"]
        ):
            raise ValueError("An episode differs from the declared model configuration")
        if (result["mode"], result["version"], result["max_steps"]) != (
            campaign["mode"],
            campaign["version"],
            campaign["max_steps"],
        ):
            raise ValueError("An episode differs from the declared campaign")
        root = json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]
        return str(path.relative_to(ROOT)), replay, result, root

    rows, checks, roots = [], {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for number, (path, replay, row, head) in enumerate(pool.map(check, paths), 1):
            rows.append(row)
            checks[path], roots[path] = replay, head
            if number % 25 == 0:
                print(f"Replayed {number}/{len(paths)} episodes", flush=True)
    verify_source(campaign)
    board = summarize(rows, campaign["games"], campaign["seeds"])
    for row in board:
        row["hardware_details"] = campaign["hardware_details"]
    snapshot = json.loads((ROOT / "site/dist/data.json").read_text())
    append_board(snapshot, board, statuses)
    history = snapshot.get("campaigns", [snapshot["current_campaign"]])
    current = str(report.relative_to(ROOT) / "campaign.json")
    snapshot.update(
        campaigns=[*history, current],
        current_campaign=current,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    for name, value in {
        "episodes.json": rows,
        "replay-validation.json": checks,
        "evidence-roots.json": roots,
        "model-status.json": statuses,
        "snapshot.json": snapshot,
    }.items():
        (report / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    (ROOT / "site/dist/data.json").write_text(
        json.dumps(snapshot, indent=2, allow_nan=False) + "\n"
    )
    print(json.dumps({"new_models": len(board), "verified_episodes": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("Workers must be positive")
    export(args.report.resolve(), args.workers)
