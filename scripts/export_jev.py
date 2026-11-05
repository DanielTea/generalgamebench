"""Add a complete replay-verified Jev suite without changing earlier rows."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from export_hosted_rerun import COMPARISON_KEYS, load, read_base
from export_refresh import verify_source

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.jev import ACTION_SCHEMA, TRANSPORT
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]


def compare_tasks(original, current, rebuilds):
    if set(original) != set(current):
        raise ValueError("The scenario sets differ")
    for game, metadata in current.items():
        if metadata == original[game]:
            continue
        proof = rebuilds.get(game, {})
        if (
            proof.get("original_metadata") != original[game]
            or proof.get("rebuilt_metadata") != metadata
            or not proof.get("exact_native_score")
            or proof.get("exact_frames", 0) < 1
            or {k: v for k, v in metadata.items() if k != "container_image"}
            != {k: v for k, v in original[game].items() if k != "container_image"}
        ):
            raise ValueError("The engine differs without a matching rebuild replay audit")


def export(report):
    if any((report / name).exists() for name in ("snapshot.json", "previous-snapshot.json")):
        raise FileExistsError("Preserve published files. Use a new report directory.")
    campaign = load(report / "campaign.json")
    verify_source(campaign)
    current = ROOT / "site/dist/data.json"
    previous = current.read_bytes()
    if hashlib.sha256(previous).hexdigest() != campaign["base_snapshot_sha256"]:
        raise ValueError("The current table changed after the declaration")
    snapshot = json.loads(previous)
    retained, roots, checks, retained_proof = read_base(campaign, snapshot)
    rebuild_path = ROOT / campaign["engine_rebuild_audit"]
    if hashlib.sha256(rebuild_path.read_bytes()).hexdigest() != campaign["engine_rebuild_sha256"]:
        raise ValueError("The engine rebuild audit changed after the declaration")
    rebuilds = load(rebuild_path)["games"]
    for proof in rebuilds.values():
        path = ROOT / proof["episode"]
        verify_episode(path, replay=False)
        if roots.get(proof["episode"]) != proof["evidence_root"]:
            raise ValueError("The rebuild audit refers to different original evidence")
    agent_id = "typesafe-" + campaign["model"]
    folder = ROOT / campaign["run_root"] / agent_id
    status = load(folder / "status.json")
    pairs = [(g, s) for g in campaign["games"] for s in campaign["seeds"]]
    if status != {
        "agent": agent_id,
        "model": campaign["model"],
        "provider": "typesafe",
        "status": "complete",
        "completed": len(pairs),
    }:
        raise ValueError("The Jev suite is not complete")
    if {p for p in folder.iterdir() if p.is_dir()} != {folder / f"{g}-{s}" for g, s in pairs}:
        raise ValueError("The episode inventory differs from the declared suite")
    new, new_roots = [], {}
    for number, (game, seed) in enumerate(pairs, 1):
        path = folder / f"{game}-{seed}"
        proof = verify_episode(path)
        ledger = read_ledger(path / "events.jsonl")
        row = ledger[-1]
        metadata = row["provider_metadata"]
        if load(path / "result.json") != row or (
            row["agent"],
            row["game"],
            row["seed"],
            row["mode"],
            row["version"],
            row["max_steps"],
            row["response_timeout_seconds"],
            row["model"],
        ) != (
            agent_id,
            game,
            seed,
            campaign["mode"],
            campaign["version"],
            campaign["max_steps"],
            campaign["timeout_s"],
            campaign["model"],
        ):
            raise ValueError("A result differs from its ledger or declared suite")
        if (
            metadata.get("requested_model"),
            metadata.get("resolved_models"),
            metadata.get("prompt_version"),
            metadata.get("transport"),
            metadata.get("action_schema"),
            metadata.get("observation"),
            metadata.get("warmup"),
            metadata.get("retries"),
            metadata.get("tool_events"),
            metadata.get("images_header"),
        ) != (
            campaign["model"],
            [campaign["model"]],
            campaign["prompt_version"],
            TRANSPORT,
            ACTION_SCHEMA,
            "png-only",
            campaign["warmup"],
            0,
            0,
            True,
        ):
            raise ValueError("The model or native image settings differ")
        compare_tasks(
            {game: snapshot["exhibition"][0]["task_metadata"][game]},
            {game: row["game_metadata"]},
            rebuilds,
        )
        relative = str(path.relative_to(ROOT))
        head = json.loads((path / "events.jsonl").read_text().splitlines()[-1])["hash"]
        new.append(row)
        roots[relative] = new_roots[relative] = head
        checks[relative] = proof
        print(f"Replayed {number}/{len(pairs)} Jev episodes", flush=True)
    verify_source(campaign)
    board = summarize(new, campaign["games"], campaign["seeds"])
    for row in board:
        row["hardware_details"] = campaign["hardware_details"]
        for key in COMPARISON_KEYS:
            if key != "task_metadata" and row.get(key) != snapshot["exhibition"][0].get(key):
                raise ValueError("The game, seed, referee, or timing settings differ")
        if row["episodes"] != len(pairs) or any(
            r["agent"] == row["agent"] for r in snapshot["exhibition"]
        ):
            raise ValueError("The suite is incomplete or already published")
    snapshot["exhibition"] = sorted(
        [*snapshot["exhibition"], *board], key=lambda row: (-row["score"], row["agent"])
    )
    snapshot["model_status"].append(status)
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
            "note": "The previous 15-model snapshot and all its verified rows remain unchanged.",
        }
    )
    if current.read_bytes() != previous:
        raise ValueError("The current table changed during replay")
    (report / "previous-snapshot.json").write_bytes(previous)
    for name, value in {
        "episodes.json": [*retained, *new],
        "evidence-roots.json": roots,
        "new-evidence-roots.json": new_roots,
        "replay-validation.json": checks,
        "retained-evidence.json": retained_proof,
        "model-status.json": [status],
        "snapshot.json": snapshot,
    }.items():
        (report / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    current.write_bytes((report / "snapshot.json").read_bytes())
    print(json.dumps(board, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    export(parser.parse_args().report.resolve())
