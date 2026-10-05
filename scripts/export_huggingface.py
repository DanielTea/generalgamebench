"""Prepare a static Space and tabular Dataset locally; never publish implicitly."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE_ID = "danieltee/generalgamebench"
DATASET_ID = "danieltee/generalgamebench-results"
EXCLUDED_TRACKS = ("local", "local_previous", "exhibition_previous")


def card(name, **values):
    text = (ROOT / "huggingface" / name).read_text()
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def export(site: Path, destination: Path, space_id=SPACE_ID, dataset_id=DATASET_ID):
    if destination.exists():
        raise FileExistsError("Use a new output directory to preserve previous exports")
    source_bytes = (site / "data.json").read_bytes()
    snapshot = json.loads(source_bytes)
    for track in EXCLUDED_TRACKS:
        snapshot.pop(track, None)
        snapshot.get("track_metadata", {}).pop(track, None)
    snapshot_bytes = (json.dumps(snapshot, indent=2, allow_nan=False) + "\n").encode()
    snapshot_hash = hashlib.sha256(snapshot_bytes).hexdigest()
    space, dataset = destination / "space", destination / "dataset"
    shutil.copytree(site, space)
    (space / "data.json").write_bytes(snapshot_bytes)
    dataset.mkdir(parents=True)
    (space / "README.md").write_text(
        card("space-card.md", space_id=space_id, dataset_id=dataset_id)
    )
    for folder in (space, dataset):
        shutil.copyfile(ROOT / "LICENSE", folder / "LICENSE")
    (dataset / "snapshot.json").write_bytes(snapshot_bytes)
    (dataset / "viewer").mkdir()
    configs = []
    counts = {}
    for track in ("exhibition", "official"):
        rows = []
        track_metadata = snapshot.get("track_metadata", {}).get(track, {})
        for ranking in snapshot.get(track, []):
            hardware_details = ranking.get(
                "hardware_details",
                track_metadata.get("hardware_details", snapshot.get("hardware_details")),
            )
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
                    "response_timeout_seconds",
                )
            }
            suite["hardware_details"] = hardware_details
            suite_id = hashlib.sha256(json.dumps(suite, sort_keys=True).encode()).hexdigest()
            for game, score in ranking.get("per_game", {}).items():
                metadata = ranking.get("provider_metadata", {})
                rows.append(
                    {
                        "schema_version": "generalgamebench-results/1",
                        "track": track,
                        "season": track_metadata.get("season", snapshot.get("season")),
                        "generated_at": snapshot.get("generated_at"),
                        "snapshot_sha256": snapshot_hash,
                        "agent_id": ranking["agent"],
                        "mode": ranking.get("mode"),
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
                        "provider_metadata": metadata,
                        "score_100": score,
                        "suite_score_100": ranking["score"],
                        "latency_eligible": ranking["latency_eligible"],
                        "latency_policy_id": ranking.get("latency_policy", {}).get("id"),
                        "latency_limit_ms": ranking.get("latency_policy", {}).get("limit_ms"),
                        "suite_p95_ms": ranking["p95_ms"],
                        "suite_p50_ms": ranking.get("p50_ms"),
                        "suite_max_ms": ranking["max_ms"],
                        "suite_misses": ranking.get("misses"),
                        "suite_episodes": ranking.get("episodes"),
                        "suite_decisions": ranking.get("decisions"),
                        "suite_ci95": ranking.get("ci95"),
                        "seeds": ranking["seeds"],
                        "decision_horizon": ranking["max_steps"],
                        "trust": ranking["trust"],
                        "hardware": ranking["hardware"],
                        "hardware_details": hardware_details,
                        "suite_errors": ranking.get("errors", 0),
                        "suite_aborted_episodes": ranking.get("aborted_episodes"),
                    }
                )
        if rows:
            file = f"{track}.jsonl"
            (dataset / file).write_text(
                "".join(json.dumps(row, allow_nan=False) + "\n" for row in rows)
            )
            # Arbitrary engine/provider dictionaries can have incompatible Arrow
            # types. Keep lossless raw JSONL and use JSON strings in the viewer.
            viewer_rows = []
            for row in rows:
                view = dict(row)
                for key in ("task_metadata", "provider_metadata"):
                    value = view.pop(key)
                    view[key + "_json"] = json.dumps(value, sort_keys=True, allow_nan=False)
                viewer_rows.append(view)
            (dataset / "viewer" / file).write_text(
                "".join(json.dumps(row, allow_nan=False) + "\n" for row in viewer_rows)
            )
            counts[track] = len(rows)
            configs.append(
                f"- config_name: {track}\n  data_files:\n  - split: test\n    path: viewer/{file}\n"
            )
    (dataset / "README.md").write_text(
        card(
            "dataset-card.md",
            configs="".join(configs).rstrip(),
            space_id=space_id,
            dataset_id=dataset_id,
            snapshot_sha256=snapshot_hash,
            size_category="n<1K" if sum(counts.values()) < 1000 else "1K<n<10K",
            counts="\n".join(f"| {track} | {count} |" for track, count in counts.items()),
        )
    )
    publication = {
        "schema_version": "generalgamebench-hub/1",
        "space_id": space_id,
        "dataset_id": dataset_id,
        "snapshot_sha256": snapshot_hash,
        "source_snapshot_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "season": snapshot.get("season"),
        "rows": counts,
    }
    (destination / "publication.json").write_text(json.dumps(publication, indent=2) + "\n")
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
    parser.add_argument("--space-id", default=SPACE_ID)
    parser.add_argument("--dataset-id", default=DATASET_ID)
    args = parser.parse_args()
    print(json.dumps(export(args.site, args.output, args.space_id, args.dataset_id)))
