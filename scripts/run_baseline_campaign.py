"""Run declared baseline episodes serially; replay auditing is a separate phase.

An existing episode is never rerun or overwritten, including a failed episode.
A fresh policy process per episode resets its RNG, as in the public CLI.
"""

import argparse
import json
import sys
from pathlib import Path

from export_refresh import verify_source

from generalgamebench import __version__
from generalgamebench.evidence import read_ledger, verify_episode
from generalgamebench.protocol import ProcessAgent
from generalgamebench.runner import run_episode

ROOT = Path(__file__).resolve().parents[1]


def check_episode(path, campaign, agent, game, seed):
    verify_episode(path, replay=False)
    result = read_ledger(path / "events.jsonl")[-1]
    expected = {
        "agent": agent,
        "game": game,
        "seed": seed,
        "version": campaign["version"],
        "mode": campaign["mode"],
        "max_steps": campaign["max_steps"],
        "model": None,
        "provider_metadata": {},
    }
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Existing episode differs from declaration: {path}")
    if json.loads((path / "result.json").read_text()) != result:
        raise ValueError(f"Result sidecar differs from ledger: {path}")
    return result


def run(report):
    campaign = json.loads((report / "campaign.json").read_text())
    verify_source(campaign)
    if campaign["version"] != __version__:
        raise ValueError("Evaluator version differs from declaration")
    agents, games, seeds = (campaign[key] for key in ("agents", "games", "seeds"))
    if not all(values and len(values) == len(set(values)) for values in (agents, games, seeds)):
        raise ValueError("Campaign dimensions must be nonempty and unique")
    if set(agents) - {"idle", "random", "react", "tracker"}:
        raise ValueError("Only built-in reference policies are allowed")
    output = ROOT / campaign["run_root"]
    status = {
        "status": "running",
        "completed": 0,
        "expected": len(agents) * len(games) * len(seeds),
    }
    try:
        for name in agents:
            for game in games:
                for seed in seeds:
                    path = output / name / f"{game}-{seed}"
                    if path.exists():
                        result = check_episode(path, campaign, name, game, seed)
                    else:
                        agent = ProcessAgent(
                            [sys.executable, "-m", "generalgamebench.baselines", name]
                        )
                        try:
                            result = run_episode(
                                agent,
                                name,
                                game,
                                seed,
                                path,
                                campaign["max_steps"],
                                campaign["mode"],
                            )
                        finally:
                            agent.close()
                    status["completed"] += 1
                    status["latest"] = {
                        key: result[key]
                        for key in ("agent", "game", "seed", "score", "steps", "errors")
                    }
                    (report / "run-status.json").write_text(json.dumps(status, indent=2) + "\n")
                    print(json.dumps(status), flush=True)
        verify_source(campaign)
        status["status"] = "recorded-awaiting-replay"
    except Exception as exc:
        status.update(status="blocked", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        (report / "run-status.json").write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    run(parser.parse_args().report.resolve())
