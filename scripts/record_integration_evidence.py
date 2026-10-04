"""Record the fixed v0.3 control cohort, then independently replay every episode.

This calls no model and produces no aggregate model leaderboard. Run from a
checkout with the admitted new engines installed. Existing evidence is never replaced.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from generalgamebench.evidence import verify_episode
from generalgamebench.protocol import ProcessAgent
from generalgamebench.runner import run_episode

ROOT = Path(__file__).resolve().parents[1]
GAMES = [
    "unity-food-collector",
    "football-empty-goal",
    "supertuxkart-lighthouse",
    "luanti-chop-tree",
    "supertux-first-coin",
    "dcss-first-experience",
    "openttd-first-road",
    "mindustry-copper",
    "cdda-first-weapon",
    "warzone-first-derrick",
]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output, report = args.output.resolve(), args.report.resolve()
    if not output.is_relative_to(ROOT) or not report.is_relative_to(ROOT):
        parser.error("Use paths inside this checkout for portable relative evidence paths")
    if output.exists() or report.exists():
        parser.error("Use new output/report paths; previous evidence is immutable")
    report.mkdir(parents=True)
    sources = sorted((ROOT / "src/generalgamebench").glob("*.py")) + [
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        Path(__file__).resolve(),
    ]
    for runtime in (
        "unity",
        "docker-football",
        "docker-stk",
        "docker-craftium",
        "docker-supertux",
        "docker-crawl",
        "docker-openttd",
        "docker-mindustry",
        "docker-cdda",
        "docker-warzone",
    ):
        sources.extend(p for p in (ROOT / "environments" / runtime).iterdir() if p.is_file())
    source_hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
    }
    cohort = [
        {"agent": "random", "game": game, "seed": seed, "steps": 200}
        for game in GAMES
        for seed in (5000, 5001)
    ] + [{"agent": "idle", "game": "unity-food-collector", "seed": 71, "steps": 1200}]
    save(
        report / "campaign.json",
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "purpose": "integration-validation-only",
            "trust": "local-unattested",
            "mode": "exhibition",
            "model_calls": 0,
            "cohort": cohort,
            "source_hashes": source_hashes,
        },
    )
    episodes, roots, checks = [], {}, {}
    for spec in cohort:
        name, game, seed = spec["agent"], spec["game"], spec["seed"]
        directory = output / name / f"{game}-{seed}"
        agent = ProcessAgent([sys.executable, "-m", "generalgamebench.baselines", name])
        try:
            result = run_episode(agent, name, game, seed, directory, spec["steps"], "exhibition")
        finally:
            agent.close()
        if result["errors"]:
            raise ValueError(f"Integration control episode failed: {game} / {seed}")
        relative = str(directory.relative_to(ROOT))
        checks[relative] = verify_episode(directory, replay=True)
        roots[relative] = json.loads((directory / "events.jsonl").read_text().splitlines()[-1])[
            "hash"
        ]
        episodes.append(result)
        print(f"{game} / {name} / {seed}: {result['steps']} decisions, replay verified", flush=True)
    for source, digest in source_hashes.items():
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Source changed during the cohort: {source}")
    save(report / "episodes.json", episodes)
    save(report / "evidence-roots.json", roots)
    save(report / "replay-validation.json", checks)
    print(f"Recorded and replayed {len(episodes)} episodes; no model ranking was changed.")


if __name__ == "__main__":
    main()
