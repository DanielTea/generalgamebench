"""Audit rebuilt containers against fixed published camera and score traces."""

import argparse
import hashlib
import json
from pathlib import Path

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.games import make_game

ROOT = Path(__file__).resolve().parents[1]


def audit(base_report, output):
    if output.exists():
        raise FileExistsError("Preserve the existing rebuild audit")
    roots = json.loads((base_report / "evidence-roots.json").read_text())
    candidates = {}
    for relative in roots:
        path = ROOT / relative
        rows = read_ledger(path / "events.jsonl")
        metadata = rows[0].get("game_metadata", {})
        if "container_image" not in metadata:
            continue
        game = rows[0]["game"]
        if game not in candidates or rows[-1]["steps"] > candidates[game][1][-1]["steps"]:
            candidates[game] = (path, rows)
    proofs = {}
    for game_id, (path, rows) in candidates.items():
        verify_episode(path, replay=False)
        manifest, result = rows[0], rows[-1]
        game = make_game(game_id, manifest["seed"], manifest["max_steps"])
        try:
            original = manifest["game_metadata"]
            current = game.metadata
            if {k: v for k, v in original.items() if k != "container_image"} != {
                k: v for k, v in current.items() if k != "container_image"
            }:
                raise ValueError(f"Rebuilt engine metadata differs: {game_id}")
            for event in rows[1:-1]:
                if hashlib.sha256(game.frame()).hexdigest() != event["frame_sha256"]:
                    raise ValueError(f"Rebuilt engine camera differs: {game_id}, {event['step']}")
                game.step(event["applied_action"])
            if game.result() != result["game_result"]:
                raise ValueError(f"Rebuilt native score differs: {game_id}")
            proofs[game_id] = {
                "original_metadata": original,
                "rebuilt_metadata": current,
                "episode": str(path.relative_to(ROOT)),
                "evidence_root": roots[str(path.relative_to(ROOT))],
                "exact_frames": result["steps"],
                "exact_native_score": True,
                "seed": manifest["seed"],
                "max_steps": manifest["max_steps"],
            }
            print(
                json.dumps(
                    {"game": game_id, "exact_frames": result["steps"], "exact_native_score": True}
                ),
                flush=True,
            )
        finally:
            game.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "scope": "One fixed published action trace per rebuilt scenario. Pinned source, task metadata, camera frames and native score match. Container image IDs differ. This audit does not establish equivalence for all possible trajectories.",
                "games": proofs,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.base_report.resolve(), args.output.resolve())
