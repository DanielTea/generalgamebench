"""Add verified hosted reruns to the fixed local vision model results."""

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
COMPARISON_KEYS = (
    "games",
    "seed_ids",
    "max_steps",
    "mode",
    "hardware",
    "version",
    "task_metadata",
    "response_timeout_seconds",
    "latency_policy",
)


def load(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combine_board(retained, new, campaign):
    if not retained or not new:
        raise ValueError("Both retained and new complete model results are required")
    expected = {key: retained[0].get(key) for key in COMPARISON_KEYS}
    if (
        expected["games"],
        expected["seed_ids"],
        expected["max_steps"],
        expected["mode"],
        expected["version"],
        expected["response_timeout_seconds"],
        expected["latency_policy"],
    ) != (
        campaign["games"],
        campaign["seeds"],
        campaign["max_steps"],
        campaign["mode"],
        campaign["version"],
        campaign["timeout_s"],
        policy(),
    ):
        raise ValueError("The retained suite differs from the new declaration")
    agents = set()
    for row in [*retained, *new]:
        if row["agent"] in agents:
            raise ValueError("A model already exists in the current table")
        agents.add(row["agent"])
        if {key: row.get(key) for key in COMPARISON_KEYS} != expected:
            raise ValueError("The game, seed, referee, or task settings differ")
        if (
            not row.get("model")
            or not row.get("hardware_details")
            or row["episodes"] != len(campaign["games"]) * len(campaign["seeds"])
            or row.get("provider_metadata", {}).get("prompt_version") != campaign["prompt_version"]
        ):
            raise ValueError("The model suite or its test conditions are incomplete")
    return sorted([*retained, *new], key=lambda row: (-row["score"], row["agent"]))


def read_base(campaign, snapshot):
    base_path = ROOT / campaign["base_campaign"]
    base = load(base_path)
    verify_source(base)
    report = base_path.parent
    if sha256(report / "snapshot.json") != campaign["base_snapshot_sha256"]:
        raise ValueError("The retained snapshot changed")
    if load(report / "snapshot.json") != snapshot:
        raise ValueError("The current table differs from the retained snapshot")
    roots = load(report / "evidence-roots.json")
    checks = load(report / "replay-validation.json")
    expected = {(r["agent"], r["game"], r["seed"]): r for r in load(report / "episodes.json")}
    rows = []
    if set(roots) != set(checks) or len(roots) != len(expected):
        raise ValueError("The retained evidence inventory differs")
    for relative, head in roots.items():
        path = ROOT / relative
        check = checks[relative]
        if not check.get("valid") or not check.get("replayed"):
            raise ValueError("The retained native replay did not pass")
        verify_episode(path, replay=False)
        if json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"] != head:
            raise ValueError("A retained evidence root changed")
        row = read_ledger(path / "events.jsonl")[-1]
        if load(path / "result.json") != row:
            raise ValueError("A retained result file differs from its ledger")
        if row != expected.pop((row["agent"], row["game"], row["seed"])):
            raise ValueError("A retained episode differs from its published record")
        rows.append(row)
    if expected:
        raise ValueError("Retained episodes are missing")
    recomputed = summarize(rows, campaign["games"], campaign["seeds"])
    original = {r["agent"]: r for r in snapshot["exhibition"]}
    for row in recomputed:
        row["hardware_details"] = original[row["agent"]]["hardware_details"]
    if recomputed != snapshot["exhibition"]:
        raise ValueError("The retained ranking differs from its evidence")
    return (
        rows,
        roots,
        checks,
        {
            "campaign": campaign["base_campaign"],
            "snapshot_sha256": campaign["base_snapshot_sha256"],
            "evidence_roots_sha256": sha256(report / "evidence-roots.json"),
            "replay_validation_sha256": sha256(report / "replay-validation.json"),
            "episodes": len(rows),
            "note": "Native replay passed before the local model publication. This export checks the unchanged source, ledger, image hashes, and ranking again. It reuses that fixed native replay report.",
        },
    )


def export(report, workers=2):
    if any((report / name).exists() for name in ("snapshot.json", "previous-snapshot.json")):
        raise FileExistsError("Preserve the published files. Use a new report directory.")
    campaign = load(report / "campaign.json")
    verify_source(campaign)
    previous_path = ROOT / "site/dist/data.json"
    previous = previous_path.read_bytes()
    if hashlib.sha256(previous).hexdigest() != campaign["base_snapshot_sha256"]:
        raise ValueError("The current table changed after the declaration")
    snapshot = json.loads(previous)
    retained, roots, checks, retained_proof = read_base(campaign, snapshot)
    statuses, selections = [], []
    for entry in load(report / "model-inventory.json")["models"]:
        name = model_id(entry)
        folder = ROOT / campaign["run_root"] / name
        status = load(folder / "status.json")
        if (status["agent"], status["model"], status["provider"], status.get("revision")) != (
            name,
            entry["model"],
            entry["provider"],
            entry.get("revision"),
        ):
            raise ValueError("The model status differs from the declaration")
        pairs = [(g, s) for g in campaign["games"] for s in campaign["seeds"]]
        complete = status["status"] == "complete"
        if not complete and status["status"] != "provider-unavailable":
            raise ValueError("Resolve incomplete or blocked model runs before publication")
        if not complete:
            pairs = pairs[:1]
        expected_paths = {folder / f"{g}-{s}" for g, s in pairs}
        if (
            status["completed"] != len(pairs)
            or {p for p in folder.iterdir() if p.is_dir()} != expected_paths
        ):
            raise ValueError("The episode inventory differs from its terminal status")
        statuses.append(status)
        selections.extend((folder / f"{g}-{s}", entry, g, s, complete) for g, s in pairs)

    def check(selection):
        path, entry, game, seed, complete = selection
        proof = verify_episode(path)
        row = read_ledger(path / "events.jsonl")[-1]
        if load(path / "result.json") != row:
            raise ValueError("A result file differs from its ledger")
        metadata = row["provider_metadata"]
        if (
            row["agent"],
            row["game"],
            row["seed"],
            row["mode"],
            row["version"],
            row["max_steps"],
            row.get("response_timeout_seconds"),
        ) != (
            model_id(entry),
            game,
            seed,
            campaign["mode"],
            campaign["version"],
            campaign["max_steps"],
            campaign["timeout_s"],
        ):
            raise ValueError("An episode differs from the declared suite")
        if (
            metadata.get("requested_model"),
            metadata.get("revision"),
            metadata.get("prompt_version"),
            metadata.get("transport"),
            metadata.get("warmup"),
        ) != (
            entry["model"],
            entry.get("revision"),
            campaign["prompt_version"],
            "authenticated-cli-per-frame",
            None,
        ):
            raise ValueError("An episode differs from the declared provider settings")
        if metadata.get("tool_events") != 0:
            raise ValueError("The provider used a forbidden tool")
        if not complete and row["errors"] != ["ProviderUnavailable"]:
            raise ValueError("An unavailable model has a different failure type")
        if row["game_metadata"] != snapshot["exhibition"][0]["task_metadata"][game]:
            raise ValueError("The game engine differs from the retained local runs")
        head = json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]
        return str(path.relative_to(ROOT)), row, proof, head, complete

    new, incomplete = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for number, (path, row, proof, head, complete) in enumerate(pool.map(check, selections), 1):
            (new if complete else incomplete).append(row)
            roots[path], checks[path] = head, proof
            if number % 25 == 0:
                print(f"Replayed {number}/{len(selections)} hosted episodes", flush=True)
    verify_source(campaign)
    board = summarize(new, campaign["games"], campaign["seeds"])
    for row in board:
        row["hardware_details"] = campaign["hardware_details"]
    snapshot["exhibition"] = combine_board(snapshot["exhibition"], board, campaign)
    snapshot["model_status"] = [*snapshot["model_status"], *statuses]
    snapshot["season"] = campaign["id"]
    snapshot["current_campaign"] = str(report.relative_to(ROOT) / "campaign.json")
    snapshot["campaigns"] = [*snapshot["campaigns"], snapshot["current_campaign"]]
    snapshot["suite_files"] = [campaign["suite_file"], *snapshot["suite_files"]]
    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["comparison_note"] = campaign["comparison_note"]
    snapshot["track_metadata"]["exhibition"] = {
        "season": campaign["id"],
        "hardware_details": campaign["comparison_note"],
    }
    snapshot["archives"] = [
        *snapshot["archives"],
        {
            "snapshot": str(report.relative_to(ROOT) / "previous-snapshot.json"),
            "sha256": campaign["base_snapshot_sha256"],
            "season": json.loads(previous)["season"],
            "note": "The previous four-model snapshot remains unchanged. Its verified model rows remain in the current table.",
        },
    ]
    if previous_path.read_bytes() != previous:
        raise ValueError("The current table changed during replay validation")
    (report / "previous-snapshot.json").write_bytes(previous)
    for name, value in {
        "episodes.json": [*retained, *new],
        "incomplete-episodes.json": incomplete,
        "evidence-roots.json": roots,
        "replay-validation.json": checks,
        "retained-evidence.json": retained_proof,
        "model-status.json": statuses,
        "snapshot.json": snapshot,
    }.items():
        (report / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    previous_path.write_bytes((report / "snapshot.json").read_bytes())
    print(
        json.dumps(
            {
                "retained_models": len(snapshot["exhibition"]) - len(board),
                "new_models": len(board),
                "episodes": len(retained) + len(new),
                "incomplete_episodes": len(incomplete),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("Workers must be positive")
    export(args.report.resolve(), args.workers)
