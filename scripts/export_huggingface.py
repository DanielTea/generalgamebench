"""Prepare a static Space and tabular Dataset locally; never publish implicitly."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def export(site: Path, destination: Path):
    if destination.exists():
        raise FileExistsError("Use a new output directory to preserve previous exports")
    snapshot_bytes = (site / "data.json").read_bytes()
    snapshot = json.loads(snapshot_bytes)
    snapshot_hash = hashlib.sha256(snapshot_bytes).hexdigest()
    space, dataset = destination / "space", destination / "dataset"
    shutil.copytree(site, space)
    dataset.mkdir(parents=True)
    (space / "README.md").write_text(
        "---\ntitle: GeneralGameBench\nsdk: static\napp_file: index.html\n"
        "license: mit\npinned: false\n---\n\n"
        "# GeneralGameBench\n\n"
        "Other benchmarks test productivity/usefulness, we test intelligence.\n\n"
        "Static, read-only leaderboard. Evaluation workers run separately. "
        "No provider credentials or game execution belong in this Space.\n\n"
        "MIT applies to original code. Game media retains its separate rights; "
        "see media/NOTICE.txt and media/sources.json.\n"
    )
    configs = []
    for track in ("local", "exhibition", "official"):
        rows = []
        for ranking in snapshot.get(track, []):
            suite = {
                k: ranking.get(k)
                for k in (
                    "games",
                    "seed_ids",
                    "max_steps",
                    "mode",
                    "hardware",
                    "version",
                    "task_metadata",
                )
            }
            suite["hardware_details"] = snapshot.get("hardware_details")
            suite_id = hashlib.sha256(json.dumps(suite, sort_keys=True).encode()).hexdigest()
            for game, score in ranking.get("per_game", {}).items():
                metadata = ranking.get("provider_metadata", {})
                rows.append(
                    {
                        "schema_version": "generalgamebench-results/1",
                        "track": track,
                        "season": snapshot.get("season"),
                        "generated_at": snapshot.get("generated_at"),
                        "snapshot_sha256": snapshot_hash,
                        "agent_id": ranking["agent"],
                        "model_id": ranking.get("model"),
                        "model_revision": metadata.get("revision"),
                        "game_id": game,
                        "suite_id": suite_id,
                        "game_ids": ranking.get("games"),
                        "seed_ids": ranking.get("seed_ids"),
                        "evaluator_version": ranking.get("version"),
                        "task_metadata": ranking.get("task_metadata", {}).get(game),
                        "transport": metadata.get("transport"),
                        "prompt_version": metadata.get("prompt_version"),
                        "score_100": score,
                        "suite_score_100": ranking["score"],
                        "latency_eligible": ranking["latency_eligible"],
                        "suite_p95_ms": ranking["p95_ms"],
                        "suite_max_ms": ranking["max_ms"],
                        "seeds": ranking["seeds"],
                        "decision_horizon": ranking["max_steps"],
                        "trust": ranking["trust"],
                        "hardware": ranking["hardware"],
                        "hardware_details": snapshot.get("hardware_details"),
                        "suite_errors": ranking.get("errors", 0),
                        "suite_aborted_episodes": ranking.get("aborted_episodes"),
                    }
                )
        if rows:
            file = f"{track}.jsonl"
            (dataset / file).write_text(
                "".join(json.dumps(row, allow_nan=False) + "\n" for row in rows)
            )
            configs.append(
                f"- config_name: {track}\n  data_files:\n  - split: test\n    path: {file}\n"
            )
    (dataset / "README.md").write_text(
        "---\nlicense: mit\nconfigs:\n" + "".join(configs) + "---\n\n"
        "# GeneralGameBench result snapshot\n\n"
        "One row per agent and game. Timing columns describe the complete suite, "
        "not just that game. Compare only identical suite_id values; also inspect "
        "transport and task metadata. Null seed_ids in legacy results mean the "
        "exact seed set was not present in that snapshot. "
        "Local/exhibition rows are unattested; short exhibitions show integration, "
        "not statistically reliable intelligence rankings. No copyrighted game "
        "frames or model weights are included in this Dataset.\n"
    )
    manifest = {
        str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in destination.rglob("*")
        if p.is_file()
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"space": str(space), "dataset": str(dataset), "files": len(manifest)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=Path("site/dist"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.site, args.output)))
