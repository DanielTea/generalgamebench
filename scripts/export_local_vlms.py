"""Show a new verified model cohort and archive the previous snapshot."""

import argparse
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from export_refresh import verify_source
from run_campaign import model_id

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.latency import policy
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]
COHORT_KEYS = (
    "games",
    "seed_ids",
    "max_steps",
    "mode",
    "hardware",
    "version",
    "task_metadata",
    "response_timeout_seconds",
    "hardware_details",
)


def replace_board(snapshot, board, statuses, campaign):
    if not board:
        raise ValueError("The new model cohort must be present")
    new_ids = [row["agent"] for row in board]
    if len(set(new_ids)) != len(new_ids):
        raise ValueError("The new cohort contains duplicate model results")
    if len(statuses) != len(board) or {s["agent"] for s in statuses} != set(new_ids):
        raise ValueError("The model status list differs from the new cohort")
    episodes = len(campaign["games"]) * len(campaign["seeds"])
    if any(s["status"] != "complete" or s["completed"] != episodes for s in statuses):
        raise ValueError("Every model must complete the declared suite")
    reference = {key: board[0].get(key) for key in COHORT_KEYS}
    for row in board:
        if (
            row["version"] != campaign["version"]
            or row["mode"] != "exhibition"
            or not row.get("model")
            or row.get("latency_policy") != policy()
        ):
            raise ValueError("The model, evaluator version or latency policy is invalid")
        if {key: row.get(key) for key in COHORT_KEYS} != reference:
            raise ValueError("All new models must use the same suite and referee settings")
        if (
            row["games"],
            row["seed_ids"],
            row["max_steps"],
            row["episodes"],
            row["response_timeout_seconds"],
        ) != (
            campaign["games"],
            campaign["seeds"],
            campaign["max_steps"],
            episodes,
            campaign["timeout_s"],
        ):
            raise ValueError("The new model results differ from the declared campaign")
    snapshot["exhibition"] = sorted(board, key=lambda row: (-row["score"], row["agent"]))
    snapshot["model_status"] = statuses
    snapshot["season"] = campaign["id"]
    snapshot["hardware_details"] = campaign["hardware_details"]
    snapshot.setdefault("track_metadata", {})["exhibition"] = {
        "season": campaign["id"],
        "hardware_details": campaign["hardware_details"],
    }
    snapshot["latency_policy"] = policy()
    snapshot["coverage"]["task_count"] = len(campaign["games"])
    return snapshot


def export(report, workers):
    campaign = json.loads((report / "campaign.json").read_text())
    inventory = json.loads((report / "model-inventory.json").read_text())
    if any((report / name).exists() for name in ("snapshot.json", "previous-snapshot.json")):
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
                expected[path] = (entry, game, seed)

    def check(path):
        replay = verify_episode(path)
        ledger = read_ledger(path / "events.jsonl")
        result = ledger[-1]
        (entry, game, seed), metadata = expected[path], result["provider_metadata"]
        if (
            result["agent"] != model_id(entry)
            or result["game"] != game
            or result["seed"] != seed
            or result["model"] != entry["model"]
            or metadata.get("requested_model") != entry["model"]
            or metadata.get("revision") != entry["revision"]
            or metadata.get("warmup") != entry.get("warmup")
            or metadata.get("prompt_version") != campaign["prompt_version"]
        ):
            raise ValueError("An episode differs from the declared model configuration")
        if (
            result["mode"],
            result["version"],
            result["max_steps"],
            result.get("response_timeout_seconds"),
        ) != (
            campaign["mode"],
            campaign["version"],
            campaign["max_steps"],
            campaign["timeout_s"],
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
    previous_bytes = (ROOT / "site/dist/data.json").read_bytes()
    snapshot = json.loads(previous_bytes)
    archive = {
        "snapshot": str(report.relative_to(ROOT) / "previous-snapshot.json"),
        "sha256": hashlib.sha256(previous_bytes).hexdigest(),
        "season": snapshot["season"],
        "current_campaign": snapshot.get("current_campaign"),
        "note": "Keep the previous results and recording rules. The model table shows the new verified runs.",
    }
    replace_board(snapshot, board, statuses, campaign)
    snapshot["archives"] = [*snapshot.get("archives", []), archive]
    history = snapshot.get("campaigns", [snapshot["current_campaign"]])
    current = str(report.relative_to(ROOT) / "campaign.json")
    snapshot.update(
        campaigns=[*history, current],
        current_campaign=current,
        generated_at=datetime.now(timezone.utc).isoformat(),
        suite_files=[campaign["suite_file"], *snapshot.get("suite_files", [])],
    )
    (report / "previous-snapshot.json").write_bytes(previous_bytes)
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
