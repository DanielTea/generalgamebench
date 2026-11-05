"""Append a declared CLI cohort to an existing weighted leaderboard."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from export_jev import compare_tasks
from export_refresh import verify_source
from run_campaign import model_id

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.ranking import summarize
from generalgamebench.weighted_score import add_weighted_score, policy, rank_rows

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retained_evidence(campaign, snapshot):
    report = ROOT / campaign["retained_report"]
    for name, expected_hash in campaign["retained_file_hashes"].items():
        if sha(report / name) != expected_hash:
            raise ValueError("A retained evidence report changed")
    roots = load(report / "evidence-roots.json")
    checks = load(report / "replay-validation.json")
    expected = {(r["agent"], r["game"], r["seed"]): r for r in load(report / "episodes.json")}
    if set(roots) != set(checks) or len(roots) != len(expected):
        raise ValueError("The retained evidence inventory differs")
    rows = []
    for relative, head in roots.items():
        path = ROOT / relative
        if not checks[relative].get("valid") or not checks[relative].get("replayed"):
            raise ValueError("The retained native replay did not pass")
        verify_episode(path, replay=False)
        if json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"] != head:
            raise ValueError("A retained evidence root changed")
        row = read_ledger(path / "events.jsonl")[-1]
        if load(path / "result.json") != row or row != expected.pop(
            (row["agent"], row["game"], row["seed"])
        ):
            raise ValueError("A retained result differs from its published ledger")
        rows.append(row)
    originals = {r["agent"]: r for r in snapshot["exhibition"]}
    if expected or {r["agent"] for r in rows} != set(originals):
        raise ValueError("Retained models or episodes are missing")
    # Each historical cohort keeps its actual engine image IDs and transport.
    for agent, original in originals.items():
        measured = summarize(
            [r for r in rows if r["agent"] == agent], campaign["games"], campaign["seeds"]
        )[0]
        measured["hardware_details"] = original["hardware_details"]
        if add_weighted_score(measured) != original:
            raise ValueError("A retained weighted row differs from its evidence")
    return rows, roots, checks


def check_result(row, entry, campaign, game, seed):
    metadata = row["provider_metadata"]
    if (
        row["agent"],
        row["model"],
        row["game"],
        row["seed"],
        row["mode"],
        row["version"],
        row["max_steps"],
        row["response_timeout_seconds"],
        metadata.get("requested_model"),
        metadata.get("prompt_version"),
        metadata.get("transport"),
        metadata.get("observation"),
        metadata.get("reasoning_effort"),
        metadata.get("tool_events"),
        metadata.get("warmup"),
    ) != (
        model_id(entry),
        entry["model"],
        game,
        seed,
        campaign["mode"],
        campaign["version"],
        campaign["max_steps"],
        campaign["timeout_s"],
        entry["model"],
        campaign["prompt_version"],
        "authenticated-cli-per-frame",
        "png-only",
        "low",
        0,
        None,
    ):
        raise ValueError("A new model, prompt or run setting differs from the declaration")
    if entry["provider"] == "claude" and metadata.get("resolved_models") != [entry["model"]]:
        raise ValueError("The Claude response resolved to a different model")


def export(report):
    if any((report / name).exists() for name in ("snapshot.json", "previous-snapshot.json")):
        raise FileExistsError("Preserve published snapshots. Use a new report directory.")
    campaign = load(report / "campaign.json")
    verify_source(campaign)
    current = ROOT / "site/dist/data.json"
    previous = current.read_bytes()
    if hashlib.sha256(previous).hexdigest() != campaign["base_snapshot_sha256"]:
        raise ValueError("The leaderboard changed after the declaration")
    snapshot = json.loads(previous)
    if snapshot["scoring_policy"] != policy() or campaign["scoring_policy"] != policy():
        raise ValueError("The scoring policy differs")
    retained, roots, checks = retained_evidence(campaign, snapshot)
    audit_path = ROOT / campaign["engine_rebuild_audit"]
    if sha(audit_path) != campaign["engine_rebuild_sha256"]:
        raise ValueError("The engine rebuild audit changed")
    rebuilds = load(audit_path)["games"]
    new, new_roots, statuses, board = [], {}, [], []
    pairs = [(g, s) for g in campaign["games"] for s in campaign["seeds"]]
    for entry in load(report / "model-inventory.json")["models"]:
        agent = model_id(entry)
        if any(r["agent"] == agent for r in [*snapshot["exhibition"], *board]):
            raise ValueError("The model is already in the leaderboard")
        folder = ROOT / campaign["run_root"] / agent
        status = load(folder / "status.json")
        if status != {
            "agent": agent,
            "provider": entry["provider"],
            "model": entry["model"],
            "revision": entry.get("revision"),
            "status": "complete",
            "completed": len(pairs),
        }:
            raise ValueError("Resolve incomplete model runs before publication")
        if {p for p in folder.iterdir() if p.is_dir()} != {folder / f"{g}-{s}" for g, s in pairs}:
            raise ValueError("The new episode inventory differs from the declared suite")
        rows = []
        for number, (game, seed) in enumerate(pairs, 1):
            path = folder / f"{game}-{seed}"
            proof = verify_episode(path)
            row = read_ledger(path / "events.jsonl")[-1]
            if load(path / "result.json") != row:
                raise ValueError("A new result differs from its ledger")
            check_result(row, entry, campaign, game, seed)
            compare_tasks(
                {
                    game: next(
                        r
                        for r in snapshot["exhibition"]
                        if r["agent"] == campaign["task_reference_agent"]
                    )["task_metadata"][game]
                },
                {game: row["game_metadata"]},
                rebuilds,
            )
            relative = str(path.relative_to(ROOT))
            roots[relative] = new_roots[relative] = json.loads(
                (path / "events.jsonl").read_text().splitlines()[-1]
            )["hash"]
            checks[relative] = proof
            rows.append(row)
            print(f"Replayed {entry['model']} {number}/{len(pairs)}", flush=True)
        measured = summarize(rows, campaign["games"], campaign["seeds"])[0]
        measured["hardware_details"] = campaign["hardware_details"]
        for key in (
            "games",
            "seed_ids",
            "max_steps",
            "mode",
            "hardware",
            "version",
            "response_timeout_seconds",
        ):
            if measured.get(key) != snapshot["exhibition"][0].get(key):
                raise ValueError("The new suite differs from the previous suite")
        # Legacy raw latency flags are evidence-format diagnostics, not a recording gate.
        for key in ("latency_policy", "latency_eligible", "misses"):
            measured.pop(key)
        board.append(add_weighted_score(measured))
        statuses.append(status)
        new.extend(rows)
    verify_source(campaign)
    snapshot["exhibition"] = rank_rows([*snapshot["exhibition"], *board])
    snapshot["model_status"].extend(statuses)
    snapshot["model_status"].extend(campaign.get("unavailable_models", []))
    snapshot["season"] = campaign["id"]
    snapshot["current_campaign"] = str(report.relative_to(ROOT) / "campaign.json")
    snapshot["campaigns"].append(snapshot["current_campaign"])
    snapshot["suite_files"].insert(0, campaign["suite_file"])
    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["comparison_note"] = campaign["comparison_note"]
    snapshot["track_metadata"]["exhibition"] = {
        "season": campaign["id"],
        "hardware_details": campaign["comparison_note"],
    }
    snapshot["archives"].append(
        {
            "snapshot": str(report.relative_to(ROOT) / "previous-snapshot.json"),
            "sha256": campaign["base_snapshot_sha256"],
            "season": json.loads(previous)["season"],
            "note": "The previous weighted snapshot and all 16 model rows remain unchanged.",
        }
    )
    if current.read_bytes() != previous:
        raise ValueError("The leaderboard changed during replay")
    (report / "previous-snapshot.json").write_bytes(previous)
    for name, value in {
        "episodes.json": [*retained, *new],
        "evidence-roots.json": roots,
        "new-evidence-roots.json": new_roots,
        "replay-validation.json": checks,
        "model-status.json": statuses,
        "snapshot.json": snapshot,
        "retained-evidence.json": {
            "report": campaign["retained_report"],
            "episodes": len(retained),
            "files": campaign["retained_file_hashes"],
            "note": "Rechecked ledger and PNG hashes and all weighted rows. Reused the unchanged native replay proof. Historical sources and recording rules remain archived.",
        },
    }.items():
        (report / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    current.write_bytes((report / "snapshot.json").read_bytes())
    print(
        json.dumps(
            [
                {
                    k: r[k]
                    for k in (
                        "model",
                        "quality_score",
                        "weighted_score",
                        "p95_ms",
                        "errors",
                        "decisions",
                    )
                }
                for r in board
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    export(parser.parse_args().report.resolve())
