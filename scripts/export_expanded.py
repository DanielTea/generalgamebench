"""Publish only declared, complete, replay-verified expanded cohorts."""

import argparse
import concurrent.futures
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.ranking import summarize

ROOT = Path(__file__).resolve().parents[1]


def agent_id(entry):
    return re.sub(r"[^a-zA-Z0-9_-]", "-", entry["provider"] + "-" + entry["model"])


def verified(path):
    verify_episode(path)
    result = read_ledger(path / "events.jsonl")[-1]
    final = json.loads((path / "events.jsonl").read_text().splitlines()[-1])
    return result, str(path.relative_to(ROOT)), final["hash"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", type=Path, default=ROOT / "runs/expanded-campaign.json")
    parser.add_argument("--inventory", type=Path, default=ROOT / "runs/discovery/models.json")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    campaign = json.loads(args.campaign.read_text())
    inventory = json.loads(args.inventory.read_text())
    games, seeds = campaign["games"], campaign["seeds"]
    for source, digest in campaign["source_hashes"].items():
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Scored source changed: {source}")
    local_paths, exhibition_paths, statuses = [], [], []
    for relative, model_names in campaign["assignments"].items():
        for model_name in model_names:
            entry = next(m for m in inventory["models"] if m["model"] == model_name)
            folder = ROOT / relative / agent_id(entry)
            status_file = folder / "status.json"
            if not status_file.exists():
                raise ValueError(f"Model has not been attempted: {model_name}")
            status = json.loads(status_file.read_text())
            statuses.append(status)
            paths = [folder / f"{game}-{seed}" for game in games for seed in seeds]
            completed = all((p / "result.json").exists() for p in paths)
            if not completed:
                if status["status"] not in {"blocked", "provider-unavailable"}:
                    raise ValueError(f"Campaign still running: {model_name}")
                # Show actual setup/access failure; never invent missing scores.
                continue
            if status["status"] != "complete":
                raise ValueError(f"Complete model suite needs final status: {model_name}")
            exhibition_paths.extend(paths)
    for agent in ("idle", "random", "react", "tracker"):
        local_paths.extend(
            ROOT / "runs/expanded-baselines-20261004" / agent / f"{game}-{seed}"
            for game in games
            for seed in (4000, 4001, 4002)
        )
        exhibition_paths.extend(
            ROOT / "runs/expanded-controls-20261004" / agent / f"{game}-{seed}"
            for game in games
            for seed in seeds
        )
    cohorts, roots = [], {}
    for paths in (local_paths, exhibition_paths):
        rows = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for index, (row, path, head) in enumerate(pool.map(verified, paths), 1):
                rows.append(row)
                roots[path] = head
                if index % 50 == 0:
                    print(f"Replayed {index}/{len(paths)} episodes", flush=True)
        cohorts.append(rows)
    local = summarize(cohorts[0], games, [4000, 4001, 4002])
    exhibition = summarize(cohorts[1], games, seeds)
    catalog = json.loads((ROOT / "docs/catalog.json").read_text())
    snapshot = {
        "schema_version": "generalgamebench-snapshot/1",
        "season": "0.2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local": local,
        "exhibition": exhibition,
        "official": [],
        "catalog": catalog,
        "coverage": {
            "task_count": len(games),
            "validated_cards": sum(c["status"] == "runnable" for c in catalog),
            "catalog_cards": len(catalog),
        },
        "model_status": statuses,
        "hardware_details": campaign["concurrency_note"],
        "suite_files": ["benchmarks/mac-baselines-v1.json", "benchmarks/mac-exhibition-v1.json"],
    }
    out = ROOT / "results/season-0.2"
    out.mkdir(parents=True, exist_ok=True)

    def save(path, value):
        path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

    save(out / "snapshot.json", snapshot)
    save(out / "episodes.json", cohorts[0] + cohorts[1])
    save(out / "evidence-roots.json", roots)
    save(out / "campaign.json", campaign)
    save(out / "model-status.json", statuses)
    # Publish IDs and revisions, never absolute weight-cache paths.
    save(
        out / "model-inventory.json",
        [{k: v for k, v in m.items() if k != "local_path"} for m in inventory["models"]],
    )
    save(ROOT / "site/dist/data.json", snapshot)
    print(
        json.dumps(
            {
                "episodes": len(roots),
                "decisions": sum(r["decisions"] for r in local + exhibition),
                "ranked_models": sum(bool(r["model"]) for r in exhibition),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
